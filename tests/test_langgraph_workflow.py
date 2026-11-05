"""Tests for LangGraph/Sarvam integration workflow.

Covers run_agentic_bi in legacy and langgraph modes with deterministic behavior
(LLM unavailable), AgenticBIOrchestrator compatibility, and mocked LLM paths
with structured outputs (no network calls).
"""

from __future__ import annotations

from typing import Any, Callable

import pytest

from src.agents.orchestrator import AgenticBIOrchestrator
from src.agents.state import UserIntent
from src.core.config import settings
from src.graph.workflow import run_agentic_bi
from src.llm.schemas import (
    IntentRouteOutput,
    NarrativeOutput,
    SQLGenerationOutput,
    SQLRepairOutput,
)


# ---------------------------------------------------------------------------
# Test helpers: deterministic mock "chat model" for LangChain structured output
# ---------------------------------------------------------------------------


class _FakeStructuredModel:
    """Mimics a LangChain runnable returned by with_structured_output()."""

    def __init__(self, output: Any):
        self._output = output

    def invoke(self, prompt: Any) -> Any:
        return self._output


class _FakeChatModel:
    """Mimics ChatOpenAI enough for node code: with_structured_output(...).invoke(...)."""

    def __init__(self, outputs: dict[type[Any], Any] | None = None):
        self._outputs = outputs or {}

    def with_structured_output(self, schema: type[Any]) -> _FakeStructuredModel:
        if schema not in self._outputs:
            raise AssertionError(
                f"Unexpected structured output schema in mock LLM: {schema!r}. "
                f"Configured: {list(self._outputs.keys())!r}"
            )
        out = self._outputs[schema]
        if callable(out) and not isinstance(out, type):
            out = out(schema)
        return _FakeStructuredModel(out)


def _disable_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no real LLM credentials are visible (hermetic determinism)."""
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    monkeypatch.delenv("AGENTIC_BI_LLM_API_KEY", raising=False)
    monkeypatch.delenv("AGENTIC_BI_SARVAM_API_KEY", raising=False)
    monkeypatch.setattr(settings, "llm_api_key", None, raising=False)
    monkeypatch.setattr(settings, "sarvam_api_key", None, raising=False)


def _assert_security_passed(state) -> None:
    assert state.security_passed is True, (
        f"Expected security_passed=True, got {state.security_passed!r}; "
        f"security_error={state.security_error!r}; execution_error={state.execution_error!r}"
    )
    assert state.validated_sql, "Expected validated_sql to be populated"
    # AST validator clamps LIMIT; guardrail evidence in final SQL
    assert "LIMIT" in state.validated_sql.upper()


# ---------------------------------------------------------------------------
# run_agentic_bi: legacy vs langgraph, deterministic (LLM unavailable)
# ---------------------------------------------------------------------------


def test_run_agentic_bi_legacy_clarification_deterministic(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "engine", "legacy")
    _disable_llm_env(monkeypatch)
    state = run_agentic_bi("Show revenue", session_id="t-legacy-clarify")
    assert state.intent == UserIntent.CLARIFICATION_REQUIRED
    assert state.clarification_prompt
    assert len(state.clarification_options) >= 2
    joined = state.clarification_prompt + " " + " ".join(state.clarification_options)
    assert "GMV" in joined


def test_run_agentic_bi_legacy_gmv_success_security(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "engine", "legacy")
    _disable_llm_env(monkeypatch)
    state = run_agentic_bi("What is our GMV by customer state?", session_id="t-legacy-gmv")
    assert state.intent == UserIntent.CERTIFIED_METRIC
    assert state.metric_name == "gmv"
    assert state.execution_error is None
    assert state.execution_result is not None
    assert len(state.execution_result.data) > 0
    _assert_security_passed(state)


def test_run_agentic_bi_langgraph_deterministic_clarification_no_llm(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "engine", "langgraph")
    _disable_llm_env(monkeypatch)
    # Explicitly force deterministic fallback in nodes even if environment changes
    monkeypatch.setattr("src.graph.nodes.llm_enabled", lambda: False)
    state = run_agentic_bi("Show revenue", session_id="t-lg-clarify")
    assert state.intent == UserIntent.CLARIFICATION_REQUIRED
    assert state.clarification_prompt
    assert len(state.clarification_options) >= 2
    joined = state.clarification_prompt + " " + " ".join(state.clarification_options)
    assert "GMV" in joined


def test_run_agentic_bi_langgraph_gmv_success_security_no_llm(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "engine", "langgraph")
    _disable_llm_env(monkeypatch)
    monkeypatch.setattr("src.graph.nodes.llm_enabled", lambda: False)
    state = run_agentic_bi("What is our GMV by customer state?", session_id="t-lg-gmv")
    assert state.intent == UserIntent.CERTIFIED_METRIC
    assert state.metric_name == "gmv"
    assert state.execution_error is None
    assert state.execution_result is not None
    rows = state.execution_result.to_pylist()
    assert len(rows) > 0
    # GMV metric query groups by customer_state -> expect state column and metric value
    cols = set(state.execution_result.column_names)
    assert "customer_state" in cols
    assert "gmv" in cols
    _assert_security_passed(state)


# ---------------------------------------------------------------------------
# Orchestrator compatibility
# ---------------------------------------------------------------------------


def test_orchestrator_process_query_still_works(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "engine", "legacy")
    _disable_llm_env(monkeypatch)
    orch = AgenticBIOrchestrator()
    # Use a deterministic, semantically resolvable GMV query (certified metric path).
    state = orch.process_query("What is our GMV by customer state?", session_id="t-orch")
    assert state.question == "What is our GMV by customer state?"
    assert state.session_id == "t-orch"
    assert state.intent == UserIntent.CERTIFIED_METRIC
    assert state.metric_name == "gmv"
    assert state.execution_result is not None
    assert state.execution_error is None
    _assert_security_passed(state)


# ---------------------------------------------------------------------------
# Mocked LLM path (structured outputs, no network)
# ---------------------------------------------------------------------------


def _install_mock_llm(
    monkeypatch: pytest.MonkeyPatch, outputs: dict[type[Any], Any]
) -> _FakeChatModel:
    """Patch graph nodes to use a fake model returning deterministic Pydantic outputs."""
    fake = _FakeChatModel(outputs)
    monkeypatch.setattr("src.graph.nodes.llm_enabled", lambda: True)
    monkeypatch.setattr("src.graph.nodes.get_chat_model", lambda task=None: fake)
    return fake


def test_langgraph_mock_llm_routes_clarification(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "engine", "langgraph")
    _disable_llm_env(monkeypatch)
    _install_mock_llm(
        monkeypatch,
        {
            IntentRouteOutput: IntentRouteOutput(
                intent=UserIntent.CLARIFICATION_REQUIRED,
                confidence=0.51,
                clarification_prompt="Revenue is ambiguous for Olist. Choose a definition.",
                clarification_options=[
                    "GMV (Gross Merchandise Value): item sales excluding freight",
                    "Total Payment Value: payments received including freight/installments",
                ],
                rationale="Ambiguous revenue request",
            ),
        },
    )
    state = run_agentic_bi("Show revenue", session_id="t-mock-clarify")
    assert state.intent == UserIntent.CLARIFICATION_REQUIRED
    assert state.clarification_prompt == "Revenue is ambiguous for Olist. Choose a definition."
    assert len(state.clarification_options) == 2
    # Graph should end at clarification - no SQL execution
    assert state.execution_result is None
    assert state.raw_sql == ""


def test_langgraph_mock_llm_routes_gmv_certified_success(monkeypatch: pytest.MonkeyPatch):
    """LLM router selects certified GMV; SQL is compiled deterministically (secure)."""
    monkeypatch.setattr(settings, "engine", "langgraph")
    _disable_llm_env(monkeypatch)
    _install_mock_llm(
        monkeypatch,
        {
            IntentRouteOutput: IntentRouteOutput(
                intent=UserIntent.CERTIFIED_METRIC,
                confidence=0.99,
                metric_name="gmv",
                dimensions=["customer_state"],
                rationale="Matched certified GMV metric",
            ),
            # Narrative is optional; provide a deterministic refinement if canvas calls it
            NarrativeOutput: NarrativeOutput(
                summary_narrative="GMV by customer state computed from certified semantic definition."
            ),
        },
    )
    state = run_agentic_bi("What is our GMV by customer state?", session_id="t-mock-gmv")
    assert state.intent == UserIntent.CERTIFIED_METRIC
    assert state.metric_name == "gmv"
    assert state.execution_error is None
    assert state.execution_result is not None
    assert len(state.execution_result.data) > 0
    _assert_security_passed(state)
    # Narrative may come from VisualCanvasAgent or mocked LLM refinement
    assert state.summary_narrative


def test_langgraph_mock_llm_exploratory_sql_routes_and_executes(
    monkeypatch: pytest.MonkeyPatch,
):
    """Mock router + SQL generation (SQLGenerationOutput) -> validated/executed safely."""
    monkeypatch.setattr(settings, "engine", "langgraph")
    _disable_llm_env(monkeypatch)
    safe_sql = (
        "SELECT c.customer_state, COUNT(DISTINCT o.order_id) AS order_count "
        "FROM orders o JOIN customers c ON o.customer_id = c.customer_id "
        "WHERE o.order_status = 'delivered' "
        "GROUP BY c.customer_state ORDER BY order_count DESC LIMIT 5"
    )
    _install_mock_llm(
        monkeypatch,
        {
            IntentRouteOutput: IntentRouteOutput(
                intent=UserIntent.EXPLORATORY_SQL,
                confidence=0.9,
                rationale="Exploratory aggregation",
            ),
            SQLGenerationOutput: SQLGenerationOutput(
                sql=safe_sql,
                rationale="CTE-free simple join; whitelisted tables only.",
            ),
            NarrativeOutput: NarrativeOutput(
                summary_narrative="Delivered orders grouped by customer state (mock narrative)."
            ),
        },
    )
    state = run_agentic_bi(
        "How many delivered orders per state (top 5)?", session_id="t-mock-explore"
    )
    assert state.intent == UserIntent.EXPLORATORY_SQL
    assert state.execution_error is None
    assert state.execution_result is not None
    rows = state.execution_result.to_pylist()
    assert 0 < len(rows) <= 5
    assert "customer_state" in state.execution_result.column_names
    assert "order_count" in state.execution_result.column_names
    _assert_security_passed(state)
    assert state.summary_narrative


def test_langgraph_mock_llm_repair_output_used_on_failure(monkeypatch: pytest.MonkeyPatch):
    """When execution fails and LLM enabled, repair model output is applied (mocked)."""
    monkeypatch.setattr(settings, "engine", "langgraph")
    _disable_llm_env(monkeypatch)
    # Use a broken SQL that references a non-existent column, then repair to valid SQL.
    broken_sql = "SELECT c.customer_state, SUM(o.not_a_real_column) AS x FROM orders o JOIN customers c ON o.customer_id = c.customer_id GROUP BY c.customer_state LIMIT 5"
    fixed_sql = (
        "SELECT c.customer_state, COUNT(DISTINCT o.order_id) AS x "
        "FROM orders o JOIN customers c ON o.customer_id = c.customer_id "
        "GROUP BY c.customer_state LIMIT 5"
    )
    _install_mock_llm(
        monkeypatch,
        {
            IntentRouteOutput: IntentRouteOutput(
                intent=UserIntent.EXPLORATORY_SQL,
                confidence=0.9,
                rationale="Exploratory",
            ),
            SQLGenerationOutput: SQLGenerationOutput(sql=broken_sql, rationale="initial (broken)"),
            SQLRepairOutput: SQLRepairOutput(
                sql=fixed_sql, rationale="Replaced invalid column with count"
            ),
            NarrativeOutput: NarrativeOutput(summary_narrative="Repaired query executed."),
        },
    )
    state = run_agentic_bi("broken then repaired", session_id="t-mock-repair")
    assert state.intent == UserIntent.EXPLORATORY_SQL
    # Should heal via mocked repair and succeed
    assert state.execution_error is None, (
        f"Expected repair to fix query; error={state.execution_error!r} "
        f"history={state.error_history!r}"
    )
    assert state.execution_result is not None
    # LLM repair path: first attempt fails (recorded) then repaired SQL succeeds.
    assert state.retry_count >= 1
    assert state.error_history and any("Attempt 1" in h for h in state.error_history)
    _assert_security_passed(state)
