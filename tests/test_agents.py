"""Unit tests for Multi-Agent Brain components."""

import pytest
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


def test_intent_router_diagnostic():
    router = IntentRouterAgent()
    state = AgenticBIState(question="Why did churn increase in Q3?")
    routed = router.route(state)
    assert routed.intent == UserIntent.DIAGNOSTIC_WHY


def test_entity_grounder_synonyms():
    grounder = CategoricalEntityGrounder()
    matches = grounder.ground_entities("What is ARR for Enterprise in US?")
    matched_vals = [m[2] for m in matches]
    assert "Enterprise" in matched_vals
    assert "USA" in matched_vals


def test_dialect_transpiler():
    sql = "SELECT customer_id, company_name FROM dim_customers LIMIT 10;"
    pg_sql = DialectTranspiler.transpile(sql, target_dialect="postgres")
    assert "SELECT" in pg_sql

    sf_sql = DialectTranspiler.transpile(sql, target_dialect="snowflake")
    assert "SELECT" in sf_sql

    bq_sql = DialectTranspiler.transpile(sql, target_dialect="bigquery")
    assert "SELECT" in bq_sql


def test_canvas_agent_vega_lite(duckdb_connector):
    res = duckdb_connector.execute_query("SELECT industry, COUNT(*) as cnt FROM dim_customers GROUP BY industry LIMIT 5;")
    state = AgenticBIState(
        question="What is customer count by industry?",
        execution_result=res,
        metric_name="customer_count",
    )
    canvas = VisualCanvasAgent()
    synthesized = canvas.synthesize(state)
    assert synthesized.chart_spec is not None
    assert synthesized.chart_spec["$schema"] == "https://vega.github.io/schema/vega-lite/v5.json"
    assert "Top Performer" in synthesized.summary_narrative
