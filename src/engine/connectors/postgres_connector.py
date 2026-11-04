"""PostgreSQL Warehouse Connector Implementation."""

from __future__ import annotations

import time
from typing import Any
import pyarrow as pa
import sqlglot

from src.core.config import settings
from src.core.exceptions import QueryExecutionError, WarehouseConnectionError
from src.engine.connectors.base import (
    BaseWarehouseConnector,
    CatalogSchema,
    ColumnMetadata,
    QueryResult,
    StandardDataType,
    TableMetadata,
)


class PostgresConnector(BaseWarehouseConnector):
    """PostgreSQL warehouse connector using psycopg3."""

    def __init__(self, uri: str | None = None, statement_timeout_ms: int = 30000):
        self.uri = uri or settings.postgres_uri
        self.statement_timeout_ms = statement_timeout_ms
        self._conn = None

    def connect(self) -> None:
        """Establish connection to PostgreSQL."""
        if not self.uri:
            raise WarehouseConnectionError("PostgreSQL URI not configured. Set AGENTIC_BI_POSTGRES_URI.")
        try:
            import psycopg
            self._conn = psycopg.connect(self.uri)
            with self._conn.cursor() as cur:
                cur.execute(f"SET statement_timeout = '{self.statement_timeout_ms}ms';")
        except ImportError:
            raise WarehouseConnectionError("psycopg package is not installed. Install with `pip install psycopg[binary]`.")
        except Exception as e:
            raise WarehouseConnectionError(f"Failed to connect to PostgreSQL: {e}") from e

    def disconnect(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def test_connection(self) -> bool:
        try:
            if not self._conn:
                self.connect()
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1;")
                return cur.fetchone() == (1,)
        except Exception:
            return False

    def introspect_schema(self, schema_name: str | None = None, table_filter: list[str] | None = None) -> CatalogSchema:
        if not self._conn:
            self.connect()
        catalog = CatalogSchema()
        target_schema = schema_name or "public"

        with self._conn.cursor() as cur:
            cur.execute(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{target_schema}';
            """)
            tables = [r[0] for r in cur.fetchall()]

            for tbl in tables:
                if table_filter and tbl not in table_filter:
                    continue
                cur.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = '{target_schema}' AND table_name = '{tbl}'
                    ORDER BY ordinal_position;
                """)
                col_rows = cur.fetchall()
                columns = {}
                for col_name, raw_type, is_null in col_rows:
                    columns[col_name] = ColumnMetadata(
                        name=col_name,
                        standard_type=self._map_type(raw_type),
                        raw_type=raw_type,
                        nullable=(is_null == "YES"),
                    )
                catalog.tables[tbl] = TableMetadata(
                    table_name=tbl,
                    schema_name=target_schema,
                    columns=columns,
                )
        return catalog

    def execute_query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        limit: int | None = None,
        timeout_ms: int | None = None,
    ) -> QueryResult:
        if not self._conn:
            self.connect()

        # Transpile DuckDB/ANSI SQL to Postgres dialect
        pg_sql = sqlglot.transpile(sql, read="duckdb", write="postgres")[0]
        if limit is not None and "LIMIT" not in pg_sql.upper():
            pg_sql = f"{pg_sql} LIMIT {limit}"

        start_time = time.perf_counter()
        try:
            with self._conn.cursor() as cur:
                cur.execute(pg_sql, params or ())
                records = cur.fetchall()
                col_names = [desc[0] for desc in cur.description] if cur.description else []
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                # Convert to Arrow Table
                pydict = {col: [row[i] for row in records] for i, col in enumerate(col_names)}
                arrow_table = pa.Table.from_pydict(pydict)

                return QueryResult(
                    data=arrow_table,
                    execution_time_ms=elapsed_ms,
                    rows_scanned=len(records),
                    rows_returned=len(records),
                    dialect=self.get_dialect(),
                    sql=pg_sql,
                )
        except Exception as e:
            raise QueryExecutionError(f"PostgreSQL query execution failed: {e}", sql=pg_sql, dialect="postgres", raw_error=e) from e

    def explain(self, sql: str) -> str:
        if not self._conn:
            self.connect()
        pg_sql = sqlglot.transpile(sql, read="duckdb", write="postgres")[0]
        with self._conn.cursor() as cur:
            cur.execute(f"EXPLAIN {pg_sql}")
            return "\n".join(r[0] for r in cur.fetchall())

    def get_dialect(self) -> str:
        return "postgres"

    def _map_type(self, raw_type: str) -> StandardDataType:
        t = raw_type.upper()
        if any(x in t for x in ["INT", "SERIAL"]):
            return StandardDataType.INTEGER
        if any(x in t for x in ["NUMERIC", "DECIMAL", "REAL", "DOUBLE"]):
            return StandardDataType.FLOAT
        if any(x in t for x in ["VARCHAR", "TEXT", "CHAR"]):
            return StandardDataType.STRING
        if "BOOL" in t:
            return StandardDataType.BOOLEAN
        if "TIMESTAMP" in t:
            return StandardDataType.TIMESTAMP
        if "DATE" in t:
            return StandardDataType.DATE
        if "JSON" in t:
            return StandardDataType.JSON
        return StandardDataType.UNKNOWN
