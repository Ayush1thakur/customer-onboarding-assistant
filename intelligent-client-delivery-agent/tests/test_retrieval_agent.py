"""Unit and Integration tests for Data Retrieval Agent, Vector Store, and DevOps FastMCP."""
from __future__ import annotations

import pytest
from agents.retrieval.autogen_retrieval import DataRetrievalAgent
from agents.retrieval.devops_mcp import FastMCPDevOpsTool
from agents.retrieval.vector_store import LocalVectorStore


def test_vector_store_build_and_search():
    store = LocalVectorStore()
    count = store.build_index()
    assert count >= 9, f"Expected at least 9 project docs, indexed {count}"

    results = store.similarity_search("Power BI at risk health", top_k=5)
    assert len(results) > 0
    assert "id" in results[0]
    assert "metadata" in results[0]


def test_devops_mcp_tool_retrieval():
    mcp = FastMCPDevOpsTool()
    projects = mcp.list_all_devops_projects()
    assert "PBI-005" in projects
    assert "PBI-001" in projects

    telemetry = mcp.get_project_telemetry("PBI-005")
    assert telemetry["project_id"] == "PBI-005"
    assert telemetry["open_bugs"] >= 0
    assert "velocity_history" in telemetry


def test_autogen_retrieval_agent_context():
    agent = DataRetrievalAgent()
    res = agent.process_retrieval_request(
        query="What is the health of active Power BI delivery projects?",
        user_id="mgr_999",
    )
    assert res["context"]["authenticated_user_id"] == "mgr_999"
    assert res["retrieved_count"] > 0
    assert len(res["project_records"]) > 0
