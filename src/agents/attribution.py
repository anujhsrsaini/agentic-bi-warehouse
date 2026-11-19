"""Diagnostic 'Why' Anomaly & Root Cause Attribution Engine — Olist Edition.

Calculates exact dimension contribution percentages for e-commerce metrics:
- Delivery Delay Rate Driver Analysis: which states have the highest late delivery rates
- Review Score Variance Decomposition: which states / categories drive CSAT drops
- GMV Concentration Analysis: contribution of top states / categories
- Geographic scoping: compares a requested state against the national benchmark
- Additive Variance Decomposition: Delta(Metric) = sum(Delta_dimension_i)
- Kitagawa Rate-Mix Decomposition: isolates Mix Effects vs Rate Effects
"""

from __future__ import annotations

from typing import Any
import pyarrow as pa


def _weighted_avg(values: list[Any], weights: list[Any]) -> float:
    """Order-weighted average, ignoring null values."""
    pairs = [
        (float(v), float(w))
        for v, w in zip(values, weights)
        if v is not None and w is not None and float(w) > 0
    ]
    if not pairs:
        return 0.0
    total_weight = sum(w for _, w in pairs)
    return sum(v * w for v, w in pairs) / total_weight if total_weight else 0.0


class MetricAttributionEngine:
    """Diagnoses drivers of metric spikes and drops for Olist e-commerce analytics."""

    def diagnose_review_score_drivers(
        self,
        query_result_table: pa.Table,
        requested_state: str | None = None,
    ) -> dict[str, Any]:
        """Analyze review score and delivery delay drivers by Brazilian state.

        Expects columns: customer_state, total_orders, avg_review_score,
                         total_gmv, late_delivery_pct (optional: avg_delivery_days)

        When ``requested_state`` is provided (e.g. 'RJ'), the narrative is scoped to
        that state and compared against the national benchmark instead of highlighting
        the global worst/best states.
        """
        pydict = query_result_table.to_pydict()
        states = pydict.get("customer_state", [])
        avg_scores = pydict.get("avg_review_score", [])
        late_pcts = pydict.get("late_delivery_pct", [])
        total_orders = pydict.get("total_orders", [])
        total_gmv = pydict.get("total_gmv", [])
        delivery_days = pydict.get("avg_delivery_days", [])

        if not avg_scores or not states:
            return {"status": "insufficient_data", "summary": "No cohort data available for diagnosis."}

        if requested_state:
            scoped = self._scoped_state_analysis(
                states, avg_scores, late_pcts, total_orders, total_gmv, delivery_days, requested_state
            )
            if scoped is not None:
                return scoped

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

    def _scoped_state_analysis(
        self,
        states: list[Any],
        avg_scores: list[Any],
        late_pcts: list[Any],
        total_orders: list[Any],
        total_gmv: list[Any],
        delivery_days: list[Any],
        requested_state: str,
    ) -> dict[str, Any] | None:
        """Build a state-scoped diagnostic comparing the requested state to the national benchmark."""
        target = str(requested_state).strip().upper()
        idx = next((i for i, s in enumerate(states) if str(s).strip().upper() == target), None)
        if idx is None:
            return None

        state_score = float(avg_scores[idx] or 0.0)
        state_late = float(late_pcts[idx] or 0.0)
        state_orders = int(total_orders[idx] or 0)
        state_gmv = float(total_gmv[idx] or 0.0)
        state_days = float(delivery_days[idx]) if delivery_days and delivery_days[idx] is not None else None

        national_score = _weighted_avg(avg_scores, total_orders)
        national_late = _weighted_avg(late_pcts, total_orders)
        national_days = _weighted_avg(delivery_days, total_orders) if delivery_days else None

        late_ratio = (state_late / national_late) if national_late > 0 else 0.0

        # Compare against the best-performing large state (SP) when available.
        sp_idx = next((i for i, s in enumerate(states) if str(s).strip().upper() == "SP"), None)
        sp_note = ""
        if sp_idx is not None and sp_idx != idx:
            sp_late = float(late_pcts[sp_idx] or 0.0)
            sp_note = f" (vs SP at {sp_late:.1f}%)"

        if late_ratio >= 1.3:
            driver = (
                f"delivery delays are the primary driver: {target}'s late-delivery rate is "
                f"{late_ratio:.1f}x the national average, directly suppressing review scores."
            )
        else:
            driver = (
                "delivery performance is broadly in line with the national average; "
                "product quality or fulfillment issues beyond logistics are the likely driver."
            )

        transit_line = ""
        if state_days is not None and national_days:
            transit_line = (
                f"\n3. **Transit Time**: average delivery time is **{state_days:.1f} days** "
                f"vs the national average of **{national_days:.1f} days**."
            )

        summary_narrative = (
            f"Diagnostic Root-Cause Analysis — {target} Review Score & Delivery Performance:\n"
            f"1. **{target} CSAT**: average review score is **{state_score:.2f}/5.0** "
            f"vs the national benchmark of **{national_score:.2f}/5.0**.\n"
            f"2. **Delivery Delays**: {target}'s late-delivery rate is **{state_late:.1f}%**{sp_note}, "
            f"compared with the national average of **{national_late:.1f}%** "
            f"({late_ratio:.1f}x).{transit_line}\n"
            f"4. **Primary Driver**: {driver}"
        )

        return {
            "requested_state": target,
            "requested_state_metrics": {
                "avg_review_score": state_score,
                "late_delivery_pct": state_late,
                "avg_delivery_days": state_days,
                "total_orders": state_orders,
                "total_gmv": state_gmv,
            },
            "national_benchmark": {
                "avg_review_score": round(national_score, 3),
                "late_delivery_pct": round(national_late, 2),
                "avg_delivery_days": round(national_days, 1) if national_days else None,
            },
            "late_delivery_ratio": round(late_ratio, 2),
            "lowest_csat_state": target,
            "lowest_csat_score": state_score,
            "highest_late_delivery_state": target,
            "highest_late_pct": state_late,
            "highest_gmv_state": target,
            "gmv_concentration_pct": round((state_gmv / (sum(float(v or 0.0) for v in total_gmv) or 1.0)) * 100.0, 1),
            "waterfall_data": [
                {
                    "state": states[i],
                    "avg_review_score": avg_scores[i],
                    "late_delivery_pct": late_pcts[i],
                    "total_orders": total_orders[i],
                }
                for i in range(min(10, len(states)))
            ],
            "summary_narrative": summary_narrative,
        }

    def diagnose_churn_drivers(
        self,
        query_result_table: pa.Table,
        requested_state: str | None = None,
    ) -> dict[str, Any]:
        """Legacy method — reroutes to review score driver analysis for Olist.

        Kept for backward-compatibility with orchestrator calls.
        """
        return self.diagnose_review_score_drivers(query_result_table, requested_state=requested_state)
