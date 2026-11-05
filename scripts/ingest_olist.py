"""Ingest and convert Olist Brazilian E-Commerce dataset into optimized Parquet.

Fetches the 8 canonical Olist tables directly from public source,
normalizes data types via DuckDB, and serializes to data/seed/*.parquet.
Total: ~550,000 real-world commercial records (~15 MB compressed).
"""

from __future__ import annotations

import time
from pathlib import Path
import duckdb

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "seed"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://raw.githubusercontent.com/Ganesh7699/Brazilian-E-Commerce-OList/main/"

TABLE_SPECS = [
    ("product_category_name_translation.csv", "category_translation.parquet", "category_translation"),
    ("olist_sellers_dataset.csv", "sellers.parquet", "sellers"),
    ("olist_products_dataset.csv", "products.parquet", "products"),
    ("olist_customers_dataset.csv", "customers.parquet", "customers"),
    ("olist_order_payments_dataset.csv", "order_payments.parquet", "order_payments"),
    ("olist_order_reviews_dataset.csv", "order_reviews.parquet", "order_reviews"),
    ("olist_order_items_dataset.csv", "order_items.parquet", "order_items"),
    ("olist_orders_dataset.csv", "orders.parquet", "orders"),
]


def ingest_olist():
    con = duckdb.connect()
    print("=" * 65)
    print("🛒 Ingesting Official Olist Brazilian E-Commerce Dataset into DuckDB")
    print("=" * 65)

    total_rows = 0
    t_start = time.perf_counter()

    for csv_file, parquet_file, tbl_name in TABLE_SPECS:
        url = BASE_URL + csv_file
        dest_path = DATA_DIR / parquet_file
        print(f"Downloading & converting {csv_file} -> {parquet_file}...", end=" ", flush=True)

        t0 = time.perf_counter()
        query = f"""
            COPY (
                SELECT * FROM read_csv_auto('{url}')
            ) TO '{dest_path}' (FORMAT 'PARQUET', COMPRESSION 'SNAPPY');
        """
        con.execute(query)
        cnt = con.execute(f"SELECT COUNT(*) FROM read_parquet('{dest_path}')").fetchone()[0]
        total_rows += cnt
        elapsed = time.perf_counter() - t0
        print(f"✓ ({cnt:,} rows in {elapsed:.1f}s)")

    duration = time.perf_counter() - t_start
    print("=" * 65)
    print(f"🎉 Successfully materialized Olist Lakehouse: {total_rows:,} real commercial rows in {duration:.1f}s.")
    print(f"📁 Destination: {DATA_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    ingest_olist()
