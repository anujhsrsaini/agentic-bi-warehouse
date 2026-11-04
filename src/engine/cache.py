"""Universal Parquet Query Caching Layer (Evidence.dev Pattern).

Caches analytical query results locally as Parquet files:
- Hashes normalized SQL queries
- Stores serialized results in .cache/parquet/{hash}.parquet
- Returns zero-copy PyArrow tables on cache hit
- Significantly reduces cloud warehouse compute costs and latency
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
import pyarrow.parquet as pq
import sqlglot

from src.core.config import settings
from src.engine.connectors.base import QueryResult


class ParquetQueryCache:
    """Parquet-backed local query cache."""

    def __init__(self, cache_dir: Path | str | None = None, ttl_seconds: int = 3600):
        self.cache_dir = Path(cache_dir or (settings.cache_dir / "parquet"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def _hash_sql(self, sql: str, dialect: str) -> str:
        """Normalize SQL via SQLGlot and generate deterministic SHA256 key."""
        try:
            normalized = sqlglot.transpile(sql, read=dialect, write="duckdb", pretty=False)[0]
        except Exception:
            normalized = " ".join(sql.strip().lower().split())
        return hashlib.sha256(f"{dialect}:{normalized}".encode("utf-8")).hexdigest()

    def get(self, sql: str, dialect: str = "duckdb") -> QueryResult | None:
        """Retrieve cached query result if available and fresh."""
        cache_key = self._hash_sql(sql, dialect)
        cache_file = self.cache_dir / f"{cache_key}.parquet"

        if not cache_file.exists():
            return None

        # Check TTL
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > self.ttl_seconds:
            try:
                cache_file.unlink()
            except Exception:
                pass
            return None

        start_time = time.perf_counter()
        try:
            arrow_table = pq.read_table(cache_file)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return QueryResult(
                data=arrow_table,
                execution_time_ms=elapsed_ms,
                rows_scanned=len(arrow_table),
                rows_returned=len(arrow_table),
                dialect=dialect,
                sql=f"-- (FROM PARQUET CACHE)\n{sql}",
            )
        except Exception:
            return None

    def put(self, sql: str, result: QueryResult, dialect: str = "duckdb") -> None:
        """Cache QueryResult as Parquet."""
        cache_key = self._hash_sql(sql, dialect)
        cache_file = self.cache_dir / f"{cache_key}.parquet"
        try:
            pq.write_table(result.data, cache_file, compression="SNAPPY")
        except Exception:
            pass

    def clear(self) -> int:
        """Clear all cached Parquet files and return count."""
        count = 0
        for f in self.cache_dir.glob("*.parquet"):
            try:
                f.unlink()
                count += 1
            except Exception:
                pass
        return count
