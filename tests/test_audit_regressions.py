"""Regression tests for the Enterprise Cockpit audit plan gaps.

Covers: raw-SQL preflight, calendar-year filters, Top-N limits, ascending
ordering, category translation, geographic diagnostic scoping, value
formatting, freight synonym, and New-vs-Repeat customer counts.
"""

import pyarrow as pa

from src.agents.attribution import MetricAttributionEngine
from src.agents.canvas import VisualCanvasAgent
from src.agents.router import IntentRouterAgent


def test_raw_sql_preflight_blocks_drop(orchestrator):
    state = orchestrator.process_query("DROP TABLE orders;")
    assert state.security_passed is False
    assert state.security_error and "UNAUTHORIZED_STATEMENT_TYPE" in state.security_error
    assert state.execution_result is None


def test_raw_sql_preflight_allows_select(orchestrator):
    state = orchestrator.process_query("SELECT COUNT(*) AS n FROM orders;")
    assert state.security_passed is True
    assert state.execution_result is not None
    assert state.execution_result.rows_returned == 1


def test_natural_language_select_not_treated_as_sql(orchestrator):
    # "Select the top 10 ..." is natural language, not raw SQL.
    state = orchestrator.process_query("Select the top 10 product categories by GMV")
    assert state.security_passed is True
    assert state.execution_result is not None


def test_calendar_year_filter_extraction():
    router = IntentRouterAgent()
    clause = router._extract_time_filter("what was our monthly gmv trend in 2018?")
    assert clause is not None
    assert "2018-01-01" in clause and "2019-01-01" in clause


def test_top_n_limit_extraction():
    router = IntentRouterAgent()
    assert router._extract_limit("top 10 product categories by gmv") == 10
    assert router._extract_limit("bottom 3 states") == 3
    assert router._extract_limit("no explicit limit here") is None


def test_ascending_detection():
    router = IntentRouterAgent()
    assert router._extract_order_ascending("which categories have the lowest review score") is True
    assert router._extract_order_ascending("top categories by gmv") is False


def test_freight_value_ratio_synonym():
    router = IntentRouterAgent()
    assert router._extract_metric_name("what is the freight value ratio by seller state") == "freight_value_ratio"


def test_resolver_limit_and_ascending(semantic_resolver):
    sql = semantic_resolver.resolve_metric_query(
        "avg_review_score", dimensions=["customer_state"], limit=10, order_ascending=True
    )
    assert "LIMIT 10" in sql
    assert "ORDER BY avg_review_score ASC" in sql


def test_resolver_category_translation_join(semantic_resolver):
    sql = semantic_resolver.resolve_metric_query("gmv", dimensions=["product_category_name"], limit=10)
    assert "COALESCE(category_translation.product_category_name_english" in sql
    assert "JOIN category_translation" in sql
    assert "LIMIT 10" in sql


def test_attribution_geographic_scoping():
    table = pa.table(
        {
            "customer_state": ["RJ", "SP", "MA"],
            "total_orders": [1000, 5000, 500],
            "avg_review_score": [3.96, 4.2, 3.8],
            "total_gmv": [100000.0, 500000.0, 50000.0],
            "late_delivery_pct": [13.5, 5.9, 19.0],
            "avg_delivery_days": [15.2, 10.0, 21.0],
        }
    )
    result = MetricAttributionEngine().diagnose_review_score_drivers(table, requested_state="RJ")
    assert result["requested_state"] == "RJ"
    assert result["requested_state_metrics"]["avg_review_score"] == 3.96
    assert "RJ" in result["summary_narrative"]
    assert "national benchmark" in result["summary_narrative"]
    assert "15.2 days" in result["summary_narrative"]


def test_canvas_formats_currency_and_scores():
    assert VisualCanvasAgent._format_metric_value("aov", 1235.5036158192079) == "R$ 1,235.50"
    assert VisualCanvasAgent._format_metric_value("gmv", 1000) == "R$ 1,000.00"
    assert VisualCanvasAgent._format_metric_value("avg_review_score", 3.9567) == "3.96"
    assert VisualCanvasAgent._format_metric_value("late_delivery_pct", 13.456) == "13.46%"
    assert VisualCanvasAgent._format_metric_value("total_orders", 12345) == "12,345"


def test_new_vs_repeat_count_split(orchestrator):
    state = orchestrator.process_query("What is our monthly New vs Repeat customer count split?")
    assert state.execution_result is not None
    cols = state.execution_result.column_names
    assert "new_customers" in cols and "repeat_customers" in cols


def test_multi_value_categorical_filter_uses_in_not_and(orchestrator):
    state = orchestrator.process_query(
        "Show distribution of payment methods (credit card vs boleto vs voucher)"
    )
    joined = " ".join(state.filters)
    assert "order_payments.payment_type IN (" in joined
    for val in ("credit_card", "boleto", "voucher"):
        assert val in joined
    assert "order_payments.payment_type =" not in joined


def test_resolver_combines_same_column_equalities():
    from src.semantic.resolver import SemanticQueryResolver

    sql = SemanticQueryResolver().resolve_metric_query(
        "total_payment_value",
        ["payment_type"],
        filters=[
            "order_payments.payment_type = 'boleto'",
            "order_payments.payment_type = 'credit_card'",
            "order_payments.payment_type = 'voucher'",
        ],
    )
    assert "payment_type IN ('boleto', 'credit_card', 'voucher')" in sql
    assert "payment_type = 'boleto' AND" not in sql
