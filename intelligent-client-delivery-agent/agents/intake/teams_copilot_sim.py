"""Simulated Copilot Studio Teams Intake Agent.

Accepts natural language queries from Delivery Managers, extracts user authentication context,
and routes requests to the Insight Orchestrator.
"""
from __future__ import annotations

from typing import Any, Dict
from agents.orchestrator.semantic_kernel_orchestrator import InsightOrchestrator


class CopilotStudioIntakeSim:
    """Teams Copilot Studio Intake Simulator."""

    def __init__(self):
        self.orchestrator = InsightOrchestrator()

    def receive_teams_message(
        self,
        message_text: str,
        user_id: str = "mgr_001",
        user_name: str = "Delivery Lead",
    ) -> Dict[str, Any]:
        """Simulate processing a message from Copilot Studio in Microsoft Teams."""
        clean_query = message_text.strip()
        if not clean_query:
            clean_query = "What is the health of our active Power BI delivery projects?"

        # Route query to Insight Orchestrator
        result = self.orchestrator.execute_insight_pipeline(
            query=clean_query,
            user_id=user_id,
        )

        reply_summary = (
            f"Hello {user_name}, I have processed your request for '{clean_query}'.\n"
            f"Found {result['total_projects']} active projects, with {result['at_risk_count']} projects currently AT RISK "
            f"({', '.join(result['at_risk_projects'])}).\n"
            f"Detailed HTML status report generated at: {result['report_path']}\n\n"
            f"[AI Answer]\n{result['llm_answer']}"
        )

        return {
            "teams_reply": reply_summary,
            "pipeline_result": result,
        }
