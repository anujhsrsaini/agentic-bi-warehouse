#!/usr/bin/env python3
"""Launcher for Governed DuckDB Analytics Agent Web Cockpit.

Usage:
    python run_app.py [--port 8000] [--host 0.0.0.0] [--reload]
"""

import argparse
import sys
from pathlib import Path
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Governed DuckDB Analytics Agent Web Cockpit")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    print(f"""
    ======================================================================
    🚀 Governed DuckDB Analytics Agent — Enterprise Web Cockpit
    ======================================================================
    • Engine:        DuckDB Vectorized In-Process (550,761 Olist Rows)
    • AST Firewall:  SQLGlot 7-Stage Sandbox Guardrails
    • Semantic:      Certified Metrics & Multi-Hop BFS Join Transpiler
    • URL:           http://localhost:{args.port}
    • API Docs:      http://localhost:{args.port}/docs
    ======================================================================
    """)

    uvicorn.run("api:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
