import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "openapi.yaml"
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app


def main() -> None:
    OUTPUT_PATH.write_text(
        json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote OpenAPI contract to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
