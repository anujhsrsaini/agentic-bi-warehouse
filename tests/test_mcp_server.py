"""Tests for Model Context Protocol (FastMCP) Tools."""

import json
import pytest
from src.mcp.server import get_dataset_schema, list_governed_metrics, query_analytics_warehouse


def test_list_governed_metrics_tool():
    res = list_governed_metrics()
    metrics = json.loads(res)
    assert len(metrics) >= 6
    names = [m["name"] for m in metrics]
    assert "arr" in names
    assert "nrr" in names or "mrr" in names


def test_get_dataset_schema_tool():
    res = get_dataset_schema()
    catalog = json.loads(res)
    assert "dim_customers" in catalog
    assert "columns" in catalog["dim_customers"]


def test_query_analytics_warehouse_tool():
    res_str = query_analytics_warehouse("What is our ARR by industry?")
    res = json.loads(res_str)
    assert res["status"] == "success"
    assert "Cybersecurity" in res["summary"] or "Fintech" in res["summary"] or len(res["data"]) > 0
    assert "SELECT" in res["sql_executed"]
