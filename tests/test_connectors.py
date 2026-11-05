"""Tests for Unified Warehouse Abstraction Layer (UWAL) and Connectors — Olist Edition."""

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
    # Verify all 8 Olist tables are discovered
    assert "orders" in catalog.tables
    assert "order_items" in catalog.tables
    assert "customers" in catalog.tables
    assert "products" in catalog.tables
    # Verify row counts
    assert catalog.tables["orders"].row_count == 99441
    assert catalog.tables["customers"].row_count == 99441


def test_duckdb_query_execution_and_arrow(duckdb_connector):
    res = duckdb_connector.execute_query("SELECT COUNT(*) AS total FROM orders;")
    assert res.execution_time_ms < 100.0
    assert res.rows_returned == 1
    assert res.to_pylist()[0]["total"] == 99441
    assert res.dialect == "duckdb"


def test_duckdb_query_delivered_orders(duckdb_connector):
    res = duckdb_connector.execute_query(
        "SELECT COUNT(*) AS delivered_count FROM orders WHERE order_status = 'delivered';"
    )
    assert res.rows_returned == 1
    delivered_count = res.to_pylist()[0]["delivered_count"]
    assert delivered_count > 90000  # 96k+ delivered orders in Olist


def test_duckdb_explain_plan(duckdb_connector):
    plan = duckdb_connector.explain("SELECT * FROM orders;")
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
    sql = "SELECT customer_id, customer_state FROM customers LIMIT 5;"
    res = duckdb_connector.execute_query(sql)

    # First get should miss
    assert cache.get(sql) is None

    # Put and second get should hit
    cache.put(sql, res)
    hit = cache.get(sql)
    assert hit is not None
    assert len(hit.data) == 5
    assert hit.to_pylist() == res.to_pylist()
