"""Unit and Integration tests for Insight Orchestrator, Hybrid RAG, and HTML status report generation."""
from __future__ import annotations

from pathlib import Path
import pytest
from agents.orchestrator.semantic_kernel_orchestrator import InsightOrchestrator


def test_hybrid_rag_and_insight_orchestrator(tmp_path: Path):
    orchestrator = InsightOrchestrator()
    output_report_file = tmp_path / "test_report.html"

    result = orchestrator.execute_insight_pipeline(
        query="What is the health of our active Power BI delivery projects?",
        user_id="mgr_test",
        output_path=output_report_file,
    )

    assert result["total_projects"] >= 9
    assert result["at_risk_count"] >= 1
    assert "PBI-005" in result["at_risk_projects"]
    assert output_report_file.exists()

    content = output_report_file.read_text(encoding="utf-8")
    assert "MAQ Software" in content
    assert "AT RISK" in content
    assert "PBI-005" in content
