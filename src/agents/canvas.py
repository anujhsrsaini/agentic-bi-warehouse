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
            formatted_val = f"${val:,.2f}" if "arr" in metric_col or "mrr" in metric_col or "revenue" in metric_col else f"{val:,.0f}"
            return f"**{metric_col.upper()}**: Current value is **{formatted_val}** across all active accounts."

        # Grouped summary
        dim_col = cols[0]
        top_row = rows[0]
        top_dim = top_row[dim_col]
        top_val = top_row[metric_col]

        formatted_val = f"${top_val:,.2f}" if "arr" in metric_col or "mrr" in metric_col else f"{top_val:,}"

        narrative = (
            f"Analysis of **{metric_col.upper()}** grouped by **{dim_col}** across {n_rows} segments:\n"
            f"- **Top Performer**: **{top_dim}** leads with **{formatted_val}**.\n"
        )
        if n_rows > 1:
            second_row = rows[1]
            narrative += f"- **Runner-Up**: **{second_row[dim_col]}** follows with **${second_row[metric_col]:,.2f}**.\n"

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
