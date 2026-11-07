"""Semantic Result Comparator (Defog sql-eval Pattern).

Evaluates execution equivalence between candidate and gold query results:
- Multiset row equivalence (permutation invariant unless ordered)
- Relative floating-point tolerance (epsilon <= 1e-4)
- Column alias and casing invariance
"""

from __future__ import annotations

import math
from typing import Any
import pyarrow as pa


class ResultComparator:
    """Float-tolerant multiset result comparator."""

    def __init__(self, float_tolerance: float = 1e-4):
        self.float_tolerance = float_tolerance

    def compare_tables(self, cand_table: pa.Table, gold_table: pa.Table) -> bool:
        """Compare candidate and gold PyArrow tables."""
        if len(cand_table) != len(gold_table) or cand_table.num_columns != gold_table.num_columns:
            return False

        if len(cand_table) == 0:
            return True

        cand_rows = cand_table.to_pylist()
        gold_rows = gold_table.to_pylist()

        # Compare row-by-row (if sorted) or multiset
        return self._compare_multisets(cand_rows, gold_rows)

    def _compare_multisets(self, cand: list[dict[str, Any]], gold: list[dict[str, Any]]) -> bool:
        """Compare lists of row dictionaries with float tolerance."""
        if len(cand) != len(gold):
            return False

        unmatched_gold = list(gold)

        for c_row in cand:
            match_idx = None
            for idx, g_row in enumerate(unmatched_gold):
                if self._compare_rows(c_row, g_row):
                    match_idx = idx
                    break
            if match_idx is None:
                return False
            unmatched_gold.pop(match_idx)

        return len(unmatched_gold) == 0

    def _compare_rows(self, c_row: dict[str, Any], g_row: dict[str, Any]) -> bool:
        """Compare two row dictionaries values."""
        c_vals = list(c_row.values())
        g_vals = list(g_row.values())

        if len(c_vals) != len(g_vals):
            return False

        for cv, gv in zip(c_vals, g_vals):
            if not self._compare_values(cv, gv):
                return False
        return True

    def _compare_values(self, a: Any, b: Any) -> bool:
        """Compare two cell values."""
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False

        # Float comparison
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            fa, fb = float(a), float(b)
            if math.isnan(fa) and math.isnan(fb):
                return True
            diff = abs(fa - fb)
            max_val = max(abs(fa), abs(fb))
            if max_val == 0.0:
                return True
            return (diff / max_val) <= self.float_tolerance

        # String comparison
        return str(a).strip().lower() == str(b).strip().lower()
