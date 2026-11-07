from collections.abc import AsyncIterator
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
    ingest_store_sales,
    load_hourly_load,
)
from src.demand.schemas import ConversionParams
from src.demand.service import read_upload
from src.exceptions import InvalidInputError, NotFoundError, UploadTooLargeError

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


def test_ingest_from_memory_matches_build_from_disk(
    directories: tuple[Path, Path], tmp_path: Path
) -> None:
    raw, processed = directories
    build_processed_store(raw, processed, 1)
    uploaded = tmp_path / "uploaded"
    buffer = pa.BufferReader(pa.py_buffer((raw / "train.parquet").read_bytes()))
    ingest_store_sales(buffer, uploaded, 1, "uploaded sales file")
    expected = load_hourly_load(processed, 1)
    actual = load_hourly_load(uploaded, 1)
    assert actual.load == expected.load
    assert actual.metadata["source"] == "uploaded sales file"


def test_ingest_rejects_a_file_that_is_not_parquet(tmp_path: Path) -> None:
    with pytest.raises(InvalidInputError, match="parquet"):
        ingest_store_sales(pa.BufferReader(b"date,hour,sales"), tmp_path, 1, "upload")


def test_ingest_rejects_parquet_without_the_sales_columns(tmp_path: Path) -> None:
    source = tmp_path / "other.parquet"
    pq.write_table(pa.table({"store_id": [1], "sales": [2.0]}), source)
    with pytest.raises(InvalidInputError, match="hours_sale"):
        ingest_store_sales(source, tmp_path, 1, "upload")


def test_ingest_rejects_a_store_missing_weekdays(tmp_path: Path) -> None:
    source = tmp_path / "short.parquet"
    row = {
        "store_id": 1,
        "product_id": 10,
        "dt": START.isoformat(),
        "hours_sale": [1.0] * 24,
        "hours_stock_status": [0] * 24,
    }
    pq.write_table(pa.Table.from_pylist([row], schema=SCHEMA), source)
    with pytest.raises(InvalidInputError, match="weekday"):
        ingest_store_sales(source, tmp_path, 1, "upload")


async def _chunks(*parts: bytes) -> AsyncIterator[bytes]:
    for part in parts:
        yield part


async def test_read_upload_joins_chunks() -> None:
    assert await read_upload(_chunks(b"ab", b"cd"), limit=4) == bytearray(b"abcd")


async def test_read_upload_refuses_bodies_over_the_limit() -> None:
    with pytest.raises(UploadTooLargeError):
        await read_upload(_chunks(b"ab", b"cde"), limit=4)


async def test_read_upload_refuses_an_empty_body() -> None:
    with pytest.raises(InvalidInputError, match="empty"):
        await read_upload(_chunks(), limit=4)
