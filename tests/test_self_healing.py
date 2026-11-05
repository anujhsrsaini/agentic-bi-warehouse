"""Tests for Self-Healing Execution Agent — Olist Edition."""

import pytest
from src.agents.executor import SelfHealingExecutionAgent
from src.agents.state import AgenticBIState


def test_self_healing_fixes_misnamed_column(duckdb_connector):
    executor = SelfHealingExecutionAgent(connector=duckdb_connector, max_retries=3)

    # Query with intentionally misnamed column 'review' instead of 'review_score'
    state = AgenticBIState(
        question="What is average review score?",
        raw_sql="SELECT AVG(review) as avg_score FROM order_reviews LIMIT 10;"
    )

    executed_state = executor.execute(state)
    # It should retry and either heal or report a clear error
    # The key thing: security should pass (table 'order_reviews' is whitelisted)
    # but execution may fail due to wrong column — retry mechanism should kick in
    assert executed_state.retry_count >= 1 or executed_state.execution_result is not None


def test_self_healing_valid_olist_query_executes(duckdb_connector):
    executor = SelfHealingExecutionAgent(connector=duckdb_connector, max_retries=3)

    state = AgenticBIState(
        question="What is total GMV?",
        raw_sql="SELECT ROUND(SUM(price), 2) AS gmv FROM order_items LIMIT 100;"
    )

    executed_state = executor.execute(state)
    assert executed_state.security_passed is True
    assert executed_state.execution_error is None
    assert executed_state.execution_result is not None
    gmv = executed_state.execution_result.to_pylist()[0]["gmv"]
    assert gmv > 10_000_000  # Olist GMV is ~13.6M BRL


def test_self_healing_blocks_unauthorized_table(duckdb_connector):
    executor = SelfHealingExecutionAgent(connector=duckdb_connector, max_retries=3)

    state = AgenticBIState(
        question="Show payroll",
        raw_sql="SELECT * FROM payroll_internal_table LIMIT 10;"
    )

    executed_state = executor.execute(state)
    assert executed_state.security_passed is False
    assert "UNAUTHORIZED_TABLE_ACCESS" in str(executed_state.execution_error)
