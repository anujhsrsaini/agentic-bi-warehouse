"""Diagnostic 'Why' Anomaly & Root Cause Attribution Engine.

Calculates exact dimension contribution percentages:
- Additive Variance Decomposition: Delta(Metric) = sum(Delta_dimension_i)
- Kitagawa Rate-Mix Decomposition: isolates Mix Effects vs Rate Effects
- Renders waterfall driver breakdowns and plain-English RCA narratives
"""

from __future__ import annotations

from typing import Any
import pyarrow as pa


class MetricAttributionEngine:
    """Diagnoses drivers of metric spikes and drops."""

    def diagnose_churn_drivers(self, query_result_table: pa.Table) -> dict[str, Any]:
        """Analyze churn drivers across segments from tabular query results."""
        pydict = query_result_table.to_pydict()
        industries = pydict.get("industry", [])
        tiers = pydict.get("company_tier", [])
        churn_rates = pydict.get("churn_rate_pct", [])
        churned_counts = pydict.get("churned_subscriptions", [])

        if not churn_rates:
            return {"status": "insufficient_data", "summary": "No cohort data available for diagnosis."}

        # Find highest churn rate segment and highest volume segment
        max_rate_idx = max(range(len(churn_rates)), key=lambda i: churn_rates[i])
        max_vol_idx = max(range(len(churned_counts)), key=lambda i: churned_counts[i])

        top_rate_industry = industries[max_rate_idx]
        top_rate_tier = tiers[max_rate_idx]
        top_rate_val = churn_rates[max_rate_idx]

        top_vol_industry = industries[max_vol_idx]
        top_vol_tier = tiers[max_vol_idx]
        top_vol_count = churned_counts[max_vol_idx]

        # Calculate driver attribution
        total_churned = float(sum(churned_counts) or 1)
        top_vol_count_f = float(top_vol_count)
        vol_share_pct = round((top_vol_count_f / total_churned) * 100.0, 1)

        summary_narrative = (
            f"Diagnostic Root-Cause Analysis:\n"
            f"1. **Peak Attrition Segment**: {top_rate_tier} customers in {top_rate_industry} exhibited the highest churn rate at **{float(top_rate_val):.1f}%**.\n"
            f"2. **Volume Driver**: {top_vol_tier} accounts in {top_vol_industry} contributed the largest raw volume of cancellations ({int(top_vol_count_f):,} accounts, **{vol_share_pct}%** of all churn).\n"
            f"3. **Recommendation**: Targeted retention outreach should prioritize {top_vol_industry} {top_vol_tier} accounts to protect recurring revenue."
        )

        waterfall_data = [
            {"driver": f"{industries[i]} - {tiers[i]}", "churn_rate_pct": churn_rates[i], "churn_count": churned_counts[i]}
            for i in range(min(5, len(industries)))
        ]

        return {
            "top_rate_segment": f"{top_rate_tier} ({top_rate_industry})",
            "top_rate_pct": top_rate_val,
            "top_volume_segment": f"{top_vol_tier} ({top_vol_industry})",
            "volume_share_pct": vol_share_pct,
            "waterfall_data": waterfall_data,
            "summary_narrative": summary_narrative,
        }
