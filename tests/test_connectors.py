"""Tests for Unified Warehouse Abstraction Layer (UWAL) and Connectors."""

import pytest
from src.engine.connectors.duckdb_connector import DuckDBConnector
from src.engine.connectors.postgres_connector import PostgresConnector
from src.engine.connectors.snowflake_connector import SnowflakeConnector
from src.engine.connectors.bigquery_connector import BigQueryConnector
from src.engine.connectors.clickhouse_connector import ClickHouseConnector
from src.engine.cache import ParquetQueryCache


def test_duckdb_connection_and_introspection(duckdb_connector):
    assert duckdb_connector.test_connection() is True
    catalog = duckdb_connector.introspect_schema()
    assert "dim_customers" in catalog.tables
    assert "fct_subscriptions" in catalog.tables
    assert catalog.tables["dim_customers"].row_count == 10000


def test_duckdb_query_execution_and_arrow(duckdb_connector):
    res = duckdb_connector.execute_query("SELECT COUNT(*) AS total FROM dim_customers;")
    assert res.execution_time_ms < 50.0
    assert res.rows_returned == 1
    assert res.to_pylist() == [{"total": 10000}]
    assert res.dialect == "duckdb"


def test_duckdb_explain_plan(duckdb_connector):
    plan = duckdb_connector.explain("SELECT * FROM dim_customers;")
    assert "PLAN" in plan.upper() or "SCAN" in plan.upper()


def test_warehouse_connector_dialects():
    pg = PostgresConnector(uri="postgresql://user:pass@localhost:5432/db")
    sf = SnowflakeConnector()
    bq = BigQueryConnector(project_id="test-proj")
    ch = ClickHouseConnector()

    assert pg.get_dialect() == "postgres"
    assert sf.get_dialect() == "snowflake"
    assert bq.get_dialect() == "bigquery"
    assert ch.get_dialect() == "clickhouse"


def test_parquet_query_cache(duckdb_connector, tmp_path):
    cache = ParquetQueryCache(cache_dir=tmp_path)
    sql = "SELECT customer_id, industry FROM dim_customers LIMIT 5;"
    res = duckdb_connector.execute_query(sql)

    # First get should miss
    assert cache.get(sql) is None

    # Put and second get should hit
    cache.put(sql, res)
    hit = cache.get(sql)
    assert hit is not None
    assert len(hit.data) == 5
    assert hit.to_pylist() == res.to_pylist()
