#!/usr/bin/env python3
"""Launch the local, guided showcase after checking its prerequisites."""

from __future__ import annotations

import sys
from importlib.util import find_spec
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    required = ("duckdb", "pyarrow", "pydantic", "pydantic_settings", "sqlglot", "rich", "yaml")
    missing = [module for module in required if find_spec(module) is None]
    if missing:
        print("Missing Python dependencies: " + ", ".join(missing))
        print("Install them with: python -m pip install -r requirements.txt")
        sys.exit(1)
    data_dir = PROJECT_ROOT / "data" / "seed"
    required_files = ("orders", "order_items", "order_payments", "order_reviews", "customers", "products", "sellers", "category_translation")
    missing_data = [name + ".parquet" for name in required_files if not (data_dir / (name + ".parquet")).is_file()]
    if missing_data:
        print("Missing sample data in " + str(data_dir) + ": " + ", ".join(missing_data))
        print("Restore the bundled Parquet files or run python scripts/ingest_olist.py with network access.")
        sys.exit(1)
    from src.cli import main

    try:
        main()
    except KeyboardInterrupt:
        print("\nSession ended by user.")
        sys.exit(0)
