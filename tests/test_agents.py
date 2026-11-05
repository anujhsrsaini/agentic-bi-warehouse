"""Unit tests for Multi-Agent Brain components — Olist Edition."""

import pytest
import pyarrow as pa
from src.agents.attribution import MetricAttributionEngine
from src.agents.canvas import VisualCanvasAgent
from src.agents.entity_grounder import CategoricalEntityGrounder
from src.agents.router import IntentRouterAgent
from src.agents.state import AgenticBIState, UserIntent
from src.security.transpiler import DialectTranspiler


def test_intent_router_ambiguity():
    router = IntentRouterAgent()
    state = AgenticBIState(question="Show revenue")
    routed = router.route(state)
    assert routed.intent == UserIntent.CLARIFICATION_REQUIRED
    assert len(routed.clarification_options) == 3
    # GMV option should appear in the clarification choices
    all_text = routed.clarification_prompt + " ".join(routed.clarification_options)
    assert "GMV" in all_text


def test_intent_router_diagnostic():
    router = IntentRouterAgent()
    state = AgenticBIState(question="Why did review scores drop in RJ?")
    routed = router.route(state)
    assert routed.intent == UserIntent.DIAGNOSTIC_WHY


def test_intent_router_gmv_certified():
    router = IntentRouterAgent()
    state = AgenticBIState(question="What is our GMV by customer state?")
    routed = router.route(state)
    assert routed.intent == UserIntent.CERTIFIED_METRIC
    assert routed.metric_name == "gmv"


def test_entity_grounder_brazilian_states():
    grounder = CategoricalEntityGrounder()
    matches = grounder.ground_entities("What is our GMV in São Paulo?")
    matched_vals = [m[2] for m in matches]
    assert "SP" in matched_vals


def test_entity_grounder_payment_types():
    grounder = CategoricalEntityGrounder()
    matches = grounder.ground_entities("GMV for credit card payments")
    matched_vals = [m[2] for m in matches]
    assert "credit_card" in matched_vals


def test_entity_grounder_multi_entity():
    grounder = CategoricalEntityGrounder()
    matches = grounder.ground_entities("GMV for credit card payments in Rio de Janeiro")
    matched_vals = [m[2] for m in matches]
    assert "credit_card" in matched_vals
    assert "RJ" in matched_vals


def test_entity_grounder_order_status():
    grounder = CategoricalEntityGrounder()
    matches = grounder.ground_entities("Show all delivered orders")
    matched_vals = [m[2] for m in matches]
    assert "delivered" in matched_vals


def test_entity_grounder_boleto_minas():
    grounder = CategoricalEntityGrounder()
    matches = grounder.ground_entities("boleto payments in Minas Gerais")
    matched_vals = [m[2] for m in matches]
    assert "boleto" in matched_vals
    assert "MG" in matched_vals


def test_dialect_transpiler():
    sql = "SELECT order_id, order_status FROM orders LIMIT 10;"
    pg_sql = DialectTranspiler.transpile(sql, target_dialect="postgres")
    assert "SELECT" in pg_sql

    sf_sql = DialectTranspiler.transpile(sql, target_dialect="snowflake")
    assert "SELECT" in sf_sql

    bq_sql = DialectTranspiler.transpile(sql, target_dialect="bigquery")
    assert "SELECT" in bq_sql


def test_canvas_agent_vega_lite(duckdb_connector):
    res = duckdb_connector.execute_query(
        "SELECT customer_state, COUNT(*) as order_count "
        "FROM customers GROUP BY customer_state ORDER BY order_count DESC LIMIT 5;"
    )
    state = AgenticBIState(
        question="What is the order count by state?",
        execution_result=res,
        metric_name="total_orders",
    )
    canvas = VisualCanvasAgent()
    synthesized = canvas.synthesize(state)
    assert synthesized.chart_spec is not None
    assert synthesized.chart_spec["$schema"] == "https://vega.github.io/schema/vega-lite/v5.json"
    assert "Top Performer" in synthesized.summary_narrative


def test_attribution_engine_review_drivers():
    engine = MetricAttributionEngine()
    # Simulate query result table as returned by diagnostic SQL
    table = pa.table({
        "customer_state": ["RJ", "AM", "SP", "MG", "RS"],
        "total_orders": [5000, 200, 40000, 10000, 8000],
        "avg_review_score": [3.8, 3.5, 4.1, 4.0, 4.2],
        "total_gmv": [500000.0, 20000.0, 5000000.0, 1000000.0, 800000.0],
        "late_delivery_pct": [25.0, 40.0, 10.0, 15.0, 12.0],
    })
    result = engine.diagnose_review_score_drivers(table)
    assert "lowest_csat_state" in result
    assert result["lowest_csat_state"] == "AM"  # score 3.5 is lowest
    assert "highest_late_delivery_state" in result
    assert result["highest_late_delivery_state"] == "AM"  # 40% is highest
    assert "summary_narrative" in result
    assert len(result["summary_narrative"]) > 50
