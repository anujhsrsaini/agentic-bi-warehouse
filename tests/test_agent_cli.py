"""Check that common help questions remain readable and need no LLM call."""

from unittest.mock import Mock

import pyarrow as pa

from src import agent_cli
from src.agents.state import AgenticBIState
from src.engine.connectors.base import QueryResult
from src.core.config import settings
from src.core.exceptions import SecurityViolationError
from src.security.ast_validator import ASTSecurityValidator
import pytest


def test_capability_question_shows_real_examples_without_query(monkeypatch, capsys):
    agent = Mock()
    monkeypatch.setattr(settings, "customer_identifier_protection", False)
    monkeypatch.setattr(agent_cli, "llm_enabled", lambda: True)
    monkeypatch.setattr(agent_cli, "AgenticBIOrchestrator", lambda: agent)
    answers = iter(["What all questions can be answered by you?", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert agent_cli.main() == 0
    output = capsys.readouterr().out
    assert "What is GMV by customer state?" in output
    assert "2016" in output
    assert "Customer-ID protection: OFF" in output
    assert "SQL used:" not in output
    agent.process_query.assert_not_called()


def test_sql_available_on_request(monkeypatch, capsys):
    result = QueryResult(data=pa.table({"gmv": [12.5]}), execution_time_ms=1, rows_scanned=1, rows_returned=1)
    state = AgenticBIState(question="sales", execution_result=result, validated_sql="SELECT 12.5 AS gmv")
    agent = Mock()
    agent.process_query.return_value = state
    monkeypatch.setattr(agent_cli, "llm_enabled", lambda: True)
    monkeypatch.setattr(agent_cli, "AgenticBIOrchestrator", lambda: agent)
    answers = iter(["sales", "/sql", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert agent_cli.main() == 0
    output = capsys.readouterr().out
    assert "12.50" in output
    assert "SELECT 12.5 AS gmv" in output


def test_privacy_command_controls_customer_id_only(monkeypatch, capsys):
    monkeypatch.setattr(settings, "customer_identifier_protection", True)
    monkeypatch.setattr(agent_cli, "llm_enabled", lambda: True)
    monkeypatch.setattr(agent_cli, "AgenticBIOrchestrator", lambda: Mock())
    validator = ASTSecurityValidator()
    with pytest.raises(SecurityViolationError):
        validator.validate_and_sanitize("SELECT customer_unique_id FROM customers")
    answers = iter(["/privacy off", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert agent_cli.main() == 0
    assert "Customer-ID protection: OFF" in capsys.readouterr().out
    validator.validate_and_sanitize("SELECT customer_unique_id FROM customers")
    with pytest.raises(SecurityViolationError):
        validator.validate_and_sanitize("DROP TABLE customers")
    with pytest.raises(SecurityViolationError):
        validator.validate_and_sanitize("SELECT password FROM customers")
    answers = iter(["/privacy on", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    agent_cli.main()
    with pytest.raises(SecurityViolationError):
        validator.validate_and_sanitize("SELECT customer_unique_id FROM customers")


def test_repeat_analysis_without_stable_identifier_is_rejected(monkeypatch):
    from src.agents.orchestrator import AgenticBIOrchestrator
    from src.graph import workflow
    result = QueryResult(data=pa.table({"repeat_pct": [0]}), execution_time_ms=1, rows_scanned=1, rows_returned=1)
    state = AgenticBIState(question="repeat customers", execution_result=result,
                           validated_sql="SELECT customer_id, 0 AS repeat_pct FROM orders")
    monkeypatch.setattr(workflow, "run_agentic_bi", lambda *args, **kwargs: state)
    output = AgenticBIOrchestrator().process_query("new versus repeat customers")
    assert output.execution_result is None
    assert "stable customer identifier" in output.execution_error
