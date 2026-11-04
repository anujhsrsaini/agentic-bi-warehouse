"""Tests for Self-Healing Execution Agent."""

import pytest
from src.agents.executor import SelfHealingExecutionAgent
from src.agents.state import AgenticBIState


def test_self_healing_fixes_misnamed_column(duckdb_connector):
    executor = SelfHealingExecutionAgent(connector=duckdb_connector, max_retries=3)
    
    # Query with intentionally misnamed column 'mrr' instead of 'mrr_amount_usd'
    state = AgenticBIState(
        question="What is total mrr?",
        raw_sql="SELECT SUM(mrr) as total FROM fct_subscriptions WHERE status = 'active';"
    )
    
    executed_state = executor.execute(state)
    assert executed_state.security_passed is True
    assert executed_state.execution_error is None
    assert executed_state.execution_result is not None
    assert executed_state.retry_count >= 1
    assert len(executed_state.error_history) == 1
    assert "mrr_amount_usd" in executed_state.validated_sql
