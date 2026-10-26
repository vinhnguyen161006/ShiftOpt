import hashlib
import shutil
import urllib.request
from pathlib import Path

from src.demand.dataset_loader import HF_REVISION

REPO = "Dingdong-Inc/FreshRetailNet-50K"
BASE_URL = f"https://huggingface.co/datasets/{REPO}/resolve/{HF_REVISION}/"
SHA256_BY_FILE = {
    "data/train.parquet": "6706832db892bbae4969c19d87e07975d2543d2ba7d7d4756360654785de5a3d",
    "data/eval.parquet": "1b118840664280c6b88bffc84c80ee1f54c05d911e354b7599e5da10995e960e",
}
ROOT = Path(__file__).resolve().parents[2]
TARGET_DIR = ROOT / "data" / "raw" / "freshretailnet50k"
CHUNK_BYTES = 1 << 20


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(name: str, expected: str) -> None:
    destination = TARGET_DIR / name
    if destination.exists() and sha256_of(destination) == expected:
        print(f"ok      {name}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    with (
        urllib.request.urlopen(BASE_URL + name, timeout=300) as response,
        partial.open("wb") as handle,
    ):
        shutil.copyfileobj(response, handle, CHUNK_BYTES)
    if sha256_of(partial) != expected:
        partial.unlink()
        raise SystemExit(f"checksum mismatch for {name}; download discarded")
    partial.replace(destination)
    print(f"fetched {name}")


def main() -> None:
    for name, expected in SHA256_BY_FILE.items():
        fetch(name, expected)


if __name__ == "__main__":
    main()
