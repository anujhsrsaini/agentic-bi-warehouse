"""Triage & Intent Router Agent.

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

        # 1. Ambiguity Check (e.g. "show revenue", "what is our revenue")
        if q in ["show revenue", "revenue", "what is our revenue", "show me revenue", "give me revenue"]:
            state.intent = UserIntent.CLARIFICATION_REQUIRED
            state.confidence = 0.50
            state.clarification_prompt = (
                "The term 'revenue' has multiple certified accounting definitions at this company. "
                "Which definition would you like to see?"
            )
            state.clarification_options = [
                "1. Annual Recurring Revenue (ARR): Annualized value of active subscriptions (MRR * 12)",
                "2. Monthly Recurring Revenue (MRR): Current monthly contracted subscription run-rate",
                "3. Invoiced Cash Collected: Total cash collected from paid customer invoices",
            ]
            return state

        # 2. Diagnostic "Why" Analytics Check
        if q.startswith("why ") or "reason for" in q or "explain the drop" in q or "explain the spike" in q or "root cause" in q:
            state.intent = UserIntent.DIAGNOSTIC_WHY
            state.confidence = 0.95
            state.metric_name = self._extract_metric_name(q) or "logo_churn_rate"
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
        # Direct check on registered metrics and synonyms
        for metric in self.semantic_config.metrics:
            if metric.name in text:
                return metric.name
            for syn in metric.synonyms:
                if syn in text:
                    return metric.name
        return None

    def _extract_dimensions(self, text: str) -> list[str]:
        """Extract requested dimensions (industry, tier, country, etc.)."""
        dims = []
        if any(w in text for w in ["industry", "vertical", "sector"]):
            dims.append("industry")
        if any(w in text for w in ["tier", "segment", "company tier"]):
            dims.append("company_tier")
        if any(w in text for w in ["country", "region", "geography"]):
            dims.append("country")
        if any(w in text for w in ["movement", "movement type"]):
            dims.append("movement_type")
        return dims
