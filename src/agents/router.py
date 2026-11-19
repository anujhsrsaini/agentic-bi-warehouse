"""Triage & Intent Router Agent — Olist Brazilian E-Commerce Edition.

Classifies question intent, scores confidence, and proactively prompts
for disambiguation when user intent is ambiguous without guessing blindly.
"""

from __future__ import annotations

import re
from src.agents.state import AgenticBIState, UserIntent
from src.core.config import settings
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

        # 2. Diagnostic "Why" Analytics & Correlations — Root-cause attribution
        _diag_triggers = ["why ", "reason for", "explain the drop", "explain the spike",
                          "root cause", "what caused", "what's driving", "diagnose", "correlation"]
        if any(t in q for t in _diag_triggers):
            state.intent = UserIntent.DIAGNOSTIC_WHY
            state.confidence = 0.95
            state.metric_name = self._extract_metric_name(q) or "avg_review_score"
            self._apply_common_extractions(state, q)
            return state

        # Multi-metric / exploratory combinations & cohort analytics
        if any(t in q for t in ["new vs repeat", "repeat vs new", "new vs returning", "repeat customer", "new customer", "first time vs returning", "retention"]):
            state.intent = UserIntent.EXPLORATORY_SQL
            state.confidence = 0.96
            state.metric_name = "gmv"
            state.dimensions = self._extract_dimensions(q)
            self._apply_common_extractions(state, q)
            return state

        if ("top" in q and ("latency" in q or "delay" in q)) or ("shipping delay" in q or "longest shipping" in q):
            state.intent = UserIntent.EXPLORATORY_SQL
            state.confidence = 0.94
            self._apply_common_extractions(state, q)
            return state

        # 3. Certified Metric Check
        matched_metric = self._extract_metric_name(q)
        if matched_metric:
            state.intent = UserIntent.CERTIFIED_METRIC
            state.confidence = 0.98
            state.metric_name = matched_metric
            state.dimensions = self._extract_dimensions(q)
            self._apply_common_extractions(state, q)
            return state

        # 4. Exploratory SQL Fallback
        state.intent = UserIntent.EXPLORATORY_SQL
        state.confidence = 0.85
        self._apply_common_extractions(state, q)
        return state

    def _apply_common_extractions(self, state: AgenticBIState, text: str) -> None:
        """Deterministically extract limit, ordering, and time filters from text."""
        extracted_limit = self._extract_limit(text)
        if extracted_limit is not None:
            state.limit = extracted_limit
        if self._extract_order_ascending(text):
            state.order_ascending = True
        t_filter = self._extract_time_filter(text)
        if t_filter and t_filter not in state.filters:
            state.filters.append(t_filter)

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

    def _extract_limit(self, text: str) -> int | None:
        """Extract a user-specified row limit (e.g. 'Top 10', 'limit 5', 'bottom 3')."""
        m = re.search(r"\b(?:top|bottom|first|limit)\s+(\d+)\b", text)
        if not m:
            return None
        try:
            n = int(m.group(1))
        except ValueError:
            return None
        if n <= 0:
            return None
        return min(n, settings.max_query_limit)

    def _extract_order_ascending(self, text: str) -> bool:
        """Detect ascending-order intent ('lowest', 'worst', 'bottom', 'least')."""
        cleaned = text.replace("at least", "")
        return bool(re.search(r"\b(lowest|worst|bottom|least|smallest|fewest)\b", cleaned))

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
        # Temporal grains
        if any(w in text for w in ["daywise", "daily", "by day", "day by day", "per day", "datewise", "by date"]):
            dims.append("order_date")
        elif any(w in text for w in ["monthwise", "monthly", "by month", "per month"]):
            dims.append("order_month")
        elif any(w in text for w in ["weekly", "by week", "per week", "weekwise"]):
            dims.append("order_week")
        elif any(w in text for w in ["yearly", "yearwise", "by year", "annual", "annually"]):
            dims.append("order_year")
        elif any(w in text for w in ["trend", "over time", "timeline", "trajectory"]):
            dims.append("order_month")

        # Match customer_state using whole words / tokens to prevent false positives on words like "split", "speed", etc.
        tokens = set(re.findall(r"\b[a-z0-9_]+\b", text))
        state_triggers = {"state", "states", "region", "regions", "sp", "rj", "mg", "rs", "pr", "sc", "ba", "df", "go", "es", "pe", "ce", "pa"}
        mentions_seller = any(w in text for w in ["seller", "sellers"])
        mentions_customer = any(w in text for w in ["customer", "customers", "buyer", "buyers"])
        if mentions_seller:
            dims.append("seller_state")
        if tokens & state_triggers and (mentions_customer or not mentions_seller):
            dims.append("customer_state")
        if any(w in text for w in ["category", "categories", "product category", "product type"]):
            dims.append("product_category_name")
        if any(has(w) for w in ["payment", "payment type", "payment method"]):
            dims.append("payment_type")
        if any(has(w) for w in ["seller", "seller state", "seller region"]):
            dims.append("seller_state")
        if any(has(w) for w in ["status", "order status"]):
            dims.append("order_status")
        return dims

    def _extract_time_filter(self, text: str) -> str | None:
        """Extract relative time windows (e.g. 'last 2 months', 'last 30 days')."""
        # Match 'last N month(s)'
        m_month = re.search(r"last\s+(\d+)\s+month", text)
        if m_month:
            n = int(m_month.group(1))
            return f"orders.order_purchase_timestamp >= (SELECT MAX(order_purchase_timestamp) - INTERVAL {n} MONTH FROM orders WHERE order_status != 'canceled')"

        # Match 'last N day(s)'
        m_day = re.search(r"last\s+(\d+)\s+day", text)
        if m_day:
            n = int(m_day.group(1))
            return f"orders.order_purchase_timestamp >= (SELECT MAX(order_purchase_timestamp) - INTERVAL {n} DAY FROM orders WHERE order_status != 'canceled')"

        # Match 'last N week(s)'
        m_week = re.search(r"last\s+(\d+)\s+week", text)
        if m_week:
            n = int(m_week.group(1))
            return f"orders.order_purchase_timestamp >= (SELECT MAX(order_purchase_timestamp) - INTERVAL {n} WEEK FROM orders WHERE order_status != 'canceled')"

        # Match 'last N year(s)' or 'last year'
        if "last year" in text:
            return "orders.order_purchase_timestamp >= (SELECT MAX(order_purchase_timestamp) - INTERVAL 1 YEAR FROM orders WHERE order_status != 'canceled')"
        m_year = re.search(r"last\s+(\d+)\s+year", text)
        if m_year:
            n = int(m_year.group(1))
            return f"orders.order_purchase_timestamp >= (SELECT MAX(order_purchase_timestamp) - INTERVAL {n} YEAR FROM orders WHERE order_status != 'canceled')"

        # Match explicit calendar year (e.g. 'in 2018', 'for 2017', 'during 2018')
        m_cal_year = re.search(r"\b(19\d{2}|20\d{2})\b", text)
        if m_cal_year:
            yr = int(m_cal_year.group(1))
            return (
                f"orders.order_purchase_timestamp >= '{yr}-01-01' "
                f"AND orders.order_purchase_timestamp < '{yr + 1}-01-01'"
            )

        return None
