"""Interactive entry point for the experimental, optionally LLM-assisted agent."""

import warnings

from rich.console import Console
from rich.table import Table

from src.agents.orchestrator import AgenticBIOrchestrator
from src.core.config import settings
from src.llm.factory import llm_enabled

console = Console()


def is_help_request(question: str) -> bool:
    text = " ".join(question.lower().strip().rstrip("?.!").split())
    if text in {"help", "/help", "examples", "what can you do", "what can i ask"}:
        return True
    return ("question" in text and ("what" in text or "which" in text)
            and any(word in text for word in ("can", "could", "able"))
            and any(word in text for word in ("answer", "ask", "questions")))


def show_examples() -> None:
    console.print("\n[bold]Try asking about the sample online store:[/bold]")
    for question in (
        "What is GMV by customer state?",
        "What is the late delivery rate by customer state?",
        "How many orders were delivered?",
        "What is average order value?",
        "What is the average review score?",
        "Top 10 products and their breakdown of new vs repeat customers purchases/revenue and order splits",
    ):
        console.print(f"  • {question}")
    console.print("\nThe data describes Brazilian orders from 2016–2018. "
                  "GMV means the value of items sold, excluding shipping.")
    console.print("You can try other questions too; the live agent may not support every request. "
                  "Type /sql after an answer to see its query, or exit to quit.")


def main():
    if not llm_enabled():
        console.print("[red]LLM mode is unavailable. Set SARVAM_API_KEY in .env and AGENTIC_BI_ENGINE=langgraph.[/red]")
        return 1
    console.print("Experimental live agent. Questions and relevant context may be sent to the configured LLM provider.")
    console.print("The data is a sample Brazilian online store from 2016–2018. Answers require review.")
    console.print("Type 'help' for examples, '/sql' for the last query, '/privacy' for customer-ID protection, or 'exit'.")
    console.print(f"Customer-ID protection: {'ON' if settings.customer_identifier_protection else 'OFF'}")
    agent = AgenticBIOrchestrator()
    last_sql = None
    while True:
        try:
            question = input("\nQuestion: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue
        command = question.lower()
        if command in {"/privacy", "/privacy on", "/privacy off"}:
            if command == "/privacy on":
                settings.customer_identifier_protection = True
            elif command == "/privacy off":
                settings.customer_identifier_protection = False
            console.print(f"Customer-ID protection: {'ON' if settings.customer_identifier_protection else 'OFF'}")
            console.print("Use /privacy on or /privacy off. This controls customer_unique_id in this process; "
                          "other query checks still apply, and database permissions may impose further limits.")
            continue
        if is_help_request(question):
            show_examples()
            continue
        if question.lower() in {"/sql", "show sql"}:
            console.print(f"SQL used:\n{last_sql}" if last_sql else "No query is available yet. Ask a data question first.")
            continue
        last_sql = None
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Arrow output on a DB-API result makes an extra copy.*", category=UserWarning)
                state = agent.process_query(question)
            if state.clarification_prompt:
                console.print(f"Clarification needed: {state.clarification_prompt}")
                continue
            if state.execution_error:
                console.print(f"[red]Unable to answer: {state.execution_error}[/red]")
                continue
            result = state.execution_result
            if result is None:
                console.print("No result was produced.")
                continue
            if state.summary_narrative:
                console.print(f"\n[bold]Answer:[/bold] {state.summary_narrative}")
            rows = result.to_pylist()[:20]
            def display(value):
                return f"{value:,.2f}" if isinstance(value, float) else str(value)
            if len(result.column_names) > 6:
                # Wide terminal tables truncate both headings and values.
                for index, row in enumerate(rows, start=1):
                    console.print(f"\n[bold]Result {index}[/bold]")
                    for name in result.column_names:
                        console.print(f"  {name.replace('_', ' ').capitalize()}: {display(row[name])}")
            else:
                table = Table()
                for name in result.column_names:
                    table.add_column(name)
                for row in rows:
                    table.add_row(*(display(row[name]) for name in result.column_names))
                console.print(table)
            if len(result.data) > 20:
                console.print(f"Showing 20 of {len(result.data)} rows.")
            last_sql = state.validated_sql or None
            if last_sql:
                console.print("Type /sql to see the query behind this answer.")
        except Exception as exc:
            console.print(f"[red]Unable to process the question ({type(exc).__name__}).[/red]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
