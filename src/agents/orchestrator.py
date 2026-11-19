"""Master Cognitive Orchestrator for Governed Agentic BI.

Delegates to a LangGraph StateGraph workflow (Sarvam/LangChain-capable) while
preserving the legacy `process_query(question, session_id) -> AgenticBIState` contract.
Set `AGENTIC_BI_ENGINE=legacy` to force the original deterministic pipeline.
"""

from __future__ import annotations

import re
import time

from src.agents.state import AgenticBIState
from src.core.exceptions import SemanticResolutionError, SecurityViolationError
from src.engine.connectors.base import BaseWarehouseConnector
from src.security.ast_validator import ASTSecurityValidator
import sqlglot
from sqlglot import exp

# Statements that can never be valid analytical input: route straight to the firewall.
_SQL_MUTATION_RE = re.compile(
    r"^\s*(DROP|ALTER|TRUNCATE|DELETE|UPDATE|INSERT|CREATE|REPLACE|MERGE|GRANT|REVOKE|"
    r"COPY|INSTALL|LOAD|PRAGMA|ATTACH|DETACH|CALL|EXEC|EXECUTE)\b",
    re.IGNORECASE,
)
_SQL_SELECT_RE = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)
_SQL_STRUCTURE_RE = re.compile(
    r"\bFROM\b|\bWHERE\b|\bGROUP\s+BY\b|\bORDER\s+BY\b|\bJOIN\b|\bLIMIT\b|\*|;",
    re.IGNORECASE,
)


class AgenticBIOrchestrator:
    """End-to-End Multi-Agent Cognitive Workflow Coordinator."""

    def __init__(self, connector: BaseWarehouseConnector | None = None):
        # Kept for compatibility; graph nodes currently use the default WarehouseSession.
        # Future: thread connector through graph runtime/config.
        self.connector = connector
        self.security_validator = ASTSecurityValidator()

    def process_query(self, question: str, session_id: str = "default-session") -> AgenticBIState:
        """Run the governed analytical workflow for a natural language question."""
        from src.agents.product_cohorts import matches_product_cohort_question, run_product_cohort_analysis

        preflight = self._preflight_raw_sql(question, session_id)
        if preflight is not None:
            return preflight

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

    @staticmethod
    def _looks_like_raw_sql(text: str) -> bool:
        """Detect raw SQL input without misclassifying natural language like 'Select the top 10'."""
        if _SQL_MUTATION_RE.match(text):
            return True
        if _SQL_SELECT_RE.match(text):
            return bool(_SQL_STRUCTURE_RE.search(text))
        return False

    def _preflight_raw_sql(self, question: str, session_id: str) -> AgenticBIState | None:
        """Route raw SQL directly to the AST firewall before any natural-language parsing."""
        if not question or not self._looks_like_raw_sql(question):
            return None

        state = AgenticBIState(question=question, session_id=session_id)
        state.raw_sql = question.strip()
        state.sql_rationale = "Raw SQL input intercepted by the AST security preflight."

        t0 = time.perf_counter()
        try:
            sanitized_sql, validation_us = self.security_validator.validate_and_sanitize(question)
            state.validated_sql = sanitized_sql
            state.validation_time_us = validation_us or ((time.perf_counter() - t0) * 1_000_000)
            state.security_passed = True
            state.security_error = None

            # Execute validated read-only SQL directly.
            from src.engine.session import WarehouseSession

            conn = WarehouseSession().get_connector()
            state.execution_result = conn.execute_query(state.validated_sql)
            state.execution_error = None
            return state
        except SecurityViolationError as e:
            state.validation_time_us = (time.perf_counter() - t0) * 1_000_000
            state.security_passed = False
            state.security_error = str(e)
            state.execution_error = str(e)
            return state
        except Exception as e:  # parse errors / execution failures
            state.validation_time_us = (time.perf_counter() - t0) * 1_000_000
            state.security_passed = False
            state.security_error = f"Parse / Validation Error: {e}"
            state.execution_error = state.security_error
            return state
