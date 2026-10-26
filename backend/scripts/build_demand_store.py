import argparse
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq
from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.time_grid import HOURS_PER_DAY, HOURS_PER_WEEK

from src.demand.dataset_loader import build_processed_store, dataset_required_staff
from src.demand.schemas import ConversionParams

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "freshretailnet50k" / "data"
PROCESSED_DIR = ROOT / "data" / "processed"


def eval_date_range(store_id: int) -> tuple[str, str]:
    table = pq.read_table(
        RAW_DIR / "eval.parquet", columns=["dt"], filters=[("store_id", "=", store_id)]
    )
    if table.num_rows == 0:
        return ("none", "none")
    return (
        str(pc.min(table.column("dt")).as_py()),
        str(pc.max(table.column("dt")).as_py()),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the processed weekly demand of one store.")
    parser.add_argument("--store-id", type=int, required=True)
    arguments = parser.parse_args()
    store_id: int = arguments.store_id
    path = build_processed_store(RAW_DIR, PROCESSED_DIR, store_id)
    demand = dataset_required_staff(PROCESSED_DIR, store_id, ConversionParams(), LaborRules())
    eval_first, eval_last = eval_date_range(store_id)
    print(f"file    {path}")
    print(f"eval    {eval_first} .. {eval_last}")
    for key, value in demand.metadata.items():
        print(f"{key:<20} {value}")
    print("required_staff (rows: weekday Mon..Sun, columns: hour 0..23)")
    for weekday in range(HOURS_PER_WEEK // HOURS_PER_DAY):
        start = weekday * HOURS_PER_DAY
        print(
            " ".join(
                f"{count:>2}" for count in demand.required_staff[start : start + HOURS_PER_DAY]
            )
        )


if __name__ == "__main__":
    main()
