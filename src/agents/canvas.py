"""Conversational Canvas & Grammar-of-Graphics Visualization Router.

Translates tabular query outputs into:
1. Executive Narrative & KPI Badges
2. Automated Vega-Lite v5 JSON Chart Specifications (Wilkinson Grammar of Graphics)
3. Interactive Contextual Action Chips
"""

from __future__ import annotations

from typing import Any
import pyarrow as pa
from src.agents.state import AgenticBIState


class VisualCanvasAgent:
    """Builds executive narratives and Vega-Lite chart specifications."""

    _CURRENCY_TOKENS = ("gmv", "aov", "price", "payment", "freight", "revenue", "arr", "mrr", "sales")
    _RATE_TOKENS = ("pct", "rate", "ratio", "percent")
    _SCORE_TOKENS = ("score", "rating", "csat", "days", "installment")

    @classmethod
    def _format_metric_value(cls, metric_col: str, value: Any) -> str:
        """Format a metric value consistently (currency, rate, score, or count)."""
        if value is None:
            return "—"
        if not isinstance(value, (int, float)):
            return str(value)
        key = metric_col.lower()
        if any(t in key for t in cls._RATE_TOKENS):
            return f"{value:,.2f}%"
        if any(t in key for t in cls._SCORE_TOKENS):
            return f"{value:,.2f}"
        if any(t in key for t in cls._CURRENCY_TOKENS):
            return f"R$ {value:,.2f}"
        if isinstance(value, int) or float(value).is_integer():
            return f"{int(value):,}"
        return f"{value:,.2f}"

    def synthesize(self, state: AgenticBIState) -> AgenticBIState:
        """Synthesize narrative, chart spec, and action chips."""
        res = state.execution_result
        if not res or len(res.data) == 0:
            state.summary_narrative = "No records matched the specified criteria."
            return state

        pydict = res.to_pylist()
        col_names = res.column_names

        # 1. Generate Executive Narrative Summary
        state.summary_narrative = self._generate_narrative(state, pydict, col_names)

        # 2. Build Vega-Lite Chart Specification
        state.chart_spec = self._build_vega_lite_spec(pydict, col_names, state.metric_name)

        return state

    def _generate_narrative(self, state: AgenticBIState, rows: list[dict[str, Any]], cols: list[str]) -> str:
        """Construct executive business commentary."""
        n_rows = len(rows)
        metric_col = cols[-1]

        # Check if single scalar metric
        if n_rows == 1 and len(cols) == 1:
            val = rows[0][metric_col]
            if val is None:
                return f"No value is available for **{metric_col}** with the selected criteria."
            formatted_val = f"{val:,.2f}" if isinstance(val, float) else str(val)
            return f"**{metric_col.upper()}**: **{formatted_val}** for the selected criteria."

        dim_col = cols[0]

        # Check if New vs Repeat customer count split
        if "new_customers" in cols and "repeat_customers" in cols:
            peak = max(rows, key=lambda r: r.get("total_customers") or 0)
            grain_label = "Daily" if "date" in dim_col or "day" in dim_col else "Monthly"
            return (
                f"**{grain_label} New vs Repeat Customer Count Split** across {n_rows} intervals:\n"
                f"- **Peak Interval**: **{peak.get(dim_col)}**\n"
                f"- **New Customers**: **{self._format_metric_value('new_customers', peak.get('new_customers'))}**\n"
                f"- **Repeat Customers**: **{self._format_metric_value('repeat_customers', peak.get('repeat_customers'))}**\n"
                f"- **Total Customers**: **{self._format_metric_value('total_customers', peak.get('total_customers'))}**"
            )

        # Check if New vs Repeat cohort analysis
        if "new_customer_gmv" in cols and "repeat_customer_gmv" in cols:
            total_new = sum(r.get("new_customer_gmv", 0) for r in rows if isinstance(r.get("new_customer_gmv"), (int, float)))
            total_rep = sum(r.get("repeat_customer_gmv", 0) for r in rows if isinstance(r.get("repeat_customer_gmv"), (int, float)))
            total_all = total_new + total_rep
            rep_pct = (total_rep / total_all * 100.0) if total_all > 0 else 0
            new_pct = 100.0 - rep_pct

            grain_label = "Daily" if "date" in dim_col or "day" in dim_col else "Monthly"
            return (
                f"**{grain_label} New vs Repeat Customer GMV Breakdown** across {n_rows} days:\n"
                f"- **New Customer GMV**: **R$ {total_new:,.2f}** ({new_pct:.1f}% of total)\n"
                f"- **Repeat Customer GMV**: **R$ {total_rep:,.2f}** ({rep_pct:.1f}% of total)\n"
                f"- **Total Period GMV**: **R$ {total_all:,.2f}**"
            )

        # Check if temporal time-series dimension
        if dim_col in ("order_date", "order_month", "order_week", "order_year", "day", "date", "month"):
            total_val = sum(r[metric_col] for r in rows if isinstance(r.get(metric_col), (int, float)))
            avg_val = total_val / len(rows) if len(rows) > 0 else 0
            sorted_by_val = sorted(rows, key=lambda r: r.get(metric_col) if isinstance(r.get(metric_col), (int, float)) else 0, reverse=True)
            peak_row = sorted_by_val[0]
            grain_label = "Daily" if "date" in dim_col or "day" in dim_col else "Monthly"
            
            return (
                f"**{grain_label} {metric_col.upper()} Trend** across {n_rows} intervals:\n"
                f"- **Total Period {metric_col.upper()}**: **{self._format_metric_value(metric_col, total_val)}** "
                f"(Average **{self._format_metric_value(metric_col, avg_val)}** per interval).\n"
                f"- **Peak Volume**: **{peak_row[dim_col]}** reached "
                f"**{self._format_metric_value(metric_col, peak_row[metric_col])}**."
            )

        # Categorical grouped summary
        top_row = rows[0]
        top_dim = top_row[dim_col]
        top_val = top_row[metric_col]

        formatted_val = f"{top_val:,.2f}" if isinstance(top_val, float) else str(top_val) if top_val is not None else "unavailable"

        narrative = (
            f"Analysis of **{metric_col.upper()}** grouped by **{dim_col}** across {n_rows} segments:\n"
            f"- **Top Performer**: **{top_dim}** leads with **{formatted_val}**.\n"
        )
        if n_rows > 1:
            second_row = rows[1]
            second_val = second_row[metric_col]
            formatted_second = f"{second_val:,.2f}" if isinstance(second_val, float) else str(second_val) if second_val is not None else "unavailable"
            narrative += f"- **Runner-Up**: **{second_row[dim_col]}** follows with **{formatted_second}**.\n"

        return narrative.strip()

    def _build_vega_lite_spec(self, rows: list[dict[str, Any]], cols: list[str], metric_name: str | None) -> dict[str, Any] | None:
        """Determine optimal Vega-Lite chart type based on column dimensionality."""
        if len(cols) < 2 or len(rows) == 0:
            return None

        dim_col = cols[0]
        metric_col = cols[-1]

        # If 2 columns: Categorical x Numeric -> Horizontal or Vertical Bar
        if len(cols) == 2:
            return {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "title": f"{metric_col.replace('_', ' ').title()} by {dim_col.replace('_', ' ').title()}",
                "data": {"values": rows[:20]},
                "mark": {"type": "bar", "cornerRadiusEnd": 4, "tooltip": True},
                "encoding": {
                    "y": {"field": dim_col, "type": "nominal", "sort": "-x", "title": dim_col.replace("_", " ").title()},
                    "x": {"field": metric_col, "type": "quantitative", "title": metric_col.replace("_", " ").title()},
                    "color": {"value": "#4F46E5"},
                },
            }

        # If 3 columns (e.g. industry, tier, arr) -> Grouped Bar Chart
        if len(cols) >= 3:
            dim_col2 = cols[1]
            return {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "title": f"{metric_col.replace('_', ' ').title()} by {dim_col.title()} and {dim_col2.title()}",
                "data": {"values": rows[:30]},
                "mark": {"type": "bar", "tooltip": True},
                "encoding": {
                    "x": {"field": dim_col, "type": "nominal", "title": dim_col.title()},
                    "y": {"field": metric_col, "type": "quantitative", "title": metric_col.title()},
                    "color": {"field": dim_col2, "type": "nominal", "title": dim_col2.title()},
                    "xOffset": {"field": dim_col2},
                },
            }

        return None
