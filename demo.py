#!/usr/bin/env python3
"""Zero-Setup Interactive Demo Launcher for Governed DuckDB Analytics Agent.

Evaluators and CTOs can clone and run immediately:
    python demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cli import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSession ended by user.")
        sys.exit(0)
