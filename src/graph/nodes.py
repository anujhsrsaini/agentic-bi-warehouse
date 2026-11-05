"""LangGraph node implementations (deterministic + Sarvam LLM via LangChain)."""

from __future__ import annotations

from typing import Any

from src.agents.attribution import MetricAttributionEngine
from src.agents.canvas import VisualCanvasAgent
from src.agents.entity_grounder import CategoricalEntityGrounder
from src.agents.router import IntentRouterAgent
from src.agents.sql_generator import SQLGeneratorAgent
from src.agents.state import AgenticBIState, UserIntent
from src.core.config import settings
from src.engine.lineage import ColumnLineageTracer
from src.engine.session import WarehouseSession
from src.graph.state import GraphState, graph_to_state, state_to_graph
from src.llm.factory import get_chat_model, llm_enabled
from src.llm.prompts import narrative_prompt, repair_prompt, router_prompt, sql_prompt
from src.llm.schemas import IntentRouteOutput, NarrativeOutput, SQLGenerationOutput, SQLRepairOutput
from src.security.ast_validator import ASTSecurityValidator
from src.semantic.loader import SemanticLayerLoader
from src.semantic.resolver import SemanticQueryResolver


def _semantic_catalog() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    loader = SemanticLayerLoader()
    cfg = loader.load()
    metrics = [
        {
            "name": m.name,
            "label": m.label,
            "description": m.description,
            "dimensions": m.dimensions,
            "synonyms": m.synonyms,
            "model": m.model,
        }
        for m in cfg.metrics
    ]
    session = WarehouseSession()
    catalog = session.get_connector().introspect_schema()
    schema_dict = {}
    for tbl_name, tbl_meta in catalog.tables.items():
        schema_dict[tbl_name] = {
            "columns": list(tbl_meta.columns.keys()),
            "row_count": tbl_meta.row_count,
        }
    return metrics, schema_dict


def route_node(g: GraphState) -> GraphState:
    state = graph_to_state(g)
    if llm_enabled():
        try:
            metrics, _ = _semantic_catalog()
            model = get_chat_model("router").with_structured_output(IntentRouteOutput)
            out: IntentRouteOutput = model.invoke(router_prompt(state.question, metrics))
            state.intent = out.intent
            state.confidence = out.confidence
            state.metric_name = out.metric_name
            state.dimensions = out.dimensions or []
            state.clarification_prompt = out.clarification_prompt
            state.clarification_options = out.clarification_options or []
            return state_to_graph(state)
        except Exception:
            # Fall back to deterministic router for reliability.
            pass
    routed = IntentRouterAgent().route(state)
    return state_to_graph(routed)


def ground_node(g: GraphState) -> GraphState:
    state = graph_to_state(g)
    grounded = CategoricalEntityGrounder().ground_entities(state.question)
    state.grounded_entities = {f"{t}.{c}": v for t, c, v, _conf in grounded}
    # Append grounded filters (deterministic, safe)
    for tbl, col, val, _conf in grounded:
        clause = f"{tbl}.{col} = '{val}'"
        if clause not in state.filters:
            state.filters.append(clause)
    return state_to_graph(state)


def generate_sql_node(g: GraphState) -> GraphState:
    state = graph_to_state(g)
    # Certified metric path: ALWAYS deterministic from semantic layer (LLM may only select params).
    if state.intent == UserIntent.CERTIFIED_METRIC and state.metric_name:
        state.raw_sql = SemanticQueryResolver().resolve_metric_query(
            metric_name=state.metric_name,
            dimensions=state.dimensions,
            filters=state.filters,
            limit=100,
        )
        state.sql_rationale = f"Compiled certified metric [{state.metric_name}] from semantic_layer.yaml."
        return state_to_graph(state)

    if llm_enabled():
        try:
            metrics, schema = _semantic_catalog()
            model = get_chat_model("sql").with_structured_output(SQLGenerationOutput)
            out: SQLGenerationOutput = model.invoke(
                sql_prompt(
                    state.question,
                    metrics,
                    schema,
                    state.grounded_entities,
                    state.intent.value,
                    state.metric_name,
                    state.dimensions,
                )
            )
            if out.certified_metric:
                state.metric_name = out.certified_metric
                state.dimensions = out.dimensions or state.dimensions
                state.filters = (state.filters or []) + (out.filters or [])
                state.raw_sql = SemanticQueryResolver().resolve_metric_query(
                    metric_name=state.metric_name,
                    dimensions=state.dimensions,
                    filters=state.filters,
                    limit=100,
                )
                state.sql_rationale = out.rationale or f"Compiled certified metric [{state.metric_name}] from semantic_layer.yaml."
                return state_to_graph(state)
            if out.sql and "select" in out.sql.lower():
                state.raw_sql = out.sql.strip().rstrip(";") + ";"
                state.sql_rationale = out.rationale or "LLM-generated exploratory SQL (AST-validated before execution)."
                return state_to_graph(state)
        except Exception:
            pass

    # Deterministic fallback (legacy templates/heuristics)
    generated = SQLGeneratorAgent().generate(state)
    return state_to_graph(generated)


def validate_execute_repair_node(g: GraphState) -> GraphState:
    state = graph_to_state(g)
    validator = ASTSecurityValidator()
    session = WarehouseSession()
    conn = session.get_connector()
    max_retries = int(settings.llm_max_retries) + 1 if llm_enabled() else 3
    max_retries = max(1, min(max_retries, 5))
    sql = state.validated_sql or state.raw_sql
    state.error_history = list(state.error_history or [])

    for attempt in range(1, max_retries + 1):
        try:
            sanitized_sql, val_time = validator.validate_and_sanitize(sql, dialect=conn.get_dialect())
            state.validated_sql = sanitized_sql
            state.validation_time_us = val_time
            state.security_passed = True
            state.security_error = None
            res = conn.execute_query(state.validated_sql)
            state.execution_result = res
            state.execution_error = None
            return state_to_graph(state)
        except Exception as e:
            err = str(e)
            state.retry_count = attempt
            state.error_history.append(f"Attempt {attempt} Error: {err}")
            state.security_passed = False if "Security Violation" in err or "UNAUTHORIZED" in err or "FORBIDDEN" in err or "MUTATION" in err else state.security_passed
            if attempt >= max_retries:
                state.execution_error = err
                state.security_error = err if not state.security_passed else state.security_error
                return state_to_graph(state)
            # LLM repair (if available), else break
            if llm_enabled():
                try:
                    _metrics, schema = _semantic_catalog()
                    model = get_chat_model("repair").with_structured_output(SQLRepairOutput)
                    out: SQLRepairOutput = model.invoke(repair_prompt(sql, err, schema, attempt))
                    if out.sql and out.sql.strip() and out.sql.strip() != sql.strip():
                        sql = out.sql.strip().rstrip(";") + ";"
                        continue
                except Exception:
                    pass
            # No repair available: stop
            state.execution_error = err
            state.security_error = err if not state.security_passed else state.security_error
            return state_to_graph(state)
    return state_to_graph(state)


def lineage_node(g: GraphState) -> GraphState:
    state = graph_to_state(g)
    if state.execution_result and getattr(state.execution_result, "column_names", None):
        target_metric = state.metric_name or state.execution_result.column_names[-1]
        try:
            tracer = ColumnLineageTracer()
            sql = state.validated_sql or state.raw_sql
            state.lineage_mermaid = tracer.to_mermaid(target_metric, sql)
            state.lineage_ascii = tracer.to_ascii_tree(target_metric, sql)
        except Exception:
            pass
    return state_to_graph(state)


def attribution_node(g: GraphState) -> GraphState:
    state = graph_to_state(g)
    if state.intent == UserIntent.DIAGNOSTIC_WHY and state.execution_result:
        try:
            diag = MetricAttributionEngine().diagnose_churn_drivers(state.execution_result.data)
            state.diagnostic_attribution = diag
            state.summary_narrative = diag.get("summary_narrative", state.summary_narrative)
        except Exception:
            pass
    return state_to_graph(state)


def canvas_node(g: GraphState) -> GraphState:
    state = graph_to_state(g)
    if not state.summary_narrative:
        state = VisualCanvasAgent().synthesize(state)
    # Optional LLM narrative refinement (bounded)
    if llm_enabled() and state.execution_result and not state.execution_error:
        try:
            rows = state.execution_result.to_pylist() if hasattr(state.execution_result, "to_pylist") else []
            cols = list(getattr(state.execution_result, "column_names", []) or [])
            model = get_chat_model("narrative").with_structured_output(NarrativeOutput)
            out: NarrativeOutput = model.invoke(
                narrative_prompt(state.question, state.validated_sql or state.raw_sql, cols, rows, state.metric_name)
            )
            if out.summary_narrative:
                state.summary_narrative = out.summary_narrative
        except Exception:
            pass
    return state_to_graph(state)
