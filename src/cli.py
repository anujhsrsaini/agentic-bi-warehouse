"""Interactive Rich Terminal Cockpit for Governed DuckDB Analytics Agent."""

from __future__ import annotations

import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt

from src.agents.orchestrator import AgenticBIOrchestrator
from src.core.exceptions import SecurityViolationError
from src.security.ast_validator import ASTSecurityValidator

console = Console()
orchestrator = AgenticBIOrchestrator()
security_validator = ASTSecurityValidator()


def render_banner() -> None:
    banner = """[bold cyan]
   █████╗  ██████╗ ███████╗███╗   ██╗████████╗██╗ ██████╗     ██████╗ ██╗
  ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██║██╔════╝     ██╔══██╗██║
  ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██║██║  ███╗    ██████╔╝██║
  ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██║██║   ██║    ██╔══██╗██║
  ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ██║╚██████╔╝    ██████╔╝██║
  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝ ╚═════╝     ╚═════╝ ╚═╝
    [/bold cyan]
[bold green]Governed DuckDB Analytics Agent & Poly-Warehouse BI Engine[/bold green]
[dim]Sub-15ms Vectorized OLAP • SQLGlot AST Guardrails • FastMCP Native • 115k Rows[/dim]
    """
    console.print(Panel(banner, border_style="cyan"))


def execute_and_render(question: str) -> None:
    console.print(f"\n[bold yellow]❓ Question:[/bold yellow] [bold white]{question}[/bold white]")
    
    with console.status("[bold green]Running multi-agent cognitive pipeline...[/bold green]", spinner="dots"):
        state = orchestrator.process_query(question)

    if state.clarification_prompt:
        console.print(Panel(
            f"[bold yellow]⚠️ Disambiguation Required:[/bold yellow]\n{state.clarification_prompt}\n\n"
            + "\n".join(f"[cyan]{opt}[/cyan]" for opt in state.clarification_options),
            title="[bold yellow]Triage Agent[/bold yellow]",
            border_style="yellow"
        ))
        return

    if state.execution_error:
        console.print(Panel(
            f"[bold red]❌ Execution Error:[/bold red]\n{state.execution_error}\n\n[dim]SQL: {state.validated_sql}[/dim]",
            title="[bold red]Error[/bold red]",
            border_style="red"
        ))
        return

    # Render SQL & Timing
    res = state.execution_result
    timing_str = f"⚡ Execution: {res.execution_time_ms:.2f} ms | AST Audit: {state.validation_time_us:.1f} μs | Rows: {len(res.data):,}"
    console.print(Panel(
        Syntax(state.validated_sql, "sql", theme="monokai", line_numbers=True),
        title=f"[bold green]Verified Governed SQL[/bold green] ({timing_str})",
        border_style="green"
    ))

    # Render Executive Narrative
    if state.summary_narrative:
        console.print(Panel(
            f"[bold white]{state.summary_narrative}[/bold white]",
            title="[bold blue]🧠 Executive Insights[/bold blue]",
            border_style="blue"
        ))

    # Render Table
    if res and len(res.data) > 0:
        table = Table(title="[bold]Analytical Results[/bold]", border_style="dim")
        for col in res.column_names:
            table.add_column(col.replace("_", " ").title(), style="cyan")
        
        rows = res.to_pylist()[:15]
        for row in rows:
            formatted_cells = []
            for col in res.column_names:
                v = row[col]
                if isinstance(v, float):
                    cell = f"${v:,.2f}" if any(k in col for k in ["arr", "mrr", "amount", "revenue", "price"]) else f"{v:,.2f}"
                elif isinstance(v, int):
                    cell = f"{v:,}"
                else:
                    cell = str(v)
                formatted_cells.append(cell)
            table.add_row(*formatted_cells)
        console.print(table)
        if len(res.data) > 15:
            console.print(f"[dim]... and {len(res.data) - 15} more rows.[/dim]")

    # Render Lineage if available
    if state.lineage_ascii:
        console.print(Panel(
            f"[dim]{state.lineage_ascii}[/dim]",
            title="[bold magenta]📐 Column-Level Lineage Trace[/bold magenta]",
            border_style="magenta"
        ))


def run_adversarial_test() -> None:
    console.print("\n[bold red]🛡️ Running Adversarial Security Test Suite...[/bold red]")
    attacks = [
        ("DROP TABLE dim_customers;", "Mutating DDL Drop"),
        ("SELECT 1; DROP TABLE dim_customers;", "Multi-Statement Stacking"),
        ("SELECT * FROM read_csv('/etc/passwd');", "Path Traversal Arbitrary Read"),
        ("SELECT * FROM read_parquet('s3://leak/data.parquet');", "Out-of-Bounds Cloud Exfiltration"),
        ("SELECT * FROM dim_customers CROSS JOIN fct_subscriptions;", "Unconstrained Cartesian Join DoS"),
        ("SELECT * FROM unauthorized_internal_payroll;", "Unregistered Table Access"),
    ]

    for atk, label in attacks:
        try:
            security_validator.validate_and_sanitize(atk)
            console.print(f"[bold red]❌ FAILED: {label} was not blocked![/bold red]")
        except SecurityViolationError as e:
            console.print(f"[bold green]✓ BLOCKED:[/bold green] [dim]{label}[/dim] ──► [yellow]{e}[/yellow]")


def main() -> None:
    render_banner()
    while True:
        console.print("\n[bold cyan]Select an Analytical Action:[/bold cyan]")
        console.print("  [1] 📊 What is our ARR by industry?")
        console.print("  [2] 💵 What is our Gross Cash Collected by Country?")
        console.print("  [3] 🔍 Diagnostic Root-Cause: Why did churn increase?")
        console.print("  [4] 🎯 Entity Grounding: What is our ARR for Enterprise in US?")
        console.print("  [5] ⚠️ Ambiguity Test: Show revenue (Watch Triage Agent ask clarification)")
        console.print("  [6] 💬 Ask Custom Analytical Question")
        console.print("  [7] 🛡️ Run Adversarial Security & Sandbox Test")
        console.print("  [0] 🚪 Exit")

        choice = Prompt.ask("\nEnter choice", default="1")
        if choice == "0":
            console.print("[green]Goodbye![/green]")
            break
        elif choice == "1":
            execute_and_render("What is our ARR by industry?")
        elif choice == "2":
            execute_and_render("What is our gross cash collected by country?")
        elif choice == "3":
            execute_and_render("Why did churn increase?")
        elif choice == "4":
            execute_and_render("What is our ARR for Enterprise in US?")
        elif choice == "5":
            execute_and_render("Show revenue")
        elif choice == "6":
            q = Prompt.ask("\nEnter your analytical question")
            if q.strip():
                execute_and_render(q)
        elif choice == "7":
            run_adversarial_test()


if __name__ == "__main__":
    main()
