"""A small, repeatable offline tour of the Olist analytics project.

The tour deliberately accepts only known questions: its local examples do not
call an LLM or silently substitute a different answer for an unknown request.
"""
from __future__ import annotations

from pathlib import Path

import sqlglot
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table
from sqlglot import exp

from src.core.exceptions import SecurityViolationError
from src.engine.connectors.duckdb_connector import DuckDBConnector
from src.security.ast_validator import ASTSecurityValidator
from src.semantic.loader import SemanticLayerLoader
from src.semantic.resolver import SemanticQueryResolver

console = Console()

# Each example has one deliberately supported metric/dimension combination.
EXAMPLES = {
    "1": ("What is GMV by customer state?", "gmv", ["customer_state"]),
    "2": ("What is the late delivery rate by customer state?", "delivery_delay_rate", ["customer_state"]),
    "3": ("How many orders were delivered?", "total_orders", []),
    "4": ("What is average order value?", "aov", []),
    "5": ("What is the average review score?", "avg_review_score", []),
}


def _normalize(question: str) -> str:
    return " ".join(question.lower().strip().rstrip("?.!").split())


def _caveats(metric_name: str) -> list[str]:
    path = Path(__file__).resolve().parent.parent / "config" / "showcase_caveats.yaml"
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return list(data.get("all", [])) + list(data.get("metrics", {}).get(metric_name, []))


def _source_tables(sql: str) -> list[str]:
    """Get referenced physical table names from the SQL that was executed."""
    root = sqlglot.parse_one(sql, read="duckdb")
    ctes = {cte.alias.lower() for cte in root.find_all(exp.CTE)}
    return sorted({table.name for table in root.find_all(exp.Table) if table.name.lower() not in ctes})


def execute_and_render(question: str) -> None:
    normalized = _normalize(question)
    console.print(f"\n[bold]Question:[/bold] {question}")
    if normalized in {"revenue", "show revenue", "what is revenue", "what is our revenue"}:
        console.print(Panel("Revenue could mean item sales (GMV) or payments including freight. "
                            "Which definition do you want? Try the GMV example.", title="Clarification needed"))
        return
    example = next((item for item in EXAMPLES.values() if _normalize(item[0]) == normalized), None)
    if example is None:
        console.print("[yellow]This offline demo only recognizes the listed example questions. "
                      "Please choose one from the menu.[/yellow]")
        return

    _, metric_name, dimensions = example
    metric = SemanticLayerLoader().load().get_metric(metric_name)
    if metric is None:
        console.print(f"[red]Metric configuration not found: {metric_name}[/red]")
        return
    connector = DuckDBConnector(data_dir=Path(__file__).resolve().parent.parent / "data" / "seed")
    try:
        sql = SemanticQueryResolver().resolve_metric_query(metric_name, dimensions=dimensions)
        sql, _ = ASTSecurityValidator().validate_and_sanitize(sql, dialect="duckdb")
        result = connector.execute_query(sql)
    except Exception as exc:
        console.print(f"[red]Unable to run this example: {exc}[/red]")
        return
    finally:
        connector.disconnect()

    console.print(Panel("Defined metric | local DuckDB | historical Olist data", title="Answer context"))
    table = Table(title=metric.label)
    for column in result.column_names:
        table.add_column(column.replace("_", " ").title())
    rows = result.to_pylist()
    for row in rows[:15]:
        values = []
        for column in result.column_names:
            value = row[column]
            values.append(f"{value:,.2f}" if isinstance(value, float) else str(value))
        table.add_row(*values)
    console.print(table)
    if len(rows) > 15:
        console.print(f"Showing 15 of {len(rows)} rows.")
    console.print(f"[bold]Definition:[/bold] {metric.description}")
    console.print(f"[bold]Calculation:[/bold] {metric.calculation}")
    console.print(f"[bold]Filter:[/bold] {metric.filter or 'None'}")
    console.print(f"[bold]Sources in executed SQL:[/bold] {', '.join(_source_tables(sql)) or 'Unknown'}")
    for caveat in _caveats(metric_name):
        console.print(f"[yellow]Note:[/yellow] {caveat}")
    console.print(Panel(Syntax(sql, "sql", theme="monokai", word_wrap=True), title="Executed SQL"))


def run_adversarial_test() -> None:
    """Show a representative blocked query without attempting execution."""
    query = "DROP TABLE orders;"
    console.print(f"\nQuery submitted to validator: {query}")
    try:
        ASTSecurityValidator().validate_and_sanitize(query)
    except SecurityViolationError as exc:
        console.print(f"[green]Blocked before execution:[/green] {exc}")
    else:
        console.print("[red]The validator did not block this query.[/red]")


def main() -> None:
    console.print(Panel(
        "Ask a business question, see a metric and inspect its SQL.\n"
        "Offline guided mode: no LLM, API key or network connection is used.\n"
        "The sample is historical Olist e-commerce data, not current business data.",
        title="Analytics assistant: local showcase",
    ))
    while True:
        console.print("\n[bold]Choose an example[/bold]")
        for key, (question, _, _) in EXAMPLES.items():
            console.print(f"  [{key}] {question}")
        console.print("  [6] Show revenue (clarification example)")
        console.print("  [7] Try an unsafe query (guardrail example)")
        console.print("  [8] Type a supported example question")
        console.print("  [0] Exit")
        choice = Prompt.ask("Choose", default="1")
        if choice == "0":
            break
        if choice in EXAMPLES:
            execute_and_render(EXAMPLES[choice][0])
        elif choice == "6":
            execute_and_render("Show revenue")
        elif choice == "7":
            run_adversarial_test()
        elif choice == "8":
            execute_and_render(Prompt.ask("Question"))
        else:
            console.print("Please choose a number from the menu.")


if __name__ == "__main__":
    main()
