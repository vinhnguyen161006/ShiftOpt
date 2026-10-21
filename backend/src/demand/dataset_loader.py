from pathlib import Path


def load_hourly_load(dataset_dir: Path, store_id: int) -> list[float]:
    """TODO: read data/processed/demand_store_<id>.parquet and return the 168-hour load index
    of a typical week (mean per weekday and hour).

    Sum hours_sale over products per date and hour. Replace hours flagged in
    hours_stock_status with the latent demand estimate (mean of the same hour and weekday over
    non-stockout days). Raise NotFoundError for an unknown store.
    """
    raise NotImplementedError


def build_processed_store(raw_dir: Path, processed_dir: Path, store_id: int) -> Path:
    """TODO: aggregate the raw FreshRetailNet-50K parquet of one store into the processed file."""
    raise NotImplementedError
