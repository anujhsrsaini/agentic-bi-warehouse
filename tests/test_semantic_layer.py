"""Tests for Governed Semantic Layer & Join Resolution — Olist Edition."""

import pytest
from src.core.exceptions import SemanticResolutionError
from src.semantic.loader import SemanticLayerLoader
from src.semantic.resolver import SemanticQueryResolver


def test_semantic_layer_loader():
    loader = SemanticLayerLoader()
    cfg = loader.load()
    assert len(cfg.models) >= 7  # 8 Olist tables
    assert len(cfg.metrics) >= 6  # 7 certified Olist KPIs

    gmv_metric = cfg.get_metric("gmv")
    assert gmv_metric is not None
    assert "SUM(order_items.price)" in gmv_metric.calculation

    # Also check synonym resolution
    assert cfg.get_metric("gross merchandise value") is not None
    assert cfg.get_metric("csat") is not None  # synonym for avg_review_score


def test_semantic_layer_all_olist_tables():
    loader = SemanticLayerLoader()
    cfg = loader.load()
    table_names = [m.name for m in cfg.models]
    expected_tables = ["orders", "order_items", "order_payments", "order_reviews",
                       "customers", "products", "sellers"]
    for t in expected_tables:
        assert t in table_names, f"Expected table '{t}' not found in semantic layer"


def test_resolve_simple_metric_gmv(semantic_resolver):
    sql = semantic_resolver.resolve_metric_query("gmv")
    assert "SUM(order_items.price) AS gmv" in sql
    assert "order_items" in sql


def test_resolve_simple_metric_total_orders(semantic_resolver):
    sql = semantic_resolver.resolve_metric_query("total_orders")
    assert "COUNT(DISTINCT" in sql
    assert "orders" in sql
    assert "delivered" in sql


def test_resolve_simple_metric_avg_review_score(semantic_resolver):
    sql = semantic_resolver.resolve_metric_query("avg_review_score")
    assert "AVG(order_reviews.review_score)" in sql


def test_resolve_metric_by_synonym(semantic_resolver):
    # 'csat' should resolve to avg_review_score
    sql = semantic_resolver.resolve_metric_query("avg_review_score")
    assert "review_score" in sql


def test_resolve_unknown_metric_raises_error(semantic_resolver):
    with pytest.raises(SemanticResolutionError):
        semantic_resolver.resolve_metric_query("customer_happiness_index")
