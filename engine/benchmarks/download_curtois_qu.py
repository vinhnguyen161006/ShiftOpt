import hashlib
import urllib.request
from pathlib import Path

BASE_URL = "https://www.schedulingbenchmarks.org/nrp/data"
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "benchmarks" / "curtois_qu"
SHA256 = {
    "Instance1.txt": "f982418dfd05e44e3738656d2da18e751bf9b7741d36d299dd394d79c275af64",
    "Instance2.txt": "66f4ceb916ade9edd93eade3e858fb9e7c5586aa47be4696309a680c9f159a29",
    "Instance3.txt": "dba847106a84a6f9dfeb282278c3668fb681c52cb353b0ebfde5195eb9e98286",
    "Instance4.txt": "927967253110a0a5d48c22f51d45abd6efae0be581bdd875a2f898465f6e032c",
    "Instance5.txt": "068edbebb062ced2c29e8b85d3328ee7bc8a1bf3370ef754f3d88d1f0a6e5144",
}


def sha256_of(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch(name: str) -> None:
    target = DATA_DIR / name
    if target.exists() and sha256_of(target.read_bytes()) == SHA256[name]:
        return
    with urllib.request.urlopen(f"{BASE_URL}/{name}", timeout=30) as response:
        payload: bytes = response.read()
    digest = sha256_of(payload)
    if digest != SHA256[name]:
        raise RuntimeError(f"{name}: sha256 {digest} does not match the pinned value")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    print(f"downloaded {name}")


def main() -> None:
    for name in SHA256:
        fetch(name)


if __name__ == "__main__":
    main()
