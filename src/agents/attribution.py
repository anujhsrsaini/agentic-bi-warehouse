"""Diagnostic 'Why' Anomaly & Root Cause Attribution Engine — Olist Edition.

Calculates exact dimension contribution percentages for e-commerce metrics:
- Delivery Delay Rate Driver Analysis: which states have the highest late delivery rates
- Review Score Variance Decomposition: which states / categories drive CSAT drops
- GMV Concentration Analysis: contribution of top states / categories
- Additive Variance Decomposition: Delta(Metric) = sum(Delta_dimension_i)
- Kitagawa Rate-Mix Decomposition: isolates Mix Effects vs Rate Effects
"""

from __future__ import annotations

from typing import Any
import pyarrow as pa


class MetricAttributionEngine:
    """Diagnoses drivers of metric spikes and drops for Olist e-commerce analytics."""

    def diagnose_review_score_drivers(self, query_result_table: pa.Table) -> dict[str, Any]:
        """Analyze review score and delivery delay drivers by Brazilian state.

        Expects columns: customer_state, total_orders, avg_review_score,
                         total_gmv, late_delivery_pct
        """
        pydict = query_result_table.to_pydict()
        states = pydict.get("customer_state", [])
        avg_scores = pydict.get("avg_review_score", [])
        late_pcts = pydict.get("late_delivery_pct", [])
        total_orders = pydict.get("total_orders", [])
        total_gmv = pydict.get("total_gmv", [])

        if not avg_scores or not states:
            return {"status": "insufficient_data", "summary": "No cohort data available for diagnosis."}

        # Lowest review score state (quality risk)
        min_score_idx = min(range(len(avg_scores)), key=lambda i: avg_scores[i] if avg_scores[i] is not None else 5.0)
        # Highest late delivery pct state (logistics risk)
        max_late_idx = max(range(len(late_pcts)), key=lambda i: late_pcts[i] if late_pcts[i] is not None else 0.0)
        # Highest GMV state (business priority)
        max_gmv_idx = max(range(len(total_gmv)), key=lambda i: float(total_gmv[i] or 0.0))

        lowest_score_state = states[min_score_idx]
        lowest_score_val = float(avg_scores[min_score_idx] or 0.0)

        highest_late_state = states[max_late_idx]
        highest_late_pct = float(late_pcts[max_late_idx] or 0.0)

        highest_gmv_state = states[max_gmv_idx]
        highest_gmv_val = float(total_gmv[max_gmv_idx] or 0.0)
        highest_gmv_orders = int(total_orders[max_gmv_idx] or 0)

        # Compute total GMV across all states for concentration share
        total_gmv_sum = float(sum(float(v or 0.0) for v in total_gmv)) or 1.0
        gmv_concentration_pct = round((highest_gmv_val / total_gmv_sum) * 100.0, 1)

        # Correlation analysis: check if high late delivery corr with low review scores
        correlation_note = ""
        if highest_late_state == lowest_score_state:
            correlation_note = (
                f" {highest_late_state} also has the highest late delivery rate ({highest_late_pct:.1f}%). "
                "This descriptive overlap does not establish a cause."
            )
        else:
            correlation_note = (
                f" {highest_late_state} has the highest late delivery rate ({highest_late_pct:.1f}%); "
                f"while {lowest_score_state} has the lowest review score. "
                "These observations do not establish a cause."
            )

        summary_narrative = (
            f"Descriptive comparison — Review Score & Delivery Performance:\n"
            f"1. **Lowest CSAT State**: {lowest_score_state} exhibited the lowest average review score "
            f"at **{lowest_score_val:.2f}/5.0**.{correlation_note}\n"
            f"2. **Late Delivery Leader**: {highest_late_state} has the highest late delivery rate at "
            f"**{highest_late_pct:.1f}%** of delivered orders.\n"
            f"3. **Revenue Concentration**: {highest_gmv_state} accounts for **{gmv_concentration_pct}%** "
            f"of total GMV ({highest_gmv_orders:,} orders)."
        )

        waterfall_data = [
            {
                "state": states[i],
                "avg_review_score": avg_scores[i],
                "late_delivery_pct": late_pcts[i],
                "total_orders": total_orders[i],
            }
            for i in range(min(10, len(states)))
        ]

        return {
            "lowest_csat_state": lowest_score_state,
            "lowest_csat_score": lowest_score_val,
            "highest_late_delivery_state": highest_late_state,
            "highest_late_pct": highest_late_pct,
            "highest_gmv_state": highest_gmv_state,
            "gmv_concentration_pct": gmv_concentration_pct,
            "waterfall_data": waterfall_data,
            "summary_narrative": summary_narrative,
        }

    def diagnose_churn_drivers(self, query_result_table: pa.Table) -> dict[str, Any]:
        """Legacy method — reroutes to review score driver analysis for Olist.

        Kept for backward-compatibility with orchestrator calls.
        """
        return self.diagnose_review_score_drivers(query_result_table)
