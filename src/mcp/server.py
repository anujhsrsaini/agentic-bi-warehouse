"""Model Context Protocol (MCP) Server for Governed DuckDB Analytics Agent.

Built on FastMCP, exposing certified business analytics tools, resources,
and prompts to Claude Desktop, Claude Code, Cursor, and agentic workflows.
"""

from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from src.agents.orchestrator import AgenticBIOrchestrator
from src.engine.session import WarehouseSession
from src.semantic.loader import SemanticLayerLoader

# Initialize FastMCP Server
mcp = FastMCP(
    "duckdb-analytics-agent",
    dependencies=["duckdb", "pyarrow", "pydantic", "sqlglot", "pyyaml"],
)

orchestrator = AgenticBIOrchestrator()
semantic_loader = SemanticLayerLoader()
session = WarehouseSession()


@mcp.tool()
def list_governed_metrics() -> str:
    """List all certified business metrics defined in the governed semantic layer.
    
    Returns a JSON string cataloging metric names, labels, mathematical formulas,
    supported dimensions, and business definitions.
    """
    config = semantic_loader.load()
    metrics = [
        {
            "name": m.name,
            "label": m.label,
            "description": m.description,
            "calculation": m.calculation,
            "dimensions": m.dimensions,
            "synonyms": m.synonyms,
        }
        for m in config.metrics
    ]
    return json.dumps(metrics, indent=2)


@mcp.tool()
def get_dataset_schema() -> str:
    """Return the schema metadata, column types, and sample categorical values for warehouse tables."""
    conn = session.get_connector()
    catalog = conn.introspect_schema()
    schema_dict = {}

    for tbl_name, tbl_meta in catalog.tables.items():
        schema_dict[tbl_name] = {
            "row_count": tbl_meta.row_count,
            "columns": {
                c_name: {
                    "standard_type": c_meta.standard_type.value,
                    "nullable": c_meta.nullable,
                    "sample_values": c_meta.sample_values,
                }
                for c_name, c_meta in tbl_meta.columns.items()
            },
        }

    return json.dumps(schema_dict, indent=2)


@mcp.tool()
def query_analytics_warehouse(natural_language_question: str) -> str:
    """Ask any business analytics question against the data warehouse.
    
    The engine resolves the request through the governed semantic layer, verifies
    safety via SQLGlot AST guardrails, executes against DuckDB (or configured warehouse),
    and returns verified tabular results with an executive summary and SQL trace.
    """
    state = orchestrator.process_query(natural_language_question)

    if state.clarification_prompt:
        return json.dumps({
            "status": "clarification_needed",
            "prompt": state.clarification_prompt,
            "options": state.clarification_options,
        }, indent=2)

    if state.execution_error:
        return json.dumps({
            "status": "error",
            "error": state.execution_error,
            "sql": state.validated_sql,
        }, indent=2)

    res = state.execution_result
    data_rows = res.to_pylist() if res else []

    output = {
        "status": "success",
        "question": state.question,
        "intent": state.intent.value,
        "metric": state.metric_name,
        "sql_executed": state.validated_sql,
        "execution_time_ms": round(res.execution_time_ms, 2) if res else 0.0,
        "rows_returned": len(data_rows),
        "summary": state.summary_narrative,
        "data": data_rows[:50],  # Return up to 50 sample rows
    }
    if state.lineage_mermaid:
        output["lineage_mermaid"] = state.lineage_mermaid

    return json.dumps(output, indent=2)


@mcp.resource("schema://warehouse_catalog")
def get_warehouse_catalog_resource() -> str:
    """Direct resource exposing full warehouse schema catalog."""
    return get_dataset_schema()


@mcp.prompt()
def analyze_saas_metrics(metric_name: str = "arr", timeframe: str = "current") -> str:
    """Pre-engineered prompt to run executive SaaS health analysis."""
    return (
        f"You are a Senior Strategic SaaS Financial Analyst. Please analyze the business metric '{metric_name}' "
        f"for {timeframe}. Call the `query_analytics_warehouse` tool with relevant questions, inspect segment breakdowns "
        f"across industry and tier, and provide an executive debrief highlighting key growth drivers and risks."
    )


def main():
    """Run FastMCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
