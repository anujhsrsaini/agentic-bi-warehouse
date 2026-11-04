"""Master Cognitive Orchestrator for Governed Agentic BI.

Executes the 6-stage analytical pipeline:
Stage 1: Intent Routing & Proactive Disambiguation
Stage 2: 3-Tier Categorical Entity Grounding & Schema Linking
Stage 3: Dual-Track SQL Generation
Stage 4: 7-Stage AST Security & Sandbox Guardrail
Stage 5: Self-Healing Execution & Reflexion Loop
Stage 6: Diagnostic Attribution, Column Lineage & Visual Canvas Synthesis
"""

from __future__ import annotations

from src.agents.attribution import MetricAttributionEngine
from src.agents.canvas import VisualCanvasAgent
from src.agents.executor import SelfHealingExecutionAgent
from src.agents.router import IntentRouterAgent
from src.agents.sql_generator import SQLGeneratorAgent
from src.agents.state import AgenticBIState, UserIntent
from src.engine.connectors.base import BaseWarehouseConnector
from src.engine.lineage import ColumnLineageTracer


class AgenticBIOrchestrator:
    """End-to-End Multi-Agent Cognitive Workflow Coordinator."""

    def __init__(self, connector: BaseWarehouseConnector | None = None):
        self.router = IntentRouterAgent()
        self.sql_generator = SQLGeneratorAgent()
        self.executor = SelfHealingExecutionAgent(connector=connector)
        self.attribution_engine = MetricAttributionEngine()
        self.canvas_agent = VisualCanvasAgent()
        self.lineage_tracer = ColumnLineageTracer()

    def process_query(self, question: str, session_id: str = "default-session") -> AgenticBIState:
        """Run the full 6-stage cognitive pipeline for a natural language question."""
        state = AgenticBIState(question=question, session_id=session_id)

        # Stage 1: Triage & Intent Routing
        state = self.router.route(state)
        if state.intent == UserIntent.CLARIFICATION_REQUIRED:
            # Proactively stop and surface structured clarification options
            return state

        # Stage 2 & 3: Entity Grounding & SQL Generation
        state = self.sql_generator.generate(state)

        # Stage 4 & 5: AST Security Firewall & Self-Healing Execution
        state = self.executor.execute(state)
        if state.execution_error or not state.execution_result:
            return state

        # Stage 6a: Column Lineage Extraction
        if state.execution_result.column_names:
            target_metric = state.metric_name or state.execution_result.column_names[-1]
            try:
                state.lineage_mermaid = self.lineage_tracer.to_mermaid(target_metric, state.validated_sql)
                state.lineage_ascii = self.lineage_tracer.to_ascii_tree(target_metric, state.validated_sql)
            except Exception:
                pass

        # Stage 6b: Diagnostic Anomaly Attribution (if applicable)
        if state.intent == UserIntent.DIAGNOSTIC_WHY:
            diag_info = self.attribution_engine.diagnose_churn_drivers(state.execution_result.data)
            state.diagnostic_attribution = diag_info
            state.summary_narrative = diag_info.get("summary_narrative", "")

        # Stage 6c: Visual Canvas & Narrative Synthesis
        if not state.summary_narrative:
            state = self.canvas_agent.synthesize(state)

        return state
