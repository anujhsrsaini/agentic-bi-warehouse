"""Production Enterprise FastAPI Cockpit Backend for Governed DuckDB Analytics Agent.

Provides high-performance REST APIs:
- POST /api/query: Natural language query execution through multi-agent cognitive loop
- POST /api/security/test: Real-time AST security firewall sandbox
- GET  /api/metrics: Certified metric registry from semantic layer
- GET  /api/stats: Vectorized warehouse metadata & row count statistics
- POST /api/chasm-trap/demo: Live fan-out / chasm trap demonstration
- Static assets: Serves built React frontend at /
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.orchestrator import AgenticBIOrchestrator
from src.core.config import settings
from src.core.exceptions import SecurityViolationError
from src.engine.session import WarehouseSession
from src.security.ast_validator import ASTSecurityValidator
from src.semantic.loader import SemanticLayerLoader

app = FastAPI(
    title="Governed DuckDB Analytics Agent API",
    description="Sub-15ms Vectorized OLAP • SQLGlot AST Guardrails • Semantic Layer",
    version="1.0.0",
)

# CORS: production demo origin plus local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://demo.d2cgrowthos.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Initialize singletons
orchestrator = AgenticBIOrchestrator()
security_validator = ASTSecurityValidator()
semantic_loader = SemanticLayerLoader()


class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language analytical question")
    session_id: str = Field("default-session", description="Session identifier")


class SecurityTestRequest(BaseModel):
    sql: str = Field(..., description="Raw SQL string to test against AST firewall")


def detect_chart_type(columns: list[str], rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Intelligently recommend visual chart type and axes based on query output."""
    if not rows or not columns:
        return None

    first_row = rows[0]
    num_cols = [c for c in columns if isinstance(first_row.get(c), (int, float))]
    cat_cols = [c for c in columns if not isinstance(first_row.get(c), (int, float))]

    if not num_cols:
        return None

    # Case 1: 1 categorical column + 1 or more numeric columns
    if cat_cols:
        x_key = cat_cols[0]
        y_key = num_cols[0]

        # Donut/Pie recommendation for small categorical breakdowns (e.g. payment_type <= 6)
        if len(rows) <= 6 and ("payment" in x_key.lower() or "status" in x_key.lower() or "type" in x_key.lower()):
            return {
                "type": "donut",
                "xKey": x_key,
                "yKey": y_key,
                "metrics": num_cols,
                "title": f"Distribution by {x_key.replace('_', ' ').title()}",
            }

        # Date/time trend -> Line chart
        if any(d in x_key.lower() for d in ["date", "month", "year", "time", "day"]):
            # If New vs Repeat split comparison
            if "new_customer_gmv" in num_cols and "repeat_customer_gmv" in num_cols:
                return {
                    "type": "line",
                    "xKey": x_key,
                    "yKey": "new_customer_gmv",
                    "metrics": ["new_customer_gmv", "repeat_customer_gmv"],
                    "title": f"New vs Repeat GMV Split by {x_key.replace('_', ' ').title()}",
                }

            if "new_customers" in num_cols and "repeat_customers" in num_cols:
                return {
                    "type": "line",
                    "xKey": x_key,
                    "yKey": "new_customers",
                    "metrics": ["new_customers", "repeat_customers"],
                    "title": f"New vs Repeat Customer Count by {x_key.replace('_', ' ').title()}",
                }

            return {
                "type": "line",
                "xKey": x_key,
                "yKey": y_key,
                "metrics": num_cols,
                "title": f"Trend by {x_key.replace('_', ' ').title()}",
            }

        # Combo chart: volume metric as bars + rate/duration metrics as lines.
        rate_cols = [
            c for c in num_cols
            if any(t in c.lower() for t in ("pct", "rate", "ratio", "days", "delay"))
        ]
        volume_cols = [c for c in num_cols if c not in rate_cols]
        if rate_cols and volume_cols:
            bar_key = volume_cols[0]
            return {
                "type": "combo",
                "xKey": x_key,
                "yKey": bar_key,
                "barKey": bar_key,
                "lineKeys": rate_cols,
                "metrics": num_cols,
                "title": (
                    f"{bar_key.replace('_', ' ').title()} & "
                    f"{', '.join(c.replace('_', ' ').title() for c in rate_cols)} "
                    f"by {x_key.replace('_', ' ').title()}"
                ),
            }

        # Otherwise vertical or horizontal bar chart
        return {
            "type": "bar",
            "xKey": x_key,
            "yKey": y_key,
            "metrics": num_cols,
            "title": f"{y_key.replace('_', ' ').title()} by {x_key.replace('_', ' ').title()}",
        }

    # Case 2: Only numeric columns (e.g. overall single metric KPI)
    if len(num_cols) == 1 and len(rows) == 1:
        return {
            "type": "kpi",
            "xKey": "",
            "yKey": num_cols[0],
            "metrics": num_cols,
            "title": num_cols[0].replace("_", " ").title(),
        }

    return {
        "type": "bar",
        "xKey": columns[0],
        "yKey": num_cols[0],
        "metrics": num_cols,
        "title": "Analytical Results",
    }


@app.post("/api/query")
def execute_query(req: QueryRequest):
    """Execute a natural language query through the Governed Agentic BI pipeline."""
    try:
        state = orchestrator.process_query(req.question, session_id=req.session_id)
        
        # Format execution result data
        res_data: list[dict[str, Any]] = []
        columns: list[str] = []
        exec_time_ms = 0.0
        rows_returned = 0
        rows_scanned = 0

        if state.execution_result:
            res_data = state.execution_result.to_pylist()
            columns = state.execution_result.column_names
            exec_time_ms = state.execution_result.execution_time_ms
            rows_returned = state.execution_result.rows_returned
            rows_scanned = state.execution_result.rows_scanned

        chart_spec = detect_chart_type(columns, res_data)

        # Build response payload
        return {
            "question": req.question,
            "session_id": req.session_id,
            "intent": state.intent.value if hasattr(state.intent, "value") else str(state.intent),
            "confidence": state.confidence,
            "clarification_prompt": state.clarification_prompt,
            "clarification_options": state.clarification_options,
            "metric_name": state.metric_name,
            "dimensions": state.dimensions,
            "filters": state.filters,
            "grounded_entities": state.grounded_entities,
            "validated_sql": state.validated_sql or state.raw_sql,
            "raw_sql": state.raw_sql,
            "sql_rationale": state.sql_rationale,
            "validation_time_us": state.validation_time_us,
            "security_passed": state.security_passed,
            "security_error": state.security_error,
            "execution_error": state.execution_error,
            "execution_time_ms": exec_time_ms,
            "rows_returned": rows_returned,
            "rows_scanned": rows_scanned,
            "columns": columns,
            "data": res_data,
            "summary_narrative": state.summary_narrative,
            "lineage_mermaid": state.lineage_mermaid,
            "lineage_ascii": state.lineage_ascii,
            "chart_spec": chart_spec,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/security/test")
def test_security(req: SecurityTestRequest):
    """Test SQL query against the 7-stage SQLGlot AST security firewall."""
    t0 = time.perf_counter()
    try:
        sanitized_sql, validation_time_us = security_validator.validate_and_sanitize(req.sql)
        return {
            "blocked": False,
            "violation": None,
            "code": "SECURITY_PASSED",
            "sanitized_sql": sanitized_sql,
            "validation_time_us": validation_time_us or ((time.perf_counter() - t0) * 1_000_000),
            "message": "✓ Query passed all 7 AST security guardrail checks. Safe for execution.",
        }
    except SecurityViolationError as e:
        us = (time.perf_counter() - t0) * 1_000_000
        return {
            "blocked": True,
            "violation": str(e),
            "code": getattr(e, "violation_type", "SECURITY_VIOLATION"),
            "sanitized_sql": None,
            "validation_time_us": us,
            "message": f"🛡️ BLOCKED by AST Firewall: {e}",
        }
    except Exception as e:
        us = (time.perf_counter() - t0) * 1_000_000
        return {
            "blocked": True,
            "violation": f"Parse / Validation Error: {e}",
            "code": "SYNTAX_PARSE_ERROR",
            "sanitized_sql": None,
            "validation_time_us": us,
            "message": f"🛡️ BLOCKED: {e}",
        }


@app.get("/api/metrics")
def get_certified_metrics():
    """Retrieve all certified metric definitions from semantic_layer.yaml."""
    cfg = semantic_loader.load()
    return [
        {
            "name": m.name,
            "label": m.label,
            "description": m.description,
            "model": m.model,
            "calculation": m.calculation,
            "filter": m.filter,
            "dimensions": m.dimensions,
            "synonyms": m.synonyms,
        }
        for m in cfg.metrics
    ]


@app.get("/api/stats")
def get_warehouse_stats():
    """Return database engine status, table row counts, and performance metrics."""
    return {
        "total_rows": 550761,
        "tables": 8,
        "engine": "DuckDB Vectorized In-Process",
        "version": "1.1.0",
        "speed": "sub-15ms OLAP",
        "dataset": "Olist Brazilian E-Commerce (Kaggle)",
        "table_stats": [
            {"table": "orders", "rows": 99441, "description": "Core transaction headers"},
            {"table": "order_items", "rows": 112650, "description": "Line-item products & prices"},
            {"table": "order_payments", "rows": 103886, "description": "Payment installments & methods"},
            {"table": "order_reviews", "rows": 99224, "description": "Customer CSAT 1-5 ratings"},
            {"table": "customers", "rows": 99441, "description": "Customer location & state"},
            {"table": "products", "rows": 32951, "description": "Product dimensions & categories"},
            {"table": "sellers", "rows": 3095, "description": "Merchant locations & states"},
            {"table": "category_translation", "rows": 73, "description": "PT to EN category dictionary"},
        ],
    }


@app.post("/api/chasm-trap/demo")
def demonstrate_chasm_trap():
    """Execute live side-by-side comparison of naive multi-join fan-out vs governed CTE query."""
    connector = WarehouseSession().get_connector()

    # 1. Naive Multi-Join (Fan-out / Chasm Trap)
    naive_sql = """
SELECT 
    COUNT(*) AS total_cartesian_rows,
    ROUND(SUM(oi.price), 2) AS naive_gmv
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN order_payments op ON o.order_id = op.order_id
WHERE o.order_status != 'canceled';
    """.strip()

    # 2. Governed Pre-Aggregated CTE
    cte_sql = """
WITH items_agg AS (
    SELECT order_id, SUM(price) AS gmv FROM order_items GROUP BY order_id
),
payments_agg AS (
    SELECT order_id, SUM(payment_value) AS payment FROM order_payments GROUP BY order_id
)
SELECT 
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(ia.gmv), 2) AS governed_gmv,
    ROUND(SUM(pa.payment), 2) AS governed_payment
FROM orders o
LEFT JOIN items_agg ia ON o.order_id = ia.order_id
LEFT JOIN payments_agg pa ON o.order_id = pa.order_id
WHERE o.order_status != 'canceled';
    """.strip()

    r1 = connector.execute_query(naive_sql)
    r2 = connector.execute_query(cte_sql)

    naive_res = r1.to_pylist()[0]
    gov_res = r2.to_pylist()[0]

    return {
        "naive": {
            "sql": naive_sql,
            "cartesian_rows": naive_res["total_cartesian_rows"],
            "naive_gmv": naive_res["naive_gmv"],
            "execution_time_ms": round(r1.execution_time_ms, 2),
            "explanation": (
                "NAIVE MULTI-JOIN ERROR: Direct JOIN of order_items (1:N) and order_payments (1:N) "
                f"creates a Cartesian cross-product of {naive_res['total_cartesian_rows']:,} rows "
                f"(vs {gov_res['total_orders']:,} actual distinct orders). GMV is falsely inflated by "
                f"+R$ {naive_res['naive_gmv'] - gov_res['governed_gmv']:,.2f}!"
            ),
        },
        "governed": {
            "sql": cte_sql,
            "total_orders": gov_res["total_orders"],
            "governed_gmv": gov_res["governed_gmv"],
            "governed_payment": gov_res["governed_payment"],
            "execution_time_ms": round(r2.execution_time_ms, 2),
            "explanation": (
                "GOVERNED SEMANTIC LAYER RESOLUTION: Each fact table (items, payments) is aggregated "
                "in its own CTE before joining to the core orders dimension, preserving exact mathematical "
                f"truth: R$ {gov_res['governed_gmv']:,.2f} GMV with zero row multiplication."
            ),
        },
        "inflation_amount": round(naive_res["naive_gmv"] - gov_res["governed_gmv"], 2),
        "fanout_factor": round(naive_res["total_cartesian_rows"] / gov_res["total_orders"], 2),
    }


@app.get("/api/health")
def health(response: Response):
    """Readiness probe: verify data and config assets are present."""
    data_ok = settings.data_dir.exists()
    semantic_ok = (settings.config_dir / "semantic_layer.yaml").exists()
    policy_ok = (settings.config_dir / "security_policies.yaml").exists()
    ok = data_ok and semantic_ok and policy_ok
    if not ok:
        response.status_code = 503
    return {
        "status": "ok" if ok else "degraded",
        "data_present": data_ok,
        "semantic_layer_present": semantic_ok,
        "security_policy_present": policy_ok,
    }


# Mount static files if frontend is built
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
