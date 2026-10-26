from datetime import date, timedelta
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.staffing.latent_demand import LATENT_DEMAND_METHOD

from src.demand.dataset_loader import (
    DATASET_LABEL,
    build_processed_store,
    dataset_required_staff,
    load_hourly_load,
)
from src.demand.schemas import ConversionParams
from src.exceptions import NotFoundError

START = date(2024, 6, 3)
MONDAY_TEN = 10
SCHEMA = pa.schema(
    [
        ("store_id", pa.int64()),
        ("product_id", pa.int64()),
        ("dt", pa.string()),
        ("hours_sale", pa.list_(pa.float64())),
        ("hours_stock_status", pa.list_(pa.int64())),
    ]
)


def _write_training_split(path: Path) -> None:
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
    pq.write_table(pa.Table.from_pylist(rows, schema=SCHEMA), path)


@pytest.fixture
def directories(tmp_path: Path) -> tuple[Path, Path]:
    raw = tmp_path / "raw"
    raw.mkdir()
    _write_training_split(raw / "train.parquet")
    return raw, tmp_path / "processed"


def test_build_and_load_round_trip(directories: tuple[Path, Path]) -> None:
    raw, processed = directories
    path = build_processed_store(raw, processed, 1)
    assert path.name == "demand_store_1.parquet"
    store = load_hourly_load(processed, 1)
    assert len(store.load) == 168
    assert store.load[MONDAY_TEN] == 6.0
    assert store.metadata["label"] == DATASET_LABEL
    assert store.metadata["method"] == LATENT_DEMAND_METHOD
    assert store.metadata["products"] == "2"
    assert store.metadata["imputed_cells"] == "1"
    assert store.metadata["unimputed_cells"] == "0"
    assert store.metadata["first_day"] == "2024-06-03"
    assert store.metadata["last_day"] == "2024-06-16"


def test_unknown_store_raises_not_found(directories: tuple[Path, Path]) -> None:
    raw, processed = directories
    with pytest.raises(NotFoundError, match="store 99"):
        build_processed_store(raw, processed, 99)


def test_missing_processed_file_raises_not_found(tmp_path: Path) -> None:
    with pytest.raises(NotFoundError, match="store 1"):
        load_hourly_load(tmp_path, 1)


def test_required_staff_uses_night_floor_and_records_assumptions(
    directories: tuple[Path, Path],
) -> None:
    raw, processed = directories
    build_processed_store(raw, processed, 1)
    conversion = ConversionParams(alpha=1.0, productivity=1.0, min_staff=1, night_min_staff=2)
    demand = dataset_required_staff(processed, 1, conversion, LaborRules())
    assert demand.required_staff[0] == 2
    assert demand.required_staff[MONDAY_TEN] == 6
    assert demand.metadata["alpha"] == "1.0"
    assert demand.metadata["night_min_staff"] == "2"
    assert demand.metadata["night_start"] == "22"
    assert demand.metadata["night_hours_floored"] == "56"


def test_night_window_comes_from_the_rules_given_not_the_build(
    directories: tuple[Path, Path],
) -> None:
    raw, processed = directories
    build_processed_store(raw, processed, 1)
    conversion = ConversionParams(alpha=1.0, productivity=1.0, min_staff=1, night_min_staff=2)
    shifted = LaborRules(night_start=23, night_end=7)
    demand = dataset_required_staff(processed, 1, conversion, shifted)
    assert demand.required_staff[22] == 6
    assert demand.required_staff[6] == 2
    assert demand.metadata["night_start"] == "23"
