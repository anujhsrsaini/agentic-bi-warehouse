"""Triage & Intent Router Agent — Olist Brazilian E-Commerce Edition.

Classifies question intent, scores confidence, and proactively prompts
for disambiguation when user intent is ambiguous without guessing blindly.
"""

from __future__ import annotations

import re
from src.agents.state import AgenticBIState, UserIntent
from src.semantic.loader import SemanticLayerLoader


class IntentRouterAgent:
    """Classifies user analytical queries and routes through the StateGraph."""

    def __init__(self):
        self.semantic_config = SemanticLayerLoader().load()

    def route(self, state: AgenticBIState) -> AgenticBIState:
        """Analyze question and update state with intent and parameters."""
        q = state.question.strip().lower()

        # 1. Ambiguity Check — "revenue" / "show revenue" is ambiguous in Olist context
        #    (GMV vs total_payment_value vs invoiced items)
        _revenue_triggers = {
            "show revenue", "revenue", "what is our revenue", "show me revenue",
            "give me revenue", "total revenue", "what is revenue",
        }
        if q in _revenue_triggers:
            state.intent = UserIntent.CLARIFICATION_REQUIRED
            state.confidence = 0.50
            state.clarification_prompt = (
                "The term 'revenue' has multiple interpretations for the Olist e-commerce dataset. "
                "GMV (item sales), Total Payments, or a state breakdown — which would you like?"
            )
            state.clarification_options = [
                "1. GMV (Gross Merchandise Value): Sum of product item prices, excluding freight",
                "2. Total Payment Value: All payments received (item price + freight + installments)",
                "3. GMV by State: Break down product revenue by Brazilian customer state",
            ]
            return state

        # 2. Diagnostic "Why" Analytics — Root-cause attribution
        _diag_triggers = ["why ", "reason for", "explain the drop", "explain the spike",
                          "root cause", "what caused", "what's driving", "diagnose"]
        if any(t in q for t in _diag_triggers):
            state.intent = UserIntent.DIAGNOSTIC_WHY
            state.confidence = 0.95
            state.metric_name = self._extract_metric_name(q) or "avg_review_score"
            return state

        # 3. Certified Metric Check
        matched_metric = self._extract_metric_name(q)
        if matched_metric:
            state.intent = UserIntent.CERTIFIED_METRIC
            state.confidence = 0.98
            state.metric_name = matched_metric
            state.dimensions = self._extract_dimensions(q)
            return state

        # 4. Exploratory SQL Fallback
        state.intent = UserIntent.EXPLORATORY_SQL
        state.confidence = 0.85
        return state

    def _extract_metric_name(self, text: str) -> str | None:
        """Extract certified metric name from text or synonyms."""
        # Prefer the most specific whole phrase: "freight to GMV" must not be
        # mistaken for the shorter "GMV" metric. Word boundaries also avoid
        # matches inside unrelated words.
        matches = []
        for metric in self.semantic_config.metrics:
            for phrase in (metric.name, *metric.synonyms):
                if re.search(r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)", text):
                    matches.append((len(phrase), metric.name))
        return max(matches, default=(0, None), key=lambda match: match[0])[1]

    def _extract_dimensions(self, text: str) -> list[str]:
        """Extract requested grouping dimensions from the question text."""
        grouping = re.search(r"\b(?:by|per|for each|grouped by|breakdown by|split by|across|across each)\b\s+(.+)", text)
        group_text = grouping.group(1) if grouping else ""

        def has(phrase: str) -> bool:
            pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
            if group_text and re.search(pattern, group_text):
                return True
            # Also match "{phrase} wise", "{phrase}-wise", or "{phrase} breakdown/split" anywhere in question
            wise_pattern = rf"\b{re.escape(phrase)}(?:s)?(?:[ -]?wise|\s+(?:breakdown|split|distribution))\b"
            return bool(re.search(wise_pattern, text))

        dims = []
        if any(has(w) for w in ["state", "region"]):
            dims.append("customer_state")
        if any(has(w) for w in ["category", "product category", "product type"]):
            dims.append("product_category_name")
        if any(has(w) for w in ["payment", "payment type", "payment method"]):
            dims.append("payment_type")
        if any(has(w) for w in ["seller", "seller state", "seller region"]):
            dims.append("seller_state")
        if any(has(w) for w in ["status", "order status"]):
            dims.append("order_status")
        return dims
