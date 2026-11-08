import json
import math
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.parquet as pq
from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.staffing.latent_demand import (
    LATENT_DEMAND_METHOD,
    ProductDay,
    weekly_load,
    zero_night_load,
)
from shiftopt.staffing.linear import required_staff
from shiftopt.time_grid import HOURS_PER_DAY

from src.demand.schemas import ConversionParams, SalesInspection, SalesMapping
from src.exceptions import InvalidInputError, NotFoundError

PARQUET_MAGIC = b"PAR1"
CSV_DELIMITERS = (",", ";", "\t")
DELIMITER_SAMPLE_BYTES = 4096
MAX_STORES_LISTED = 200
LABEL = "uploaded sales, not staffing demand; head counts follow the team's conversion assumptions"
FLAT_METHOD = (
    "sales used as observed (no stockout column); each hour is the mean over days of the weekly "
    "sum across products"
)
COLUMN_GUESSES: dict[str, tuple[str, ...]] = {
    "date_column": ("date", "dt", "ngay", "day", "timestamp", "thoi_diem"),
    "hour_column": ("hour", "gio"),
    "sales_column": ("sales", "hours_sale", "revenue", "doanh_so", "doanh_thu", "quantity", "qty"),
    "stockout_column": ("stockout", "hours_stock_status", "het_hang"),
    "product_column": ("product_id", "product", "sku", "san_pham"),
    "store_column": ("store_id", "store", "cua_hang"),
}

Record = tuple[int, object, date, int, float, int]


@dataclass(frozen=True)
class SalesDemand:
    load: tuple[float, ...]
    required_staff: tuple[int, ...]
    metadata: dict[str, str]


def inspect_sales(data: bytes) -> SalesInspection:
    """Read the columns of an uploaded file and guess the mapping from their names. Also lists the
    store values when a store column is guessed, so the form can offer them."""
    table = _read_table(data)
    columns = list(table.column_names)
    guess = {field: _guess(columns, names) for field, names in COLUMN_GUESSES.items()}
    stores: list[str] = []
    if guess["store_column"] is not None:
        values = pc.unique(table.column(guess["store_column"])).to_pylist()
        stores = sorted({str(value) for value in values if value is not None})[:MAX_STORES_LISTED]
    return SalesInspection(
        format="parquet" if data[:4] == PARQUET_MAGIC else "csv",
        rows=table.num_rows,
        columns=columns,
        guess=guess,
        stores=stores,
    )


def derive_demand(
    data: bytes,
    mapping: SalesMapping,
    conversion: ConversionParams,
    rules: LaborRules,
    sha256: str,
) -> SalesDemand:
    """Turn an uploaded sales file into the weekly hourly load and the head count per hour.
    Stockout hours are replaced by the mean of the same product, weekday and hour over days in
    stock. Night hours use the night floor unless mapping.night_from_sales is set. Raise
    InvalidInputError for a file that cannot be read as the mapping says, and NotFoundError when
    the requested store is absent."""
    table = _select_rows(_read_table(data), mapping)
    product_days, product_count = _product_days(_records(table, mapping))
    try:
        result = weekly_load(product_days)
    except ValueError as error:
        raise InvalidInputError(str(error)) from error
    staff, floored = staff_from_load(result.load, conversion, rules, mapping.night_from_sales)
    days = [product_day.day for product_day in product_days]
    metadata = {
        "label": LABEL,
        "method": LATENT_DEMAND_METHOD if mapping.stockout_column else FLAT_METHOD,
        "sha256": sha256,
        "store": mapping.store or "",
        "rows": str(table.num_rows),
        "products": str(product_count),
        "first_day": min(days).isoformat(),
        "last_day": max(days).isoformat(),
        "imputed_cells": str(result.imputed_cells),
        "unimputed_cells": str(result.unimputed_cells),
        "night_from_sales": str(mapping.night_from_sales),
        "night_hours_floored": str(floored),
        "night_start": str(rules.night_start),
        "night_end": str(rules.night_end),
        "mapping": json.dumps(mapping.model_dump(), sort_keys=True),
    }
    return SalesDemand(tuple(result.load), staff, metadata)


def staff_from_load(
    load: Iterable[float], conversion: ConversionParams, rules: LaborRules, night_from_sales: bool
) -> tuple[tuple[int, ...], int]:
    """Head count per hour and the number of night hours whose sales were set to zero."""
    if night_from_sales:
        used, floored = tuple(load), 0
    else:
        used, floored = zero_night_load(tuple(load), rules)
    staff = required_staff(
        used,
        alpha=conversion.alpha,
        productivity=conversion.productivity,
        min_staff=conversion.min_staff,
        night_min_staff=conversion.night_min_staff,
        rules=rules,
    )
    return tuple(staff), floored


def _read_table(data: bytes) -> pa.Table:
    try:
        if data[:4] == PARQUET_MAGIC:
            return pq.read_table(pa.BufferReader(data))
        delimiter = _delimiter(data)
        return pacsv.read_csv(
            pa.BufferReader(data), parse_options=pacsv.ParseOptions(delimiter=delimiter)
        )
    except (pa.ArrowException, ValueError) as error:
        raise InvalidInputError(f"file is not a readable parquet or CSV file: {error}") from error


def _delimiter(data: bytes) -> str:
    sample = data[:DELIMITER_SAMPLE_BYTES].decode("utf-8", errors="replace")
    first_line = sample.splitlines()[0] if sample else ""
    return max(CSV_DELIMITERS, key=first_line.count)


def _guess(columns: list[str], names: tuple[str, ...]) -> str | None:
    lowered = {column.lower(): column for column in columns}
    for name in names:
        if name in lowered:
            return lowered[name]
    return None


def _needed_columns(mapping: SalesMapping) -> list[str]:
    names = (
        mapping.date_column,
        mapping.sales_column,
        mapping.hour_column,
        mapping.stockout_column,
        mapping.product_column,
        mapping.store_column,
    )
    return list(dict.fromkeys(name for name in names if name is not None))


def _select_rows(table: pa.Table, mapping: SalesMapping) -> pa.Table:
    needed = _needed_columns(mapping)
    missing = [name for name in needed if name not in table.column_names]
    if missing:
        raise InvalidInputError(
            f"columns not in file: {', '.join(missing)}; file has {', '.join(table.column_names)}"
        )
    table = table.select(needed)
    if mapping.store_column is None:
        if mapping.store is not None:
            raise InvalidInputError("store is set but no store column is chosen")
        return table
    column = table.column(mapping.store_column)
    if mapping.store is None:
        stores = [value for value in pc.unique(column).to_pylist() if value is not None]
        if len(stores) > 1:
            raise InvalidInputError(f"file has {len(stores)} stores; choose one store")
        return table
    mask = pc.equal(pc.cast(column, pa.string()), pa.scalar(mapping.store))
    filtered = table.filter(mask)
    if filtered.num_rows == 0:
        raise NotFoundError(f"store {mapping.store} not found in the sales file")
    return filtered


def _records(table: pa.Table, mapping: SalesMapping) -> Iterator[Record]:
    row_count = table.num_rows
    dates = table.column(mapping.date_column).to_pylist()
    sales = table.column(mapping.sales_column).to_pylist()
    wide = pa.types.is_list(table.schema.field(mapping.sales_column).type)
    products = _column_or(table, mapping.product_column, row_count, 0)
    flags = _column_or(table, mapping.stockout_column, row_count, 0)
    hours = _column_or(table, mapping.hour_column, row_count, None)
    for index in range(row_count):
        row = index + 1
        day, moment_hour = _day(dates[index], row)
        if wide:
            hourly_sales = _hourly_list(sales[index], row, "sales")
            hourly_flags = (
                _hourly_list(flags[index], row, "stockout")
                if mapping.stockout_column
                else [0] * HOURS_PER_DAY
            )
            for hour in range(HOURS_PER_DAY):
                yield (
                    row,
                    products[index],
                    day,
                    hour,
                    _sale(hourly_sales[hour], row),
                    _flag(hourly_flags[hour], row),
                )
            continue
        if mapping.hour_column is not None:
            hour = _hour(hours[index], row)
        elif moment_hour is not None:
            hour = moment_hour
        else:
            raise InvalidInputError(
                f"row {row}: date has no time; choose an hour column for the hour of each sale"
            )
        yield (row, products[index], day, hour, _sale(sales[index], row), _flag(flags[index], row))


def _column_or(table: pa.Table, name: str | None, row_count: int, default: Any) -> list[Any]:
    if name is None:
        return [default] * row_count
    values: list[Any] = table.column(name).to_pylist()
    return values


def _day(value: object, row: int) -> tuple[date, int | None]:
    if isinstance(value, datetime):
        return value.date(), value.hour
    if isinstance(value, date):
        return value, None
    if isinstance(value, str):
        text = value.strip()
        try:
            if len(text) <= 10:
                return date.fromisoformat(text), None
            moment = datetime.fromisoformat(text)
        except ValueError as error:
            raise InvalidInputError(
                f"row {row}: date '{value}' is not YYYY-MM-DD or YYYY-MM-DD HH:MM[:SS]"
            ) from error
        return moment.date(), moment.hour
    raise InvalidInputError(f"row {row}: date is empty or not a date")


def _hour(value: Any, row: int) -> int:
    if value is None or isinstance(value, bool):
        raise InvalidInputError(f"row {row}: hour is empty")
    try:
        hour = int(value)
    except (TypeError, ValueError) as error:
        raise InvalidInputError(f"row {row}: hour '{value}' is not a whole number") from error
    if not 0 <= hour < HOURS_PER_DAY:
        raise InvalidInputError(f"row {row}: hour {hour} is outside 0..{HOURS_PER_DAY - 1}")
    return hour


def _hourly_list(value: Any, row: int, name: str) -> list[Any]:
    if not isinstance(value, list) or len(value) != HOURS_PER_DAY:
        raise InvalidInputError(f"row {row}: {name} must list {HOURS_PER_DAY} hourly values")
    return list(value)


def _sale(value: Any, row: int) -> float:
    if value is None:
        raise InvalidInputError(f"row {row}: sales is empty")
    try:
        sale = float(value)
    except (TypeError, ValueError) as error:
        raise InvalidInputError(f"row {row}: sales '{value}' is not a number") from error
    if not math.isfinite(sale) or sale < 0:
        raise InvalidInputError(f"row {row}: sales must be finite and non-negative")
    return sale


def _flag(value: Any, row: int) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if value in (0, 1):
        return int(value)
    raise InvalidInputError(f"row {row}: stockout must be 0 or 1, got '{value}'")


def _product_days(records: Iterable[Record]) -> tuple[list[ProductDay], int]:
    sales: dict[tuple[object, date], list[float]] = defaultdict(lambda: [0.0] * HOURS_PER_DAY)
    flags: dict[tuple[object, date], list[int]] = defaultdict(lambda: [0] * HOURS_PER_DAY)
    for _, product, day, hour, sale, flag in records:
        key = (product, day)
        sales[key][hour] += sale
        flags[key][hour] = max(flags[key][hour], flag)
    keys = sorted(sales, key=repr)
    products = sorted({key[0] for key in keys}, key=repr)
    ids = {product: index for index, product in enumerate(products)}
    product_days = [
        ProductDay(
            product_id=ids[product],
            day=day,
            hours_sale=tuple(sales[(product, day)]),
            hours_stock_status=tuple(flags[(product, day)]),
        )
        for product, day in keys
    ]
    return product_days, len(ids)
