"""Tests for Semantic Bootstrap Engine — Olist Edition."""

import pytest
from src.semantic.bootstrapper import SemanticBootstrapEngine


def test_semantic_bootstrap_discovers_schema(duckdb_connector):
    engine = SemanticBootstrapEngine(duckdb_connector)
    config = engine.bootstrap()

    assert config["version"] == "1.0"
    model_names = [m["name"] for m in config["models"]]
    # Should discover at least the core Olist tables
    assert "orders" in model_names or "order_items" in model_names
    assert len(config["models"]) >= 4
