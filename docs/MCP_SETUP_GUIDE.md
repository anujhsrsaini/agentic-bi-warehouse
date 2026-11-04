# Model Context Protocol (MCP) Setup Guide: Claude Desktop, Claude Code & Cursor

This guide details how to connect the **Governed DuckDB Analytics Agent** directly to your AI workflows via the Model Context Protocol (FastMCP).

---

## 1. FastMCP Server Specification

The repository includes a production-grade FastMCP server (`src/mcp/server.py`) exposing:
* **Tools**:
  * `list_governed_metrics`: Returns certified metrics (ARR, NRR, Churn, ARPA) and formulas.
  * `get_dataset_schema`: Provides warehouse catalog metadata, column types, and sample categorical values.
  * `query_analytics_warehouse`: High-stakes question answering with AST security guardrails and execution telemetry.
* **Resources**:
  * `schema://warehouse_catalog`: Machine-readable warehouse catalog JSON.
* **Prompts**:
  * `analyze_saas_metrics`: Pre-engineered executive financial analysis prompt.

---

## 2. Configuration for Claude Desktop

Add this block to your Claude Desktop configuration file:
* **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Linux**: `~/.config/Claude/claude_desktop_config.json`
* **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "duckdb-analytics-agent": {
      "command": "python3",
      "args": [
        "-m",
        "src.mcp.server"
      ],
      "cwd": "/path/to/agentic-bi-warehouse"
    }
  }
}
```

---

## 3. Configuration for Cursor IDE

1. Open Cursor Settings -> **Features** -> **MCP**.
2. Click **+ Add New MCP Server**.
3. Name: `duckdb-analytics-agent`
4. Type: `command`
5. Command: `python3 -m src.mcp.server`

---

## 4. Running Standalone via stdio

To test the MCP server transport directly in terminal:
```bash
python3 -m src.mcp.server
```
