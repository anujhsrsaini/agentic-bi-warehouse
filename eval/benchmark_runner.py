"""Run the project's small Olist evaluation suite (not the Spider benchmark).

Result comparisons, SQL-shape checks, clarification checks and attack checks are
reported separately: a SQL substring match is not evidence of result accuracy.
"""
from __future__ import annotations

import argparse
import platform
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml
from rich.console import Console
from rich.table import Table

from eval.comparator import ResultComparator
from src.agents.orchestrator import AgenticBIOrchestrator
from src.core.config import settings
from src.core.exceptions import SecurityViolationError
from src.engine.session import WarehouseSession
from src.security.ast_validator import ASTSecurityValidator

console = Console()


def grade_case(tc, orchestrator, conn, comparator, validator):
    """Return an independently classified case result, including a failure reason."""
    result = {"id": tc["id"], "passed": False, "category": "unknown", "reason": ""}
    if tc.get("tier") == "adversarial":
        result["category"] = "Security rejection"
        try:
            validator.validate_and_sanitize(tc["payload"])
        except SecurityViolationError as exc:
            expected = tc["expected_violation"]
            result.update(passed=expected in str(exc), reason=f"Rejected: {exc}")
        else:
            result["reason"] = "Payload was not rejected"
        return result

    state = orchestrator.process_query(tc["question"])
    if "expected_clarification_contains" in tc:
        result["category"] = "Clarification"
        prompt = state.clarification_prompt or ""
        intent = getattr(state.intent, "value", state.intent)
        passed = (intent == tc.get("expected_intent") and
                  tc["expected_clarification_contains"].casefold() in prompt.casefold())
        result.update(passed=passed, reason=f"Intent: {intent}; prompt: {prompt or '(none)'}")
        return result

    if "expected_sql" in tc:
        result["category"] = "Result comparison"
    elif "expected_sql_contains" in tc:
        result["category"] = "SQL shape only"
    else:
        result["reason"] = "No supported explicit expectation specified"
        return result

    if state.execution_error or state.execution_result is None:
        result["reason"] = str(state.execution_error or "No execution result")
        return result
    if "expected_sql" in tc:
        gold = conn.execute_query(tc["expected_sql"])
        passed = comparator.compare_tables(state.execution_result.data, gold.data)
        result.update(passed=passed, reason="Results match" if passed else "Result mismatch against gold query")
    else:
        sql = (state.validated_sql or "").casefold()
        missing = [part for part in tc["expected_sql_contains"] if part.casefold() not in sql]
        expected_intent = tc.get("intent")
        actual_intent = getattr(state.intent, "value", state.intent)
        intent_ok = expected_intent is None or actual_intent == expected_intent
        result.update(passed=not missing and intent_ok,
                      reason=f"Missing SQL fragments: {missing}; intent: {actual_intent}" if missing or not intent_ok
                      else "Required SQL fragments present (not a result correctness check)")
    return result


def _run_benchmark(dataset_path=None):
    dataset_path = Path(dataset_path or Path(__file__).with_name("golden_dataset.yaml"))
    with dataset_path.open(encoding="utf-8") as f:
        bench_data = yaml.safe_load(f)
    cases = bench_data.get("test_cases", [])
    if not cases:
        console.print("[red]No evaluation cases found.[/red]")
        return 1
    # Keep this project benchmark reproducible and independent of external LLM keys.
    settings.engine = "legacy"
    settings.warehouse_type = "duckdb"
    console.print(f"{bench_data.get('benchmark_name', 'Olist evaluation')} | {len(cases)} cases")
    console.print(f"Mode: legacy deterministic, DuckDB | Python {platform.python_version()} | Data: {settings.data_dir}")
    console.print("SQL shape checks do not establish answer correctness. No latency or accuracy claim is inferred from them.")

    orchestrator = AgenticBIOrchestrator()
    conn = WarehouseSession().get_connector()
    conn.connect()
    comparator = ResultComparator()
    validator = ASTSecurityValidator()
    results = []
    start = time.perf_counter()
    try:
        for tc in cases:
            try:
                result = grade_case(tc, orchestrator, conn, comparator, validator)
            except Exception as exc:
                result = {"id": tc.get("id", "unknown"), "category": "Error", "passed": False,
                          "reason": f"{type(exc).__name__}: {exc}"}
            results.append(result)
    finally:
        conn.disconnect()

    summary = Table(title="Project evaluation — case counts")
    summary.add_column("Category")
    summary.add_column("Passed / total")
    for category in sorted({r["category"] for r in results}):
        group = [r for r in results if r["category"] == category]
        summary.add_row(category, f"{sum(r['passed'] for r in group)} / {len(group)}")
    console.print(summary)
    details = Table(title="Case details")
    for heading in ("ID", "Category", "Status", "Details"):
        details.add_column(heading)
    for result in results:
        details.add_row(result["id"], result["category"], "PASS" if result["passed"] else "FAIL", result["reason"])
    console.print(details)
    console.print(f"Total: {sum(r['passed'] for r in results)} / {len(results)} passed in {time.perf_counter() - start:.2f}s")
    return 0 if all(r["passed"] for r in results) else 1


def run_benchmark(dataset_path=None):
    """Run the suite without permanently changing application settings."""
    old_engine, old_warehouse = settings.engine, settings.warehouse_type
    try:
        return _run_benchmark(dataset_path)
    finally:
        settings.engine, settings.warehouse_type = old_engine, old_warehouse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", help="Path to a YAML evaluation dataset")
    args = parser.parse_args()
    sys.exit(run_benchmark(args.dataset))
