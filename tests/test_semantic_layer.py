"""Tests for Governed Semantic Layer & Join Resolution."""

import pytest
from src.core.exceptions import SemanticResolutionError
from src.semantic.loader import SemanticLayerLoader
from src.semantic.resolver import SemanticQueryResolver


def test_semantic_layer_loader():
    loader = SemanticLayerLoader()
    cfg = loader.load()
    assert len(cfg.models) >= 5
    assert len(cfg.metrics) >= 6

    arr_metric = cfg.get_metric("arr")
    assert arr_metric is not None
    assert "SUM(mrr_amount_usd) * 12.0" in arr_metric.calculation


def test_resolve_simple_metric(semantic_resolver):
    sql = semantic_resolver.resolve_metric_query("arr")
    assert "SUM(mrr_amount_usd) * 12.0 AS arr" in sql
    assert "FROM fct_subscriptions" in sql
    assert "status = 'active'" in sql


def test_resolve_metric_with_dimension_and_join(semantic_resolver):
    sql = semantic_resolver.resolve_metric_query("arr", dimensions=["industry"])
    assert "dim_customers.industry AS industry" in sql
    assert "JOIN dim_customers ON" in sql
    assert "dim_customers.is_deleted = false" in sql
    assert "GROUP BY dim_customers.industry" in sql


def test_resolve_unknown_metric_raises_error(semantic_resolver):
    with pytest.raises(SemanticResolutionError):
        semantic_resolver.resolve_metric_query("customer_happiness_index")
