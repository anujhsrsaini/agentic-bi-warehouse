"""Graph state adapters bridging AgenticBIState <-> LangGraph state."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, TypedDict

from src.agents.state import AgenticBIState, UserIntent
from src.engine.connectors.base import QueryResult


class GraphState(TypedDict, total=False):
    question: str
    session_id: str
    intent: str
    confidence: float
    clarification_options: list[str]
    clarification_prompt: str | None
    metric_name: str | None
    dimensions: list[str]
    filters: list[str]
    grounded_entities: dict[str, Any]
    raw_sql: str
    sql_rationale: str
    validated_sql: str
    validation_time_us: float
    security_passed: bool
    security_error: str | None
    execution_result: Any  # QueryResult (not serializable checkpoint-safe; in-memory ok)
    execution_error: str | None
    retry_count: int
    error_history: list[str]
    summary_narrative: str
    lineage_mermaid: str
    lineage_ascii: str
    chart_spec: dict[str, Any] | None
    diagnostic_attribution: dict[str, Any] | None
    _next: str | None


def state_to_graph(state: AgenticBIState) -> GraphState:
    d = asdict(state)
    intent = d.get("intent")
    d["intent"] = intent.value if isinstance(intent, UserIntent) else str(intent)
    # Preserve non-JSON-serializable runtime objects (PyArrow-backed QueryResult).
    # dataclasses.asdict deep-copies and can turn QueryResult into a plain dict,
    # which breaks downstream nodes expecting attribute access (e.g. .data).
    d["execution_result"] = state.execution_result
    return d  # type: ignore[return-value]


def graph_to_state(g: GraphState) -> AgenticBIState:
    intent = g.get("intent", UserIntent.CERTIFIED_METRIC)
    if not isinstance(intent, UserIntent):
        try:
            intent = UserIntent(str(intent))
        except Exception:
            intent = UserIntent.CERTIFIED_METRIC
    return AgenticBIState(
        question=g.get("question", ""),
        session_id=g.get("session_id", "default-session"),
        intent=intent,
        confidence=float(g.get("confidence", 1.0) or 1.0),
        clarification_options=list(g.get("clarification_options") or []),
        clarification_prompt=g.get("clarification_prompt"),
        metric_name=g.get("metric_name"),
        dimensions=list(g.get("dimensions") or []),
        filters=list(g.get("filters") or []),
        grounded_entities=dict(g.get("grounded_entities") or {}),
        raw_sql=g.get("raw_sql", "") or "",
        sql_rationale=g.get("sql_rationale", "") or "",
        validated_sql=g.get("validated_sql", "") or "",
        validation_time_us=float(g.get("validation_time_us", 0.0) or 0.0),
        security_passed=bool(g.get("security_passed", False)),
        security_error=g.get("security_error"),
        execution_result=g.get("execution_result"),
        execution_error=g.get("execution_error"),
        retry_count=int(g.get("retry_count", 0) or 0),
        error_history=list(g.get("error_history") or []),
        summary_narrative=g.get("summary_narrative", "") or "",
        lineage_mermaid=g.get("lineage_mermaid", "") or "",
        lineage_ascii=g.get("lineage_ascii", "") or "",
        chart_spec=g.get("chart_spec"),
        diagnostic_attribution=g.get("diagnostic_attribution"),
    )
