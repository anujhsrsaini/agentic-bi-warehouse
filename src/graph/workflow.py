"""LangGraph StateGraph workflow assembly."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agents.state import AgenticBIState, UserIntent
from src.core.config import settings
from src.graph.nodes import (
    attribution_node,
    canvas_node,
    generate_sql_node,
    ground_node,
    lineage_node,
    route_node,
    validate_execute_repair_node,
)
from src.graph.state import GraphState, graph_to_state, state_to_graph


def _after_route(g: GraphState) -> str:
    intent = g.get("intent")
    if str(intent) == UserIntent.CLARIFICATION_REQUIRED.value or intent == UserIntent.CLARIFICATION_REQUIRED:
        return "end"
    return "ground"


def _after_exec(g: GraphState) -> str:
    if g.get("execution_error") or not g.get("execution_result"):
        return "end"
    intent = g.get("intent")
    if str(intent) == UserIntent.DIAGNOSTIC_WHY.value or intent == UserIntent.DIAGNOSTIC_WHY:
        return "attribution"
    return "canvas"


_COMPILED = None


def build_graph():
    global _COMPILED
    if _COMPILED is not None:
        return _COMPILED
    sg = StateGraph(GraphState)
    sg.add_node("route", route_node)
    sg.add_node("ground", ground_node)
    sg.add_node("generate_sql", generate_sql_node)
    sg.add_node("validate_execute_repair", validate_execute_repair_node)
    sg.add_node("lineage", lineage_node)
    sg.add_node("attribution", attribution_node)
    sg.add_node("canvas", canvas_node)

    sg.set_entry_point("route")
    sg.add_conditional_edges("route", _after_route, {"ground": "ground", "end": END})
    sg.add_edge("ground", "generate_sql")
    sg.add_edge("generate_sql", "validate_execute_repair")
    sg.add_edge("validate_execute_repair", "lineage")
    sg.add_conditional_edges("lineage", _after_exec, {"attribution": "attribution", "canvas": "canvas", "end": END})
    sg.add_edge("attribution", "canvas")
    sg.add_edge("canvas", END)
    _COMPILED = sg.compile()
    return _COMPILED


def run_agentic_bi(question: str, session_id: str = "default-session") -> AgenticBIState:
    if settings.engine.lower() == "legacy":
        # Local import to avoid cycles; legacy behavior preserved.
        from src.agents.router import IntentRouterAgent
        from src.agents.sql_generator import SQLGeneratorAgent
        from src.agents.executor import SelfHealingExecutionAgent
        from src.agents.attribution import MetricAttributionEngine
        from src.agents.canvas import VisualCanvasAgent
        from src.engine.lineage import ColumnLineageTracer

        state = AgenticBIState(question=question, session_id=session_id)
        state = IntentRouterAgent().route(state)
        if state.intent == UserIntent.CLARIFICATION_REQUIRED:
            return state
        state = SQLGeneratorAgent().generate(state)
        state = SelfHealingExecutionAgent().execute(state)
        if state.execution_error or not state.execution_result:
            return state
        if state.execution_result.column_names:
            target_metric = state.metric_name or state.execution_result.column_names[-1]
            try:
                tracer = ColumnLineageTracer()
                state.lineage_mermaid = tracer.to_mermaid(target_metric, state.validated_sql)
                state.lineage_ascii = tracer.to_ascii_tree(target_metric, state.validated_sql)
            except Exception:
                pass
        if state.intent == UserIntent.DIAGNOSTIC_WHY:
            diag = MetricAttributionEngine().diagnose_churn_drivers(state.execution_result.data)
            state.diagnostic_attribution = diag
            state.summary_narrative = diag.get("summary_narrative", "")
        if not state.summary_narrative:
            state = VisualCanvasAgent().synthesize(state)
        return state

    graph = build_graph()
    init = state_to_graph(AgenticBIState(question=question, session_id=session_id))
    out = graph.invoke(init)
    return graph_to_state(out)
