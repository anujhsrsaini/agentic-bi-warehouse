"""Structured output schemas for LangChain/Sarvam nodes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.agents.state import UserIntent


class IntentRouteOutput(BaseModel):
    intent: UserIntent
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    metric_name: str | None = None
    dimensions: list[str] = Field(default_factory=list)
    clarification_prompt: str | None = None
    clarification_options: list[str] = Field(default_factory=list)
    rationale: str = ""


class SQLGenerationOutput(BaseModel):
    sql: str
    rationale: str = ""
    certified_metric: str | None = None
    dimensions: list[str] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)


class SQLRepairOutput(BaseModel):
    sql: str
    rationale: str = ""


class NarrativeOutput(BaseModel):
    summary_narrative: str
