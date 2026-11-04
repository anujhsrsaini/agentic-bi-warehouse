"""Tests for Semantic Bootstrap Engine."""

import pytest
from src.semantic.bootstrapper import SemanticBootstrapEngine


def test_semantic_bootstrap_discovers_schema(duckdb_connector):
    engine = SemanticBootstrapEngine(duckdb_connector)
    config = engine.bootstrap()

    assert config["version"] == "1.0"
    model_names = [m["name"] for m in config["models"]]
    assert "dim_customers" in model_names
    assert "fct_subscriptions" in model_names
    assert len(config["metrics"]) > 0
