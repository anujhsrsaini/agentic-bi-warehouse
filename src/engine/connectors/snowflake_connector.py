"""Snowflake Warehouse Connector Implementation."""

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


class SnowflakeConnector(BaseWarehouseConnector):
    """Snowflake cloud warehouse connector with native Arrow batch streaming."""

    def __init__(
        self,
        account: str | None = None,
        user: str | None = None,
        password: str | None = None,
        warehouse: str | None = None,
        database: str | None = None,
        schema: str | None = None,
    ):
        self.account = account or settings.snowflake_account
        self.user = user or settings.snowflake_user
        self.password = password or settings.snowflake_password
        self.warehouse = warehouse or settings.snowflake_warehouse
        self.database = database or settings.snowflake_database
        self.schema = schema or settings.snowflake_schema
        self._conn = None

    def connect(self) -> None:
        if not (self.account and self.user and self.password):
            raise WarehouseConnectionError("Snowflake credentials not provided. Set AGENTIC_BI_SNOWFLAKE_* environment variables.")
        try:
            import snowflake.connector
            self._conn = snowflake.connector.connect(
                account=self.account,
                user=self.user,
                password=self.password,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema,
            )
        except ImportError:
            raise WarehouseConnectionError("snowflake-connector-python is not installed. Install via `pip install snowflake-connector-python[pandas]`.")
        except Exception as e:
            raise WarehouseConnectionError(f"Failed to connect to Snowflake: {e}") from e

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
            cur = self._conn.cursor()
            cur.execute("SELECT 1;")
            return cur.fetchone() == (1,)
        except Exception:
            return False

    def introspect_schema(self, schema_name: str | None = None, table_filter: list[str] | None = None) -> CatalogSchema:
        if not self._conn:
            self.connect()
        target_schema = schema_name or self.schema or "PUBLIC"
        catalog = CatalogSchema()

        cur = self._conn.cursor()
        cur.execute(f"SHOW TABLES IN SCHEMA {target_schema};")
        tables = [r[1] for r in cur.fetchall()]

        for tbl in tables:
            if table_filter and tbl not in table_filter:
                continue
            cur.execute(f"DESCRIBE TABLE {target_schema}.{tbl};")
            cols = cur.fetchall()
            columns = {}
            for col_info in cols:
                col_name = col_info[0]
                raw_type = col_info[1]
                columns[col_name] = ColumnMetadata(
                    name=col_name,
                    standard_type=self._map_type(raw_type),
                    raw_type=raw_type,
                )
            catalog.tables[tbl] = TableMetadata(table_name=tbl, schema_name=target_schema, columns=columns)
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

        sf_sql = sqlglot.transpile(sql, read="duckdb", write="snowflake")[0]
        if limit is not None and "LIMIT" not in sf_sql.upper():
            sf_sql = f"{sf_sql} LIMIT {limit}"

        start_time = time.perf_counter()
        try:
            cur = self._conn.cursor()
            cur.execute(sf_sql)
            # Arrow batch streaming
            arrow_batches = cur.fetch_arrow_all()
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            arrow_table = pa.Table.from_batches([arrow_batches]) if isinstance(arrow_batches, pa.RecordBatch) else arrow_batches

            return QueryResult(
                data=arrow_table,
                execution_time_ms=elapsed_ms,
                rows_scanned=len(arrow_table),
                rows_returned=len(arrow_table),
                dialect=self.get_dialect(),
                sql=sf_sql,
            )
        except Exception as e:
            raise QueryExecutionError(f"Snowflake execution failed: {e}", sql=sf_sql, dialect="snowflake", raw_error=e) from e

    def explain(self, sql: str) -> str:
        if not self._conn:
            self.connect()
        sf_sql = sqlglot.transpile(sql, read="duckdb", write="snowflake")[0]
        cur = self._conn.cursor()
        cur.execute(f"EXPLAIN USING JSON {sf_sql};")
        return str(cur.fetchall())

    def get_dialect(self) -> str:
        return "snowflake"

    def _map_type(self, raw_type: str) -> StandardDataType:
        t = raw_type.upper()
        if "NUMBER" in t or "INT" in t:
            return StandardDataType.INTEGER
        if "FLOAT" in t or "DOUBLE" in t or "REAL" in t:
            return StandardDataType.FLOAT
        if "VARCHAR" in t or "TEXT" in t or "STRING" in t:
            return StandardDataType.STRING
        if "BOOLEAN" in t:
            return StandardDataType.BOOLEAN
        if "TIMESTAMP" in t:
            return StandardDataType.TIMESTAMP
        if "DATE" in t:
            return StandardDataType.DATE
        if "VARIANT" in t or "OBJECT" in t:
            return StandardDataType.JSON
        if "ARRAY" in t:
            return StandardDataType.ARRAY
        return StandardDataType.UNKNOWN
