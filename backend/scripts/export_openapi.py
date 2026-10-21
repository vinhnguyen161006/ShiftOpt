"""Write the FastAPI OpenAPI schema to backend/openapi.json for frontend type generation."""

import json
from pathlib import Path

from src.main import create_app

OUTPUT = Path(__file__).resolve().parents[1] / "openapi.json"


def main() -> None:
    schema = create_app().openapi()
    OUTPUT.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
