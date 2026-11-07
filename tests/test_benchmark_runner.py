"""Tests for benchmark grading and its required failure gate."""
from types import SimpleNamespace

import pyarrow as pa

from eval import benchmark_runner as benchmark


class FakeOrchestrator:
    def __init__(self, state):
        self.state = state

    def process_query(self, question):
        return self.state


def test_sql_fragment_case_is_not_a_diagnostic_presence_check():
    state = SimpleNamespace(intent="CERTIFIED_METRIC", execution_error=None,
                            execution_result=object(), validated_sql="SELECT 1",
                            summary_narrative="Some narrative")
    case = {"id": "shape", "question": "test", "expected_sql_contains": ["GROUP BY"]}
    result = benchmark.grade_case(case, FakeOrchestrator(state), None, None, None)
    assert result["category"] == "SQL shape only"
    assert result["passed"] is False
    assert "GROUP BY" in result["reason"]


def test_clarification_is_graded_without_requiring_query_results():
    state = SimpleNamespace(intent="CLARIFICATION_REQUIRED", clarification_prompt="Do you mean GMV?")
    case = {"id": "clarify", "question": "revenue", "expected_intent": "CLARIFICATION_REQUIRED",
            "expected_clarification_contains": "GMV"}
    result = benchmark.grade_case(case, FakeOrchestrator(state), None, None, None)
    assert result["category"] == "Clarification"
    assert result["passed"] is True


def test_a_failed_required_case_returns_failure(tmp_path, monkeypatch):
    dataset = tmp_path / "case.yaml"
    dataset.write_text("test_cases:\n  - id: deliberate_failure\n    question: test\n", encoding="utf-8")
    connection = SimpleNamespace(connect=lambda: None, disconnect=lambda: None)
    monkeypatch.setattr(benchmark, "WarehouseSession", lambda: SimpleNamespace(get_connector=lambda: connection))
    monkeypatch.setattr(benchmark, "grade_case", lambda *args: {
        "id": "deliberate_failure", "category": "test", "passed": False, "reason": "deliberate"})
    assert benchmark.run_benchmark(dataset) == 1


def test_result_comparison_checks_columns_even_for_empty_results():
    candidate = pa.table({"a": []})
    gold = pa.table({"a": [], "b": []})
    assert not benchmark.ResultComparator().compare_tables(candidate, gold)
