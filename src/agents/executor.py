"""Self-Healing Execution Agent.

Executes queries via UWAL connector and implements an automated
Reflexion repair loop (up to 3 retries) when execution errors occur.
"""

from __future__ import annotations

import re
from src.agents.state import AgenticBIState
from src.core.exceptions import QueryExecutionError
from src.engine.connectors.base import BaseWarehouseConnector
from src.engine.session import WarehouseSession
from src.security.ast_validator import ASTSecurityValidator


class SelfHealingExecutionAgent:
    """Executes queries with automated Reflexion self-healing feedback."""

    def __init__(self, connector: BaseWarehouseConnector | None = None, max_retries: int = 3):
        self.session = WarehouseSession(connector=connector)
        self.validator = ASTSecurityValidator()
        self.max_retries = max_retries

    def execute(self, state: AgenticBIState) -> AgenticBIState:
        """Execute state.validated_sql with automated self-healing."""
        conn = self.session.get_connector()

        for attempt in range(1, self.max_retries + 1):
            try:
                # 1. AST Validation & Security Check
                sanitized_sql, val_time = self.validator.validate_and_sanitize(
                    state.validated_sql or state.raw_sql, dialect=conn.get_dialect()
                )
                state.validated_sql = sanitized_sql
                state.validation_time_us = val_time
                state.security_passed = True

                # 2. Query Execution
                res = conn.execute_query(state.validated_sql)
                state.execution_result = res
                state.execution_error = None
                return state

            except Exception as e:
                err_msg = str(e)
                state.retry_count = attempt
                state.error_history.append(f"Attempt {attempt} Error: {err_msg}")

                if attempt == self.max_retries:
                    state.execution_error = err_msg
                    return state

                # 3. Reflexion Self-Healing Repair
                repaired_sql = self._repair_sql(state.validated_sql or state.raw_sql, err_msg)
                if repaired_sql == state.validated_sql:
                    # Could not determine automatic fix
                    state.execution_error = err_msg
                    return state
                state.validated_sql = repaired_sql

        return state

    def _repair_sql(self, sql: str, error_msg: str) -> str:
        """Self-healing heuristics to fix common SQL errors."""
        repaired = sql

        # Fix 1: Unknown column reference / typo
        col_match = re.search(r'column ["\']?(\w+)["\']? not found', error_msg, re.IGNORECASE)
        if col_match:
            missing_col = col_match.group(1).lower()
            # Common column name replacements for Olist E-Commerce schema
            replacements = {
                "review": "review_score",
                "score": "review_score",
                "rating": "review_score",
                "freight": "freight_value",
                "shipping": "freight_value",
                "category": "product_category_name",
                "state": "customer_state",
                "city": "customer_city",
                "payment": "payment_value",
                "value": "payment_value",
                "status": "order_status",
            }
            if missing_col in replacements:
                repaired = re.sub(rf'\b{missing_col}\b', replacements[missing_col], repaired, flags=re.IGNORECASE)

        # Fix 2: Group By missing non-aggregate column
        if "must appear in the GROUP BY clause" in error_msg or "not in GROUP BY" in error_msg:
            # Check for SELECT columns that should be in GROUP BY
            pass

        return repaired
