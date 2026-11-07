"""3-Tier Categorical Entity Grounder (CHESS + Defog Pattern) — Olist Edition.

Bridges the colloquial user language gap to exact database keys:
- Tier 1: Cached Enum Dictionary (SP, RJ, credit_card, delivered, etc.)
- Tier 2: Trigram & Fuzzy Matcher (Jaro-Winkler / Levenshtein)
- Tier 3: Synonym & Acronym Dictionary (Brazilian states, payment types, etc.)
"""

from __future__ import annotations

import difflib
from typing import Any


class CategoricalEntityGrounder:
    """Grounds user natural language mentions to exact categorical database values.

    Covers the full Olist Brazilian E-Commerce schema:
    - Brazilian state codes (SP, RJ, MG, …)
    - Payment types (credit_card, boleto, voucher, debit_card)
    - Order statuses (delivered, shipped, canceled, …)
    - Product category synonyms (electronics, furniture, etc.)
    """

    # Pre-indexed categorical values from data/seed Olist Parquet files
    ENUM_REGISTRY: dict[str, dict[str, list[str]]] = {
        "orders": {
            "order_status": [
                "delivered", "shipped", "canceled", "invoiced",
                "processing", "unavailable", "created", "approved",
            ],
        },
        "order_payments": {
            "payment_type": ["credit_card", "boleto", "voucher", "debit_card"],
        },
        "customers": {
            "customer_state": [
                "SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO", "ES", "PE",
                "CE", "PA", "MT", "MS", "RN", "MA", "PB", "PI", "AL", "SE",
                "RO", "TO", "AM", "AC", "AP", "RR", "DF",
            ],
        },
        "sellers": {
            "seller_state": [
                "SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO", "ES", "PE",
                "CE", "PA", "MT", "MS", "RN", "MA", "PB", "PI", "AL", "SE",
                "RO", "TO", "AM", "AC", "AP", "RR", "DF",
            ],
        },
    }

    # mention -> (table, column, canonical_value)
    SYNONYM_MAP: dict[str, tuple[str, str, str]] = {
        # ── Brazilian States ──────────────────────────────────────────────────
        "sp": ("customers", "customer_state", "SP"),
        "sao paulo": ("customers", "customer_state", "SP"),
        "são paulo": ("customers", "customer_state", "SP"),
        "saint paul": ("customers", "customer_state", "SP"),

        "rj": ("customers", "customer_state", "RJ"),
        "rio": ("customers", "customer_state", "RJ"),
        "rio de janeiro": ("customers", "customer_state", "RJ"),

        "mg": ("customers", "customer_state", "MG"),
        "minas gerais": ("customers", "customer_state", "MG"),
        "minas": ("customers", "customer_state", "MG"),

        "rs": ("customers", "customer_state", "RS"),
        "rio grande do sul": ("customers", "customer_state", "RS"),

        "pr": ("customers", "customer_state", "PR"),
        "parana": ("customers", "customer_state", "PR"),
        "paraná": ("customers", "customer_state", "PR"),

        "sc": ("customers", "customer_state", "SC"),
        "santa catarina": ("customers", "customer_state", "SC"),

        "ba": ("customers", "customer_state", "BA"),
        "bahia": ("customers", "customer_state", "BA"),

        "go": ("customers", "customer_state", "GO"),
        "goias": ("customers", "customer_state", "GO"),
        "goiás": ("customers", "customer_state", "GO"),

        "df": ("customers", "customer_state", "DF"),
        "brasilia": ("customers", "customer_state", "DF"),
        "brasília": ("customers", "customer_state", "DF"),
        "distrito federal": ("customers", "customer_state", "DF"),

        "pe": ("customers", "customer_state", "PE"),
        "pernambuco": ("customers", "customer_state", "PE"),

        "ce": ("customers", "customer_state", "CE"),
        "ceara": ("customers", "customer_state", "CE"),
        "ceará": ("customers", "customer_state", "CE"),

        "am": ("customers", "customer_state", "AM"),
        "amazonas": ("customers", "customer_state", "AM"),

        "pa": ("customers", "customer_state", "PA"),
        "para": ("customers", "customer_state", "PA"),
        "pará": ("customers", "customer_state", "PA"),

        # ── Payment Types ─────────────────────────────────────────────────────
        "credit card": ("order_payments", "payment_type", "credit_card"),
        "credit_card": ("order_payments", "payment_type", "credit_card"),
        "creditcard": ("order_payments", "payment_type", "credit_card"),
        "visa": ("order_payments", "payment_type", "credit_card"),
        "mastercard": ("order_payments", "payment_type", "credit_card"),

        "boleto": ("order_payments", "payment_type", "boleto"),
        "bank slip": ("order_payments", "payment_type", "boleto"),
        "billet": ("order_payments", "payment_type", "boleto"),

        "voucher": ("order_payments", "payment_type", "voucher"),
        "coupon": ("order_payments", "payment_type", "voucher"),
        "gift card": ("order_payments", "payment_type", "voucher"),
        "gift voucher": ("order_payments", "payment_type", "voucher"),

        "debit card": ("order_payments", "payment_type", "debit_card"),
        "debit_card": ("order_payments", "payment_type", "debit_card"),
        "debit": ("order_payments", "payment_type", "debit_card"),

        # ── Order Statuses ────────────────────────────────────────────────────
        "delivered": ("orders", "order_status", "delivered"),
        "completed": ("orders", "order_status", "delivered"),
        "fulfilled": ("orders", "order_status", "delivered"),

        "shipped": ("orders", "order_status", "shipped"),
        "in transit": ("orders", "order_status", "shipped"),
        "dispatched": ("orders", "order_status", "shipped"),

        "canceled": ("orders", "order_status", "canceled"),
        "cancelled": ("orders", "order_status", "canceled"),
        "cancellation": ("orders", "order_status", "canceled"),

        "invoiced": ("orders", "order_status", "invoiced"),
        "billed": ("orders", "order_status", "invoiced"),

        "processing": ("orders", "order_status", "processing"),
        "pending": ("orders", "order_status", "processing"),
    }

    def ground_entities(self, text: str) -> list[tuple[str, str, str, float]]:
        """Identify entities in user text and ground them to (table, column, canonical_value, confidence)."""
        tokens = [t.strip("?,.!'\"`").lower() for t in text.split()]
        matches: list[tuple[str, str, str, float]] = []
        seen_values: set[str] = set()
        text_lower = text.lower()

        # ── Tier 3: Synonym Map (single-token and multi-word) ─────────────────
        for token in tokens:
            if token in self.SYNONYM_MAP:
                tbl, col, val = self.SYNONYM_MAP[token]
                if val not in seen_values:
                    matches.append((tbl, col, val, 1.0))
                    seen_values.add(val)

        # Multi-word phrase check (e.g. "credit card", "rio de janeiro")
        for phrase, (tbl, col, val) in self.SYNONYM_MAP.items():
            if " " in phrase and phrase in text_lower:
                if val not in seen_values:
                    matches.append((tbl, col, val, 1.0))
                    seen_values.add(val)

        # ── Tier 2: Fuzzy Trigram Matcher across Enum Registry ────────────────
        # Skip overly-short tokens and avoid false payment_type matches on "mrr"
        skip_state_tokens = {"gmv", "aov", "csat", "otd", "mrr", "arr"}
        for tbl, cols in self.ENUM_REGISTRY.items():
            for col, allowed_vals in cols.items():
                for token in tokens:
                    if len(token) < 3 or token in skip_state_tokens:
                        continue
                    # Two-letter state codes are too short for safe fuzzy
                    # matching ("Rio" was previously misread as RO as well
                    # as its explicit RJ synonym). Exact codes still match
                    # through the synonym map above.
                    close = difflib.get_close_matches(
                        token, [v.lower() for v in allowed_vals if len(v) >= 3], n=1, cutoff=0.80
                    )
                    if close:
                        for orig in allowed_vals:
                            if orig.lower() == close[0] and orig not in seen_values:
                                matches.append((tbl, col, orig, 0.88))
                                seen_values.add(orig)

        return matches
