import argparse
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from shiftopt.constraints.labor_law_vn import LaborRules

from src.demand.sales_ingest import derive_demand
from src.demand.schemas import ConversionParams, SalesMapping

ROOT = Path(__file__).resolve().parents[2]
TRAIN_FILE = ROOT / "data" / "demo" / "train.parquet"
MAPPING = {
    "date_column": "dt",
    "sales_column": "hours_sale",
    "stockout_column": "hours_stock_status",
    "product_column": "product_id",
    "store_column": "store_id",
}
QUANTILES = (0.1, 0.25, 0.5, 0.75, 0.9)
REFERENCE_STORE = 18
PEAK_RANGE = (4, 15)
MAX_UNIMPUTED_SHARE = 0.05
HEADER = "store,total_sales,products,peak_staff,person_hours,unimputed_share,selected"


def store_totals(path: Path) -> list[tuple[int, float, int]]:
    """Total hourly sales and distinct product count per store, sorted by total sales. Reads only
    the three columns needed, and flattens the hour lists with pyarrow instead of Python loops."""
    table = pq.read_table(path, columns=["store_id", "product_id", "hours_sale"])
    parents = pc.list_parent_indices(table["hours_sale"])
    flat = pa.table(
        {
            "store": pc.take(table["store_id"], parents),
            "value": pc.list_flatten(table["hours_sale"]),
        }
    )
    totals = flat.group_by("store").aggregate([("value", "sum")]).to_pylist()
    products = table.group_by("store_id").aggregate([("product_id", "count_distinct")]).to_pylist()
    product_count = {row["store_id"]: row["product_id_count_distinct"] for row in products}
    rows = [
        (int(row["store"]), float(row["value_sum"]), int(product_count[row["store"]]))
        for row in totals
    ]
    return sorted(rows, key=lambda row: (row[1], row[0]))


def candidate_stores(ranked: list[tuple[int, float, int]]) -> list[int]:
    if not ranked:
        return []
    picks = {ranked[round(q * (len(ranked) - 1))][0] for q in QUANTILES}
    if any(store == REFERENCE_STORE for store, _, _ in ranked):
        picks.add(REFERENCE_STORE)
    return sorted(picks)


def evaluate(path: Path, store: int) -> tuple[int, int, float]:
    mapping = SalesMapping(**MAPPING, store=str(store))
    conversion = ConversionParams(alpha=1.0, productivity=4.0, min_staff=1, night_min_staff=1)
    derived = derive_demand(path.read_bytes(), mapping, conversion, LaborRules(), sha256="rank")
    imputed = int(derived.metadata["imputed_cells"])
    unimputed = int(derived.metadata["unimputed_cells"])
    stockout = imputed + unimputed
    share = unimputed / stockout if stockout else 0.0
    return max(derived.required_staff), sum(derived.required_staff), share


def main(path: Path) -> None:
    ranked = store_totals(path)
    by_store = {store: (sales, products) for store, sales, products in ranked}
    print(HEADER)
    for store in candidate_stores(ranked):
        sales, products = by_store[store]
        peak, person_hours, share = evaluate(path, store)
        selected = PEAK_RANGE[0] <= peak <= PEAK_RANGE[1] and share < MAX_UNIMPUTED_SHARE
        print(
            f"{store},{sales:.1f},{products},{peak},{person_hours},{share:.4f},"
            f"{'yes' if selected else 'no'}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rank candidate FreshRetailNet stores")
    parser.add_argument("--file", type=Path, default=TRAIN_FILE)
    args = parser.parse_args()
    main(args.file)
