from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.staffing.latent_demand import ProductDay, weekly_load, zero_night_load
from shiftopt.staffing.linear import required_staff
from shiftopt.time_grid import HOURS_PER_DAY, HOURS_PER_WEEK

from src.demand.schemas import ConversionParams
from src.exceptions import NotFoundError

HF_REVISION = "c374e85975c82816c495acfa904cc55ab14a47d3"
TRAIN_FILE = "train.parquet"
TRAIN_COLUMNS = ["store_id", "product_id", "dt", "hours_sale", "hours_stock_status"]
PROCESSED_NAME = "demand_store_{store_id}.parquet"
DATASET_LABEL = (
    "normalized sales of an e-commerce front warehouse (FreshRetailNet-50K, CC BY 4.0, "
    "arXiv:2505.16319, about 863-865 SKU); not staffing demand and not a 24/7 physical store"
)


@dataclass(frozen=True)
class StoreLoad:
    load: tuple[float, ...]
    metadata: dict[str, str]


@dataclass(frozen=True)
class StoreDemand:
    required_staff: tuple[int, ...]
    metadata: dict[str, str]


def build_processed_store(raw_dir: Path, processed_dir: Path, store_id: int) -> Path:
    """Aggregate the training split of one store into a 168-row weekly load file. Reads only
    the rows of store_id, builds the latent-demand week (stockout cells replaced) and writes
    demand_store_<id>.parquet with the method and the coverage of the input as schema metadata.
    Night hours are not changed here: the night rule belongs to the caller's LaborRules and is
    applied in dataset_required_staff. Raise NotFoundError when the store is absent."""
    table = pq.read_table(
        raw_dir / TRAIN_FILE,
        columns=TRAIN_COLUMNS,
        filters=[("store_id", "=", store_id)],
    )
    if table.num_rows == 0:
        raise NotFoundError(f"store {store_id} not found in the training split")
    rows = _product_days(table)
    result = weekly_load(rows)
    days = sorted({row.day for row in rows})
    grid = pa.table(
        {
            "weekday": [index // HOURS_PER_DAY for index in range(HOURS_PER_WEEK)],
            "hour": [index % HOURS_PER_DAY for index in range(HOURS_PER_WEEK)],
            "load": list(result.load),
        }
    )
    metadata = {
        "label": DATASET_LABEL,
        "method": result.method,
        "source": f"FreshRetailNet-50K train split, revision {HF_REVISION}",
        "store_id": str(store_id),
        "products": str(len({row.product_id for row in rows})),
        "first_day": days[0].isoformat(),
        "last_day": days[-1].isoformat(),
        "imputed_cells": str(result.imputed_cells),
        "unimputed_cells": str(result.unimputed_cells),
    }
    processed_dir.mkdir(parents=True, exist_ok=True)
    path = processed_dir / PROCESSED_NAME.format(store_id=store_id)
    pq.write_table(grid.replace_schema_metadata(metadata), path)
    return path


def load_hourly_load(dataset_dir: Path, store_id: int) -> StoreLoad:
    """Read the processed 168-hour load of one store with its metadata. Raise NotFoundError when
    build_processed_store has not run for that store."""
    path = dataset_dir / PROCESSED_NAME.format(store_id=store_id)
    if not path.exists():
        raise NotFoundError(f"no processed demand for store {store_id}; build it first")
    table = pq.read_table(path)
    load = tuple(float(value) for value in table.column("load").to_pylist())
    if len(load) != HOURS_PER_WEEK:
        raise ValueError(f"processed demand for store {store_id} must have {HOURS_PER_WEEK} hours")
    metadata = {
        key.decode(): value.decode() for key, value in (table.schema.metadata or {}).items()
    }
    return StoreLoad(load, metadata)


def dataset_required_staff(
    dataset_dir: Path, store_id: int, conversion: ConversionParams, rules: LaborRules
) -> StoreDemand:
    """Head count per hour of a processed store under the given conversion assumptions and night
    window. Night hours are zeroed here, so the night head count is the night floor of these
    rules. alpha, productivity, both staff floors and the night window are copied into the
    metadata so the result states the assumptions it was built with."""
    store = load_hourly_load(dataset_dir, store_id)
    load, floored = zero_night_load(store.load, rules)
    staff = required_staff(
        load,
        alpha=conversion.alpha,
        productivity=conversion.productivity,
        min_staff=conversion.min_staff,
        night_min_staff=conversion.night_min_staff,
        rules=rules,
    )
    metadata = {
        **store.metadata,
        "night_start": str(rules.night_start),
        "night_end": str(rules.night_end),
        "night_hours_floored": str(floored),
        "alpha": str(conversion.alpha),
        "productivity": str(conversion.productivity),
        "min_staff": str(conversion.min_staff),
        "night_min_staff": str(conversion.night_min_staff),
    }
    return StoreDemand(staff, metadata)


def _product_days(table: pa.Table) -> list[ProductDay]:
    return [
        ProductDay(
            product_id=int(row["product_id"]),
            day=date.fromisoformat(row["dt"]),
            hours_sale=tuple(float(sale) for sale in row["hours_sale"]),
            hours_stock_status=tuple(int(flag) for flag in row["hours_stock_status"]),
        )
        for row in table.to_pylist()
    ]
