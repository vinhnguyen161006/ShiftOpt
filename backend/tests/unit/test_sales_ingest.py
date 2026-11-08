from datetime import date, timedelta
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.staffing.latent_demand import LATENT_DEMAND_METHOD

from src.demand.sales_ingest import SalesDemand, derive_demand, inspect_sales
from src.demand.schemas import ConversionParams, SalesMapping
from src.exceptions import InvalidInputError, NotFoundError

START = date(2024, 6, 3)
MONDAY_TEN = 10
CONVERSION = ConversionParams(alpha=1.0, productivity=1.0, min_staff=1, night_min_staff=1)
WIDE_SCHEMA = pa.schema(
    [
        ("store_id", pa.int64()),
        ("product_id", pa.int64()),
        ("dt", pa.string()),
        ("hours_sale", pa.list_(pa.float64())),
        ("hours_stock_status", pa.list_(pa.int64())),
    ]
)
WIDE_MAPPING = SalesMapping(
    date_column="dt",
    sales_column="hours_sale",
    stockout_column="hours_stock_status",
    product_column="product_id",
    store_column="store_id",
    store="1",
)


def _wide_parquet(tmp_path: Path) -> bytes:
    rows: list[dict[str, object]] = []
    for day in range(14):
        for store_id, product_id, sale in [(1, 10, 4.0), (1, 11, 2.0), (2, 10, 50.0)]:
            sales = [sale] * 24
            flags = [0] * 24
            if store_id == 1 and product_id == 10 and day == 0:
                sales[MONDAY_TEN] = 100.0
                flags[MONDAY_TEN] = 1
            rows.append(
                {
                    "store_id": store_id,
                    "product_id": product_id,
                    "dt": (START + timedelta(days=day)).isoformat(),
                    "hours_sale": sales,
                    "hours_stock_status": flags,
                }
            )
    path = tmp_path / "train.parquet"
    pq.write_table(pa.Table.from_pylist(rows, schema=WIDE_SCHEMA), path)
    return path.read_bytes()


def _week(prefix: str = "", value: float = 1.0, days: int = 7) -> list[str]:
    return [
        f"{prefix}{(START + timedelta(days=day)).isoformat()} {hour:02d}:00:00,{value}"
        for day in range(days)
        for hour in range(24)
    ]


def _csv(header: str, rows: list[str], delimiter: str = ",") -> bytes:
    return "\n".join(
        [header.replace(",", delimiter), *[row.replace(",", delimiter) for row in rows]]
    ).encode()


def _derive(
    data: bytes,
    mapping: SalesMapping,
    conversion: ConversionParams = CONVERSION,
) -> SalesDemand:
    return derive_demand(data, mapping, conversion, LaborRules(), sha256="test")


TIME_MAPPING = SalesMapping(date_column="thoi_diem", sales_column="doanh_thu")


def test_wide_parquet_replaces_stockout_hours_and_sums_products(tmp_path: Path) -> None:
    demand = _derive(_wide_parquet(tmp_path), WIDE_MAPPING)
    assert demand.load[MONDAY_TEN] == 6.0
    assert len(demand.load) == 168
    assert demand.metadata["method"] == LATENT_DEMAND_METHOD
    assert demand.metadata["imputed_cells"] == "1"
    assert demand.metadata["unimputed_cells"] == "0"
    assert demand.metadata["products"] == "2"
    assert demand.metadata["first_day"] == "2024-06-03"
    assert demand.metadata["last_day"] == "2024-06-16"
    assert demand.metadata["store"] == "1"


def test_timestamp_rows_give_hours_without_an_hour_column() -> None:
    demand = _derive(_csv("thoi_diem,doanh_thu", _week(value=1.0)), TIME_MAPPING)
    assert demand.load == (1.0,) * 168
    assert demand.metadata["night_hours_floored"] == "56"
    assert demand.required_staff[12] == 1
    assert demand.required_staff[0] == 1


def test_semicolon_csv_with_custom_names_and_hour_column() -> None:
    rows = [
        f"{(START + timedelta(days=day)).isoformat()};{hour};2.5"
        for day in range(7)
        for hour in range(24)
    ]
    mapping = SalesMapping(date_column="ngay", hour_column="gio", sales_column="doanh_thu")
    demand = _derive(_csv("ngay;gio;doanh_thu", rows, delimiter=";"), mapping)
    assert demand.load[12] == 2.5
    assert demand.metadata["method"].startswith("sales used as observed")


def test_duplicate_rows_for_the_same_hour_are_summed() -> None:
    rows = [
        f"{(START + timedelta(days=day)).isoformat()} 12:00:00,{value}"
        for day in range(7)
        for value in (2.0, 3.0)
    ]
    demand = _derive(_csv("thoi_diem,doanh_thu", rows), TIME_MAPPING)
    assert demand.load[12] == 5.0
    assert demand.load[36] == 5.0


def test_store_filter_keeps_only_the_chosen_store() -> None:
    rows = _week("A,", 1.0) + _week("B,", 2.0)
    mapping = SalesMapping(
        date_column="thoi_diem",
        sales_column="doanh_thu",
        store_column="cua_hang",
        store="B",
    )
    demand = _derive(_csv("cua_hang,thoi_diem,doanh_thu", rows), mapping)
    assert demand.load[12] == 2.0
    assert demand.metadata["rows"] == "168"


def test_several_stores_without_a_choice_are_rejected() -> None:
    rows = _week("A,", 1.0) + _week("B,", 2.0)
    mapping = SalesMapping(
        date_column="thoi_diem", sales_column="doanh_thu", store_column="cua_hang"
    )
    with pytest.raises(InvalidInputError, match="2 stores"):
        _derive(_csv("cua_hang,thoi_diem,doanh_thu", rows), mapping)


def test_unknown_store_is_not_found() -> None:
    rows = _week("A,", 1.0)
    mapping = SalesMapping(
        date_column="thoi_diem", sales_column="doanh_thu", store_column="cua_hang", store="Z"
    )
    with pytest.raises(NotFoundError, match="store Z"):
        _derive(_csv("cua_hang,thoi_diem,doanh_thu", rows), mapping)


def test_hour_outside_the_day_is_rejected() -> None:
    rows = ["2024-06-03,25,1.0"]
    mapping = SalesMapping(date_column="ngay", hour_column="gio", sales_column="doanh_thu")
    with pytest.raises(InvalidInputError, match="row 1: hour 25"):
        _derive(_csv("ngay,gio,doanh_thu", rows), mapping)


def test_negative_sales_are_rejected() -> None:
    rows = ["2024-06-03 10:00:00,-1.0"]
    with pytest.raises(InvalidInputError, match="non-negative"):
        _derive(_csv("thoi_diem,doanh_thu", rows), TIME_MAPPING)


def test_date_without_time_needs_an_hour_column() -> None:
    rows = ["2024-06-03,1.0"]
    mapping = SalesMapping(date_column="ngay", sales_column="doanh_thu")
    with pytest.raises(InvalidInputError, match="choose an hour column"):
        _derive(_csv("ngay,doanh_thu", rows), mapping)


def test_missing_weekday_is_rejected() -> None:
    rows = _week(days=1)
    with pytest.raises(InvalidInputError, match="missing weekdays"):
        _derive(_csv("thoi_diem,doanh_thu", rows), TIME_MAPPING)


def test_unreadable_file_is_rejected() -> None:
    with pytest.raises(InvalidInputError):
        _derive(b"", TIME_MAPPING)


def test_missing_column_is_named_in_the_error() -> None:
    mapping = SalesMapping(date_column="ngay", sales_column="doanh_thu")
    with pytest.raises(InvalidInputError, match="columns not in file: ngay"):
        _derive(_csv("thoi_diem,doanh_thu", _week()), mapping)


def test_night_from_sales_keeps_night_sales_and_uses_them() -> None:
    rows = _week(value=1.0)
    data = _csv("thoi_diem,doanh_thu", rows)
    efficient = ConversionParams(alpha=1.0, productivity=0.5, min_staff=1, night_min_staff=1)
    zeroed = _derive(data, TIME_MAPPING, efficient)
    kept = _derive(data, TIME_MAPPING.model_copy(update={"night_from_sales": True}), efficient)
    assert zeroed.required_staff[0] == 1
    assert kept.required_staff[0] == 2
    assert kept.metadata["night_from_sales"] == "True"
    assert kept.metadata["night_hours_floored"] == "0"


def test_inspect_guesses_columns_and_lists_stores(tmp_path: Path) -> None:
    rows = _week("A,", 1.0) + _week("B,", 2.0)
    data = _csv("cua_hang,thoi_diem,doanh_thu,het_hang", [row + ",0" for row in rows])
    inspection = inspect_sales(data)
    assert inspection.format == "csv"
    assert inspection.rows == 336
    assert inspection.guess["date_column"] == "thoi_diem"
    assert inspection.guess["sales_column"] == "doanh_thu"
    assert inspection.guess["store_column"] == "cua_hang"
    assert inspection.guess["stockout_column"] == "het_hang"
    assert inspection.guess["hour_column"] is None
    assert inspection.stores == ["A", "B"]


def test_inspect_recognises_wide_parquet(tmp_path: Path) -> None:
    inspection = inspect_sales(_wide_parquet(tmp_path))
    assert inspection.format == "parquet"
    assert inspection.guess["date_column"] == "dt"
    assert inspection.guess["sales_column"] == "hours_sale"
    assert inspection.guess["product_column"] == "product_id"
    assert inspection.stores == ["1", "2"]
