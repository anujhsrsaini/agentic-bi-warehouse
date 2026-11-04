"""SQLGlot Multi-Dialect Transpiler.

Transpiles validated Canonical SQL (DuckDB/ANSI) to target warehouse dialects:
- Snowflake
- BigQuery
- PostgreSQL
- ClickHouse
- DuckDB
"""

from __future__ import annotations

import sqlglot


class DialectTranspiler:
    """Translates Canonical ANSI/DuckDB SQL to warehouse-specific dialects."""

    SUPPORTED_DIALECTS = {"duckdb", "postgres", "snowflake", "bigquery", "clickhouse"}

    @classmethod
    def transpile(cls, sql: str, target_dialect: str, source_dialect: str = "duckdb") -> str:
        """Transpile SQL to target dialect."""
        target = target_dialect.lower()
        if target not in cls.SUPPORTED_DIALECTS:
            target = "duckdb"

        if source_dialect.lower() == target:
            return sql.strip()

        try:
            transpiled = sqlglot.transpile(sql, read=source_dialect, write=target, pretty=True)[0]
            return transpiled
        except Exception:
            # Fallback to source SQL if transpilation encounters dialect-specific edge cases
            return sql.strip()
