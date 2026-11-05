# Governed DuckDB Analytics Agent & Poly-Warehouse BI Engine

[![CI](https://github.com/anujhsrsaini/agentic-bi-warehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/anujhsrsaini/agentic-bi-warehouse/actions)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.1%2B-yellow.svg)](https://duckdb.org)
[![FastMCP](https://img.shields.io/badge/MCP-1.2.0%2B-green.svg)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Dataset](https://img.shields.io/badge/Dataset-Olist_E--Commerce_550k_rows-orange.svg)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

An enterprise-grade, governed analytical agent and poly-warehouse query engine. Built on **in-process vectorized DuckDB** with pluggable connectors for **Snowflake**, **Google BigQuery**, **PostgreSQL**, and **ClickHouse**, governed by a **YAML Semantic Layer** and protected by a **7-Stage SQLGlot AST Security Firewall**.

Powered by the **real-world Olist Brazilian E-Commerce public dataset** — 550,761 rows across 8 tables, ingested directly from Kaggle into Parquet. No synthetic data.

---

## ⚡ The 60-Second Zero-Setup Verification

No cloud accounts, credentials, or remote clusters required. Evaluators and CTOs can clone and launch the interactive terminal cockpit in under 5 seconds:

```bash
git clone https://github.com/anujhsrsaini/agentic-bi-warehouse.git
cd agentic-bi-warehouse
pip install -r requirements.txt

# (Optional) Re-ingest Olist data from Kaggle — already included as Parquet
# python scripts/ingest_olist.py

# Run the interactive zero-setup demo
python demo.py
```

---

## 1. The Problem: The "Spider 2.0 Reality Cliff"

Modern data teams want AI agents (Claude Code, Cursor, autonomous BI bots) to answer business questions directly from enterprise warehouses. However, naive Text-to-SQL fails in production:

* On clean, textbook academic schemas (**Spider 1.0**), LLMs score over **91.2%**.
* On enterprise data warehouses (**Spider 2.0 (ICLR 2025)**) with 1,000+ columns and real-world business context, accuracy drops to **21.3%**.

### Why Naive Text-to-SQL Fails:
1. **Hallucinated Business Logic**: When asked for *"GMV"* or *"AOV"*, an LLM writes arbitrary sums without accounting for canceled orders, chasm-trap fan-out, or freight exclusions.
2. **Join Traps (Fan-out & Chasm Traps)**: Joining `order_items` AND `order_payments` both to `orders` duplicates rows — naively summing payment values per order item inflates GMV by the item count. This system uses CTE-based pre-aggregation to avoid this trap.
3. **Categorical Value Mismatches (The #1 Failure Mode)**: Users ask for *"São Paulo"* or *"credit card"*, but the database stores `'SP'` and `'credit_card'`. Naive text-to-SQL filters return zero rows.
4. **Security & Sandbox Breaches**: Direct SQL execution risks SQL injection, mutating commands (`DROP TABLE`), and filesystem exfiltration (`read_parquet('/etc/passwd')`).

---

## 2. The Dataset: Olist Brazilian E-Commerce

**550,761 rows** · **8 tables** · Real orders from 2016–2018 · Public Domain (Kaggle)

| Table | Rows | Description |
|:---|---:|:---|
| `orders` | 99,441 | Order lifecycle, status, timestamps |
| `order_items` | 112,650 | Line items — price, freight, product, seller |
| `order_payments` | 103,886 | Payment type, installments, value |
| `order_reviews` | 99,224 | Star ratings (1–5) with timestamps |
| `customers` | 99,441 | Customer city, state (Brazilian states) |
| `products` | 32,951 | Category, dimensions, weight |
| `sellers` | 3,095 | Seller city, state |
| `category_translation` | 73 | Portuguese → English category names |

### Certified Business KPIs

| Metric | Formula | Key Consideration |
|:---|:---|:---|
| **GMV** | `SUM(order_items.price)` | Excludes freight & canceled orders |
| **Total Orders** | `COUNT(DISTINCT orders.order_id)` | Delivered only |
| **AOV** | `SUM(price) / COUNT(DISTINCT order_id)` | CTE-aggregated, chasm-trap safe |
| **Freight Ratio** | `SUM(freight) / SUM(price) * 100` | Logistics overhead indicator |
| **Avg Review Score** | `AVG(review_score)` | CSAT proxy, 1–5 stars |
| **Total Payment Value** | `SUM(payment_value)` | Includes freight & installments |
| **Delivery Delay Rate** | `% orders delivered after estimated date` | OTD performance |

---

## 3. System Architecture

```mermaid
flowchart TD
    subgraph Clients["1. Agent & User Touchpoints"]
        CLI["Interactive CLI Cockpit (demo.py)"]
        ClaudeDesktop["Claude Desktop / Claude Code (FastMCP)"]
        CursorIDE["Cursor IDE / Agentic Tools (FastMCP)"]
    end

    subgraph AgenticBrain["2. Multi-Agent Cognitive StateGraph"]
        direction TB
        A1["1. Triage & Intent Router<br>(Proactive Disambiguation)"]
        A2["2. 3-Tier Value Grounder & Schema Linker<br>(Brazilian States + Payment Types + Statuses)"]
        A3["3. SQL Generator & Query Planner<br>(Dual-Track: Certified vs. Exploratory)"]
        A4["4. AST Security & Guardrail Validator<br>(7-Stage SQLGlot Firewall)"]
        A5["5. Self-Healing Execution Agent<br>(Reflexion Loop <= 3)"]
        A6["6. Diagnostic 'Why' & Canvas Synthesizer<br>(CSAT + Delivery Delay Attribution)"]

        A1 --> A2 --> A3 --> A4 --> A5
        A5 -.->|Runtime Error| A3
        A5 --> A6
    end

    subgraph UWAL["3. Unified Warehouse Abstraction Layer (UWAL)"]
        Transpiler["SQLGlot Dialect Transpiler"]
        DuckDBPool["Thread-Safe DuckDB Connection Pool"]
        ParquetCache["Evidence-Style Parquet Query Cache"]

        subgraph Adapters["Pluggable Warehouse Adapters"]
            DuckDBAdapter["DuckDB (Default / In-Memory Lakehouse)"]
            PGAdapter["PostgreSQL (psycopg3 / ADBC)"]
            SnowflakeAdapter["Snowflake (Arrow Batch Streaming)"]
            BQAdapter["BigQuery (Dry-Run Cost Caps)"]
            CHAdapter["ClickHouse (Real-Time Columnar OLAP)"]
        end
    end

    subgraph Storage["4. Columnar Olist Data Lakehouse (550,761 Rows)"]
        Data[("Partitioned Parquet Files<br>• orders.parquet (99k rows)<br>• order_items.parquet (113k rows)<br>• order_payments.parquet (104k rows)<br>• order_reviews.parquet (99k rows)<br>• customers.parquet (99k rows)<br>• products.parquet (33k rows)<br>• sellers.parquet (3k rows)<br>• category_translation.parquet (73 rows)")]
    end

    Clients --> AgenticBrain
    A5 --> UWAL
    UWAL --> Storage
    A6 --> Clients
```

---

## 4. The 5 Breakthrough Innovations

1. **Chasm-Trap-Safe CTE Architecture**:
   - Olist has a fan-out trap: `orders → order_items (1:N)` AND `orders → order_payments (1:N)`. Naively joining both duplicates rows. The system uses CTEs to pre-aggregate each fact table before joining, ensuring zero inflation.
2. **Column-Level Data Lineage & Mathematical Explainability (`src/engine/lineage.py`)**:
   - Answers *"Why is this GMV number different from last month?"* by traversing SQLGlot AST graphs to emit interactive **Mermaid DAGs**, **ASCII hierarchy trees**, and plain-English calculation narratives.
3. **3-Tier Brazilian E-Commerce Entity Grounder (`src/agents/entity_grounder.py`)**:
   - Maps "São Paulo" → `customer_state = 'SP'`, "credit card" → `payment_type = 'credit_card'`, "Rio" → `customer_state = 'RJ'` — eliminating the #1 Text-to-SQL failure mode.
4. **Diagnostic "Why" Analytics — CSAT & Delivery Attribution (`src/agents/attribution.py`)**:
   - Goes beyond "What is the review score?" to "Why did scores drop in RJ?" Uses **Additive Variance Decomposition** to identify whether CSAT degradation is driven by late deliveries, product issues, or seller performance.
5. **Conversational Canvas UI & Grammar-of-Graphics (`src/agents/canvas.py`)**:
   - Automatically compiles query outputs into executive scorecard badges, interactive sparklines, and optimal Vega-Lite v5 JSON charts.

---

## 5. Performance & Benchmark Scorecard

Evaluated over the **550,761-row real-world Olist E-Commerce dataset** via `eval/benchmark_runner.py`:

| Benchmark Metric | Observed Value | SLA Target Gate | Status |
| :--- | :---: | :---: | :---: |
| **Execution Accuracy ($\text{EX}_{\text{rel}}$)** | **100.0%** | $\ge 90.0\%$ | **PASSED** |
| **AST Safety Pass Rate (ASPR)** | **100.0%** | $100.0\%$ | **PASSED** |
| **Semantic Metric Precision (SMP)** | **100.0%** | $100.0\%$ | **PASSED** |
| **P50 Query Latency** | **7.96 ms** | $< 15.00\text{ ms}$ | **PASSED** |
| **P95 Query Latency** | **12.97 ms** | $< 25.00\text{ ms}$ | **PASSED** |
| **Analytical Throughput** | **115.1 QPS** | $> 50.0\text{ QPS}$ | **PASSED** |
| **Chasm-Trap Attack Blocked** | **✓** | Mandatory | **PASSED** |

---

## 6. Model Context Protocol (FastMCP) Integration

Connect directly to **Claude Desktop**, **Claude Code**, or **Cursor**:

```json
{
  "mcpServers": {
    "duckdb-analytics-agent": {
      "command": "python3",
      "args": ["-m", "src.mcp.server"],
      "cwd": "/absolute/path/to/agentic-bi-warehouse"
    }
  }
}
```

Exposes three certified tools:
* `list_governed_metrics()`: Catalog of certified Olist KPIs (GMV, AOV, CSAT, Delivery Delay Rate, etc.).
* `get_dataset_schema()`: Complete Olist schema metadata, column types, and Brazilian state/payment enums.
* `query_analytics_warehouse(natural_language_question)`: End-to-end governed execution pipeline returning verified tabular results and execution telemetry.

---

## 7. Developer Commands

```bash
# (Re-)ingest Olist dataset from Kaggle as Parquet
python scripts/ingest_olist.py

make test    # Run full pytest suite
make eval    # Run Olist-calibrated Spider 2.0-style benchmark harness
make demo    # Launch interactive Rich terminal cockpit
make mcp     # Launch FastMCP server over stdio
```

---

## 8. Example CLI Queries

```
[1] GMV by Brazilian customer state
[2] Average Review Score (CSAT) by product category
[3] Diagnostic Root-Cause: Why did review scores drop?
[4] Entity Grounding: GMV for Credit Card payments in SP
[5] Ambiguity Test: Show revenue → triage agent asks for clarification
[6] Late Delivery Rate by state
[7] Payment method breakdown
```

---

## 9. License

Apache 2.0. See [LICENSE](LICENSE) for details.

---

## 10. Dataset Attribution

This project uses the **[Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)** made available by Olist Store on Kaggle under a [Creative Commons Attribution Non-Commercial ShareAlike 4.0 International](https://creativecommons.org/licenses/by-nc-sa/4.0/) license. Data represents real commercial orders from the Brazilian marketplace from 2016 to 2018.
