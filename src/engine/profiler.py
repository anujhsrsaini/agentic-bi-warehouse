"""Microsecond Execution Profiler and Telemetry Tracker."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class QueryProfile:
    """Detailed telemetry profile for an analytical query execution."""
    ast_validation_time_us: float = 0.0
    execution_time_ms: float = 0.0
    rows_scanned: int = 0
    rows_returned: int = 0
    bytes_scanned: int | None = None
    dialect: str = "duckdb"
    cache_hit: bool = False
    tokens_used: int = 0


class QueryProfiler:
    """Scoped execution profiler."""

    def __init__(self):
        self._profiles: list[QueryProfile] = []

    def record(self, profile: QueryProfile) -> None:
        self._profiles.append(profile)

    @property
    def last_profile(self) -> QueryProfile | None:
        return self._profiles[-1] if self._profiles else None
