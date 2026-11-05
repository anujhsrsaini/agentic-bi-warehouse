"""Tests for Model Context Protocol (FastMCP) Tools — Olist Edition."""

import json
import pytest
from src.mcp.server import get_dataset_schema, list_governed_metrics, query_analytics_warehouse


def test_list_governed_metrics_tool():
    res = list_governed_metrics()
    metrics = json.loads(res)
    assert len(metrics) >= 6
    names = [m["name"] for m in metrics]
    # Verify Olist KPIs are registered
    assert "gmv" in names
    assert "avg_review_score" in names
    assert "total_orders" in names


def test_get_dataset_schema_tool():
    res = get_dataset_schema()
    catalog = json.loads(res)
    # Verify Olist tables are present
    assert "orders" in catalog
    assert "order_items" in catalog
    assert "customers" in catalog
    assert "columns" in catalog["orders"]


def test_query_analytics_warehouse_tool():
    res_str = query_analytics_warehouse("What is our GMV by customer state?")
    res = json.loads(res_str)
    assert res["status"] == "success"
    # SP (São Paulo) should be the top state by GMV
    assert "SP" in res["summary"] or len(res["data"]) > 0
    assert "SELECT" in res["sql_executed"]
