"""Pydantic v2 Models for Governed Semantic Layer."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class DimensionDefinition(BaseModel):
    name: str
    type: str
    column: str
    description: str | None = None
    synonyms: list[str] = Field(default_factory=list)


class MeasureDefinition(BaseModel):
    name: str
    expr: str
    agg: str = "sum"  # sum, count, avg, min, max, count_distinct
    description: str | None = None


class ForeignKeyDefinition(BaseModel):
    fk: str
    references: str  # e.g. "dim_customers.customer_id"
    relationship: str = "many_to_one"  # many_to_one, one_to_many, one_to_one


class SemanticModel(BaseModel):
    name: str
    table: str
    primary_key: str | None = None  # Optional for composite-keyed or junction tables
    dimensions: list[DimensionDefinition] = Field(default_factory=list)
    measures: list[MeasureDefinition] = Field(default_factory=list)
    foreign_keys: list[ForeignKeyDefinition] = Field(default_factory=list)


class MetricDefinition(BaseModel):
    name: str
    label: str
    description: str
    model: str
    calculation: str  # SQL formula
    filter: str | None = None
    dimensions: list[str] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)


class SemanticLayerConfig(BaseModel):
    version: str = "1.0"
    models: list[SemanticModel] = Field(default_factory=list)
    metrics: list[MetricDefinition] = Field(default_factory=list)

    def get_model(self, name: str) -> SemanticModel | None:
        for m in self.models:
            if m.name.lower() == name.lower():
                return m
        return None

    def get_metric(self, name: str) -> MetricDefinition | None:
        for met in self.metrics:
            if met.name.lower() == name.lower():
                return met
            if name.lower() in [s.lower() for s in met.synonyms]:
                return met
        return None
