"""Master Cognitive Orchestrator for Governed Agentic BI.

Delegates to a LangGraph StateGraph workflow (Sarvam/LangChain-capable) while
preserving the legacy `process_query(question, session_id) -> AgenticBIState` contract.
Set `AGENTIC_BI_ENGINE=legacy` to force the original deterministic pipeline.
"""

from __future__ import annotations

from src.agents.state import AgenticBIState
from src.engine.connectors.base import BaseWarehouseConnector


class AgenticBIOrchestrator:
    """End-to-End Multi-Agent Cognitive Workflow Coordinator."""

    def __init__(self, connector: BaseWarehouseConnector | None = None):
        # Kept for compatibility; graph nodes currently use the default WarehouseSession.
        # Future: thread connector through graph runtime/config.
        self.connector = connector

    def process_query(self, question: str, session_id: str = "default-session") -> AgenticBIState:
        """Run the governed analytical workflow for a natural language question."""
        from src.graph.workflow import run_agentic_bi

        return run_agentic_bi(question, session_id=session_id)

