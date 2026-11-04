"""ClickHouse Warehouse Connector Implementation."""

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


class ClickHouseConnector(BaseWarehouseConnector):
    """ClickHouse real-time columnar OLAP connector."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
    ):
        self.host = host or settings.clickhouse_host
        self.port = port or settings.clickhouse_port
        self.user = user or settings.clickhouse_user
        self.password = password or settings.clickhouse_password
        self.database = database or settings.clickhouse_database
        self._client = None

    def connect(self) -> None:
        try:
            import clickhouse_connect
            self._client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                database=self.database,
            )
        except ImportError:
            raise WarehouseConnectionError("clickhouse-connect not installed. Install via `pip install clickhouse-connect`.")
        except Exception as e:
            raise WarehouseConnectionError(f"Failed to connect to ClickHouse: {e}") from e

    def disconnect(self) -> None:
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def test_connection(self) -> bool:
        try:
            if not self._client:
                self.connect()
            res = self._client.command("SELECT 1")
            return res == 1
        except Exception:
            return False

    def introspect_schema(self, schema_name: str | None = None, table_filter: list[str] | None = None) -> CatalogSchema:
        if not self._client:
            self.connect()
        target_db = schema_name or self.database
        catalog = CatalogSchema()

        tables = self._client.command(f"SHOW TABLES FROM {target_db}")
        if isinstance(tables, str):
            table_list = tables.splitlines()
        else:
            table_list = list(tables)

        for tbl in table_list:
            if table_filter and tbl not in table_filter:
                continue
            desc_rows = self._client.query(f"DESCRIBE TABLE {target_db}.{tbl}").result_rows
            columns = {}
            for col_info in desc_rows:
                col_name = col_info[0]
                raw_type = col_info[1]
                columns[col_name] = ColumnMetadata(
                    name=col_name,
                    standard_type=self._map_type(raw_type),
                    raw_type=raw_type,
                )
            catalog.tables[tbl] = TableMetadata(table_name=tbl, schema_name=target_db, columns=columns)
        return catalog

    def execute_query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        limit: int | None = None,
        timeout_ms: int | None = None,
    ) -> QueryResult:
        if not self._client:
            self.connect()

        ch_sql = sqlglot.transpile(sql, read="duckdb", write="clickhouse")[0]
        if limit is not None and "LIMIT" not in ch_sql.upper():
            ch_sql = f"{ch_sql} LIMIT {limit}"

        start_time = time.perf_counter()
        try:
            arrow_table = self._client.query_arrow(ch_sql)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return QueryResult(
                data=arrow_table,
                execution_time_ms=elapsed_ms,
                rows_scanned=len(arrow_table),
                rows_returned=len(arrow_table),
                dialect=self.get_dialect(),
                sql=ch_sql,
            )
        except Exception as e:
            raise QueryExecutionError(f"ClickHouse execution failed: {e}", sql=ch_sql, dialect="clickhouse", raw_error=e) from e

    def explain(self, sql: str) -> str:
        if not self._client:
            self.connect()
        ch_sql = sqlglot.transpile(sql, read="duckdb", write="clickhouse")[0]
        res = self._client.command(f"EXPLAIN {ch_sql}")
        return str(res)

    def get_dialect(self) -> str:
        return "clickhouse"

    def _map_type(self, raw_type: str) -> StandardDataType:
        t = raw_type.upper()
        if "INT" in t:
            return StandardDataType.INTEGER
        if "FLOAT" in t or "DECIMAL" in t:
            return StandardDataType.FLOAT
        if "STRING" in t or "FIXEDSTRING" in t or "LOWCARDINALITY" in t:
            return StandardDataType.STRING
        if "BOOL" in t:
            return StandardDataType.BOOLEAN
        if "DATETIME" in t:
            return StandardDataType.TIMESTAMP
        if "DATE" in t:
            return StandardDataType.DATE
        if "TUPLE" in t or "MAP" in t or "JSON" in t:
            return StandardDataType.JSON
        if "ARRAY" in t:
            return StandardDataType.ARRAY
        return StandardDataType.UNKNOWN
