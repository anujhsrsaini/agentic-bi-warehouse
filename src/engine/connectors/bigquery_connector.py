"""Google BigQuery Warehouse Connector Implementation."""

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
    QueryCostEstimate,
    QueryResult,
    StandardDataType,
    TableMetadata,
)


class BigQueryConnector(BaseWarehouseConnector):
    """Google BigQuery cloud warehouse connector with dry-run cost protection."""

    def __init__(
        self,
        project_id: str | None = None,
        dataset_id: str | None = None,
        max_bytes_billed: int | None = None,
    ):
        self.project_id = project_id or settings.bigquery_project_id
        self.dataset_id = dataset_id or settings.bigquery_dataset_id
        self.max_bytes_billed = max_bytes_billed or settings.bigquery_max_bytes_billed
        self._client = None

    def connect(self) -> None:
        if not self.project_id:
            raise WarehouseConnectionError("BigQuery Project ID not configured. Set AGENTIC_BI_BIGQUERY_PROJECT_ID.")
        try:
            from google.cloud import bigquery
            self._client = bigquery.Client(project=self.project_id)
        except ImportError:
            raise WarehouseConnectionError("google-cloud-bigquery not installed. Install via `pip install google-cloud-bigquery google-cloud-bigquery-storage`.")
        except Exception as e:
            raise WarehouseConnectionError(f"Failed to connect to BigQuery: {e}") from e

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
            query_job = self._client.query("SELECT 1 AS test;")
            res = list(query_job.result())
            return len(res) > 0
        except Exception:
            return False

    def introspect_schema(self, schema_name: str | None = None, table_filter: list[str] | None = None) -> CatalogSchema:
        if not self._client:
            self.connect()
        target_dataset = schema_name or self.dataset_id
        catalog = CatalogSchema()

        dataset_ref = self._client.dataset(target_dataset)
        tables = list(self._client.list_tables(dataset_ref))

        for tbl_item in tables:
            tbl_id = tbl_item.table_id
            if table_filter and tbl_id not in table_filter:
                continue
            table_obj = self._client.get_table(tbl_item)
            columns = {}
            for field in table_obj.schema:
                columns[field.name] = ColumnMetadata(
                    name=field.name,
                    standard_type=self._map_type(field.field_type),
                    raw_type=field.field_type,
                    nullable=(field.mode != "REQUIRED"),
                )
            catalog.tables[tbl_id] = TableMetadata(
                table_name=tbl_id,
                schema_name=target_dataset,
                columns=columns,
                row_count=table_obj.num_rows,
            )
        return catalog

    def estimate_cost_or_bytes(self, sql: str) -> QueryCostEstimate:
        """Execute BigQuery dry-run to determine scanned bytes and estimated cost."""
        if not self._client:
            self.connect()
        from google.cloud import bigquery
        bq_sql = sqlglot.transpile(sql, read="duckdb", write="bigquery")[0]
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        query_job = self._client.query(bq_sql, job_config=job_config)

        scanned_bytes = query_job.total_bytes_processed
        # BigQuery on-demand pricing: $6.25 per TB ($6.25 / 10^12 bytes)
        cost_usd = (scanned_bytes / (1024 ** 4)) * 6.25
        will_exceed = scanned_bytes > self.max_bytes_billed

        return QueryCostEstimate(
            estimated_bytes=scanned_bytes,
            estimated_cost_usd=round(cost_usd, 4),
            will_exceed_limit=will_exceed,
            explanation=f"Scans {scanned_bytes / (1024**2):.1f} MB (~${cost_usd:.4f} USD)",
        )

    def execute_query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        limit: int | None = None,
        timeout_ms: int | None = None,
    ) -> QueryResult:
        if not self._client:
            self.connect()
        from google.cloud import bigquery

        bq_sql = sqlglot.transpile(sql, read="duckdb", write="bigquery")[0]
        if limit is not None and "LIMIT" not in bq_sql.upper():
            bq_sql = f"{bq_sql} LIMIT {limit}"

        start_time = time.perf_counter()
        try:
            job_config = bigquery.QueryJobConfig(maximum_bytes_billed=self.max_bytes_billed)
            query_job = self._client.query(bq_sql, job_config=job_config)
            arrow_table = query_job.to_arrow()
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return QueryResult(
                data=arrow_table,
                execution_time_ms=elapsed_ms,
                rows_scanned=query_job.total_rows or len(arrow_table),
                rows_returned=len(arrow_table),
                bytes_scanned=query_job.total_bytes_billed,
                dialect=self.get_dialect(),
                sql=bq_sql,
            )
        except Exception as e:
            raise QueryExecutionError(f"BigQuery execution failed: {e}", sql=bq_sql, dialect="bigquery", raw_error=e) from e

    def explain(self, sql: str) -> str:
        estimate = self.estimate_cost_or_bytes(sql)
        return f"BigQuery Dry-Run: {estimate.explanation}"

    def get_dialect(self) -> str:
        return "bigquery"

    def _map_type(self, raw_type: str) -> StandardDataType:
        t = raw_type.upper()
        if "INT" in t:
            return StandardDataType.INTEGER
        if "FLOAT" in t or "NUMERIC" in t or "BIGNUMERIC" in t:
            return StandardDataType.FLOAT
        if "STRING" in t:
            return StandardDataType.STRING
        if "BOOL" in t:
            return StandardDataType.BOOLEAN
        if "TIMESTAMP" in t:
            return StandardDataType.TIMESTAMP
        if "DATE" in t:
            return StandardDataType.DATE
        if "RECORD" in t or "STRUCT" in t or "JSON" in t:
            return StandardDataType.JSON
        return StandardDataType.UNKNOWN
