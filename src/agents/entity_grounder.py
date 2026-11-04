"""3-Tier Categorical Entity Grounder (CHESS + Defog Pattern).

Bridges the colloquial user language gap to exact database keys:
- Tier 1: Cached Enum Dictionary (Startup, Mid-Market, Enterprise, Healthcare, etc.)
- Tier 2: Trigram & Fuzzy Matcher (Jaro-Winkler / Levenshtein)
- Tier 3: Synonym & Acronym Dictionary
"""

from __future__ import annotations

import difflib
from typing import Any


class CategoricalEntityGrounder:
    """Grounds user natural language mentions to exact categorical database values."""

    # Pre-indexed categorical values from data/seed
    ENUM_REGISTRY: dict[str, dict[str, list[str]]] = {
        "dim_customers": {
            "industry": ["Healthcare", "Fintech", "DevTools", "E-commerce", "Cybersecurity", "EdTech"],
            "company_tier": ["Startup", "Mid-Market", "Enterprise"],
            "country": ["USA", "GBR", "DEU", "FRA", "CAN", "IND", "AUS", "SGP"],
        },
        "dim_plans": {
            "tier": ["Free", "Basic", "Pro", "Enterprise", "Scale"],
            "billing_interval": ["monthly", "annual"],
        },
        "fct_subscriptions": {
            "status": ["active", "canceled", "past_due", "paused"],
        },
        "fct_invoices": {
            "status": ["paid", "open", "void", "uncollectible"],
        },
        "fct_mrr_movements": {
            "movement_type": ["new", "expansion", "contraction", "churn"],
        },
    }

    SYNONYM_MAP: dict[str, tuple[str, str, str]] = {
        # mention -> (table, column, canonical_value)
        "us": ("dim_customers", "country", "USA"),
        "usa": ("dim_customers", "country", "USA"),
        "united states": ("dim_customers", "country", "USA"),
        "uk": ("dim_customers", "country", "GBR"),
        "britain": ("dim_customers", "country", "GBR"),
        "germany": ("dim_customers", "country", "DEU"),
        "france": ("dim_customers", "country", "FRA"),
        "india": ("dim_customers", "country", "IND"),
        "canada": ("dim_customers", "country", "CAN"),
        
        "enterprise": ("dim_customers", "company_tier", "Enterprise"),
        "mid-market": ("dim_customers", "company_tier", "Mid-Market"),
        "midmarket": ("dim_customers", "company_tier", "Mid-Market"),
        "startups": ("dim_customers", "company_tier", "Startup"),
        "startup": ("dim_customers", "company_tier", "Startup"),
        
        "health": ("dim_customers", "industry", "Healthcare"),
        "healthcare": ("dim_customers", "industry", "Healthcare"),
        "finance": ("dim_customers", "industry", "Fintech"),
        "fintech": ("dim_customers", "industry", "Fintech"),
        "devtools": ("dim_customers", "industry", "DevTools"),
        "dev": ("dim_customers", "industry", "DevTools"),
        "security": ("dim_customers", "industry", "Cybersecurity"),
        "cyber": ("dim_customers", "industry", "Cybersecurity"),
        "ecommerce": ("dim_customers", "industry", "E-commerce"),
        "e-commerce": ("dim_customers", "industry", "E-commerce"),
        "education": ("dim_customers", "industry", "EdTech"),
        "edtech": ("dim_customers", "industry", "EdTech"),
        
        "active": ("fct_subscriptions", "status", "active"),
        "churned": ("fct_subscriptions", "status", "canceled"),
        "cancelled": ("fct_subscriptions", "status", "canceled"),
        "canceled": ("fct_subscriptions", "status", "canceled"),
    }

    def ground_entities(self, text: str) -> list[tuple[str, str, str, float]]:
        """Identify entities in user text and ground them to (table, column, canonical_value, confidence)."""
        tokens = [t.strip("?,.!'\"").lower() for t in text.split()]
        matches = []

        # 1. Check Synonym Map (Tier 3)
        for token in tokens:
            if token in self.SYNONYM_MAP:
                tbl, col, val = self.SYNONYM_MAP[token]
                matches.append((tbl, col, val, 1.0))

        # Check multi-word synonyms e.g. "united states"
        text_lower = text.lower()
        for phrase, (tbl, col, val) in self.SYNONYM_MAP.items():
            if " " in phrase and phrase in text_lower:
                matches.append((tbl, col, val, 1.0))

        # 2. Check Fuzzy Trigram Matcher across Enum Registry (Tier 2)
        text_lower = text.lower()
        skip_billing_interval = ("monthly recurring revenue" in text_lower) or ("mrr" in text_lower)

        for tbl, cols in self.ENUM_REGISTRY.items():
            for col, allowed_vals in cols.items():
                if col == "billing_interval" and skip_billing_interval:
                    continue
                for token in tokens:
                    if len(token) < 3:
                        continue
                    close = difflib.get_close_matches(token, [v.lower() for v in allowed_vals], n=1, cutoff=0.78)
                    if close:
                        # Find original case
                        for orig in allowed_vals:
                            if orig.lower() == close[0]:
                                if not any(m[2] == orig for m in matches):
                                    matches.append((tbl, col, orig, 0.88))

        return matches
