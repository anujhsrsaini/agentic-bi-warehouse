"""Master Cognitive Orchestrator for Governed Agentic BI.

Delegates to a LangGraph StateGraph workflow (Sarvam/LangChain-capable) while
preserving the legacy `process_query(question, session_id) -> AgenticBIState` contract.
Set `AGENTIC_BI_ENGINE=legacy` to force the original deterministic pipeline.
"""

from __future__ import annotations

from src.agents.state import AgenticBIState
from src.core.exceptions import SemanticResolutionError
from src.engine.connectors.base import BaseWarehouseConnector
import sqlglot
from sqlglot import exp


class AgenticBIOrchestrator:
    """End-to-End Multi-Agent Cognitive Workflow Coordinator."""

    def __init__(self, connector: BaseWarehouseConnector | None = None):
        # Kept for compatibility; graph nodes currently use the default WarehouseSession.
        # Future: thread connector through graph runtime/config.
        self.connector = connector

    def process_query(self, question: str, session_id: str = "default-session") -> AgenticBIState:
        """Run the governed analytical workflow for a natural language question."""
        from src.agents.product_cohorts import matches_product_cohort_question, run_product_cohort_analysis
        from src.graph.workflow import run_agentic_bi

        try:
            if matches_product_cohort_question(question):
                return run_product_cohort_analysis(question, session_id)
            state = run_agentic_bi(question, session_id=session_id, connector=self.connector)
            text = question.casefold()
            if state.execution_result is not None and "customer" in text and "repeat" in text:
                try:
                    tree = sqlglot.parse_one(state.validated_sql, read="duckdb")
                    columns = {column.name.casefold() for column in tree.find_all(exp.Column)}
                except Exception:
                    columns = set()
                if "customer_unique_id" not in columns:
                    state.execution_result = None
                    state.summary_narrative = ""
                    state.execution_error = (
                        "The generated query did not use the stable customer identifier, "
                        "so its new-versus-repeat calculation cannot be trusted. "
                        "If customer-ID protection is on, use /privacy off; then try again."
                    )
                elif "product" in text and "categor" not in text and "product_id" not in columns:
                    state.execution_result = None
                    state.summary_narrative = ""
                    state.execution_error = "The generated query did not provide an individual product breakdown. Please try again."
            return state
        except SemanticResolutionError as exc:
            return AgenticBIState(
                question=question,
                session_id=session_id,
                execution_error=f"This metric and breakdown are not supported safely: {exc}",
            )

