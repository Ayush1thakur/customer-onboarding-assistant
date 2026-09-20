"""Data Retrieval Agent for grounding project metrics from multiple data sources.

Retrieves and grounds project metrics from local vector store, Azure DevOps cache,
and D365 timesheets.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from agents.retrieval.devops_mcp import DevOpsDataTool
from agents.retrieval.vector_store import LocalVectorStore


class DataRetrievalAgent:
    """Data Retrieval Agent for project metrics grounding."""

    def __init__(self, name: str = "DataRetrievalAgent"):
        self.name = name
        self.vector_store = LocalVectorStore()
        self.vector_store.build_index()
        self.devops_tool = DevOpsDataTool()

    def process_retrieval_request(
        self,
        query: str,
        user_id: str = "mgr_001",
        user_role: str = "Delivery Manager",
    ) -> Dict[str, Any]:
        """Process retrieval request with simulated user identity context."""
        # Grounding query using Vector Store
        search_results = self.vector_store.similarity_search(query, top_k=9)

        # Retrieve DevOps MCP tool data for all returned projects
        project_details = []
        for hit in search_results:
            pid = hit["id"]
            devops_telemetry = self.devops_tool.get_project_telemetry(pid)
            project_details.append(
                {
                    "project_id": pid,
                    "search_score": hit.get("score", 0),
                    "vector_content": hit.get("content"),
                    "metadata": hit.get("metadata"),
                    "devops_telemetry": devops_telemetry,
                }
            )

        return {
            "query": query,
            "context": {
                "authenticated_user_id": user_id,
                "role": user_role,
                "scope": "Power BI Projects",
            },
            "retrieved_count": len(project_details),
            "project_records": project_details,
        }
