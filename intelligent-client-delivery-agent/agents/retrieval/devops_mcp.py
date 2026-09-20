"""Azure DevOps data tool for fetching sprint velocities, open bug counts, and project timelines.

Reads from a local cached JSON file simulating Azure DevOps REST API responses.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


class DevOpsDataTool:
    """Tool for Azure DevOps data retrieval from local cache."""

    def __init__(self, devops_json_path: Optional[Path] = None):
        self.devops_path = devops_json_path or (DATA_DIR / "devops" / "cached_sample.json")
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if self.devops_path.exists():
            with self.devops_path.open(encoding="utf-8") as f:
                return json.load(f).get("projects", {})
        return {}

    def get_project_telemetry(self, project_id: str) -> Dict[str, Any]:
        """Tool method: Fetch detailed Azure DevOps telemetry for a given project_id."""
        project_data = self._cache.get(project_id)
        if not project_data:
            return {"error": f"Project {project_id} not found in Azure DevOps telemetry."}

        sprints = project_data.get("sprints", [])
        velocities = [s.get("velocity", 0) for s in sprints]
        latest_velocity = velocities[-1] if velocities else 0

        return {
            "project_id": project_id,
            "open_bugs": project_data.get("open_bugs", 0),
            "deadline": project_data.get("deadline", "N/A"),
            "sprint_count": len(sprints),
            "latest_sprint_velocity": latest_velocity,
            "velocity_history": velocities,
        }

    def list_all_devops_projects(self) -> List[str]:
        """Tool method: List all available Azure DevOps project IDs."""
        return sorted(list(self._cache.keys()))


# Backward-compatibility alias for tests
FastMCPDevOpsTool = DevOpsDataTool


# Standalone query function for Azure DevOps data retrieval
def devops_mcp_query_tool(project_id: str) -> str:
    tool = DevOpsDataTool()
    res = tool.get_project_telemetry(project_id)
    return json.dumps(res, indent=2)
