"""Tests for ColumnLineageTracer."""

import pytest
from src.engine.lineage import ColumnLineageTracer


def test_column_lineage_ascii_and_mermaid():
    tracer = ColumnLineageTracer()
    sql = """
    SELECT
        dim_customers.industry,
        SUM(fct_subscriptions.mrr_amount_usd) as total_mrr
    FROM fct_subscriptions
    JOIN dim_customers ON fct_subscriptions.customer_id = dim_customers.customer_id
    GROUP BY dim_customers.industry;
    """
    ascii_tree = tracer.to_ascii_tree("total_mrr", sql)
    assert "Lineage: total_mrr" in ascii_tree

    mermaid = tracer.to_mermaid("total_mrr", sql)
    assert "flowchart LR" in mermaid
    assert "total_mrr" in mermaid

    narrative = tracer.generate_audit_narrative("total_mrr", sql)
    assert "Mathematical Lineage Audit" in narrative
    assert "soft-deleted" not in narrative


def test_failed_lineage_is_explicitly_unavailable():
    tracer = ColumnLineageTracer()
    assert "unavailable" in tracer.to_ascii_tree("missing", "SELECT 1 AS value").lower()
    assert "unavailable" in tracer.generate_audit_narrative("missing", "SELECT 1 AS value").lower()
