"""State container for Agentic BI multi-agent cognitive loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from src.engine.connectors.base import QueryResult


class UserIntent(str, Enum):
    """Classified user question intent."""
    CERTIFIED_METRIC = "CERTIFIED_METRIC"
    EXPLORATORY_SQL = "EXPLORATORY_SQL"
    DIAGNOSTIC_WHY = "DIAGNOSTIC_WHY"
    SCHEMA_METADATA = "SCHEMA_METADATA"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"


@dataclass
class AgenticBIState:
    """Immutable state container passed across the multi-agent graph."""
    question: str
    session_id: str = "default-session"
    
    # Stage 1: Router
    intent: UserIntent = UserIntent.CERTIFIED_METRIC
    confidence: float = 1.0
    clarification_options: list[str] = field(default_factory=list)
    clarification_prompt: str | None = None

    # Stage 2: Semantic Linker & Grounder
    metric_name: str | None = None
    dimensions: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    grounded_entities: dict[str, Any] = field(default_factory=dict)

    # Stage 3: SQL Generator
    raw_sql: str = ""
    sql_rationale: str = ""

    # Stage 4: AST Guardrail
    validated_sql: str = ""
    validation_time_us: float = 0.0
    security_passed: bool = False
    security_error: str | None = None

    # Stage 5: Execution & Self-Healing
    execution_result: QueryResult | None = None
    execution_error: str | None = None
    retry_count: int = 0
    error_history: list[str] = field(default_factory=list)

    # Stage 6: Insights, Lineage & Canvas
    summary_narrative: str = ""
    lineage_mermaid: str = ""
    lineage_ascii: str = ""
    chart_spec: dict[str, Any] | None = None
    diagnostic_attribution: dict[str, Any] | None = None
