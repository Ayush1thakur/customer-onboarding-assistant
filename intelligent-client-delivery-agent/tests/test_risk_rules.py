import csv
import json
from datetime import date
from pathlib import Path

import pytest

from agents.orchestrator.risk_rules import (
    AT_RISK_THRESHOLD,
    bug_deadline_risk,
    risk_score,
    stale_status_risk,
    timesheet_overrun_risk,
    velocity_drop_risk,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# Fixed "as of" date matching the sample data, so tests are deterministic
# regardless of when they're run.
REFERENCE_DATE = date(2026, 9, 7)

AT_RISK_IDS = {"PBI-003", "PBI-005", "PBI-008"}
HEALTHY_IDS = {"PBI-001", "PBI-002", "PBI-004", "PBI-006", "PBI-007", "PBI-009"}


def _load_project_status() -> dict[str, dict]:
    path = DATA_DIR / "sharepoint" / "project_status.csv"
    with path.open(newline="", encoding="utf-8") as f:
        return {row["project_id"]: row for row in csv.DictReader(f)}


def _load_devops_cache() -> dict[str, dict]:
    path = DATA_DIR / "devops" / "cached_sample.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)["projects"]


def _load_timesheet_totals() -> dict[str, dict[str, float]]:
    path = DATA_DIR / "d365_timesheets" / "timesheets.csv"
    totals: dict[str, dict[str, float]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = row["project_id"]
            bucket = totals.setdefault(pid, {"estimated_hours": 0.0, "logged_hours": 0.0})
            bucket["estimated_hours"] += float(row["estimated_hours"])
            bucket["logged_hours"] += float(row["logged_hours"])
    return totals


def _build_project(project_id, statuses, devops, timesheets) -> dict:
    status = statuses[project_id]
    devops_entry = devops[project_id]
    deadline = date.fromisoformat(devops_entry["deadline"])
    hours = timesheets[project_id]
    return {
        "project_id": project_id,
        "sprint_history": [s["velocity"] for s in devops_entry["sprints"]],
        "open_bugs": devops_entry["open_bugs"],
        "days_to_deadline": (deadline - REFERENCE_DATE).days,
        "estimated_hours": hours["estimated_hours"],
        "logged_hours": hours["logged_hours"],
        "last_updated": status["last_updated"],
        "status_color": status["status_color"],
        "today": REFERENCE_DATE,
    }


@pytest.fixture(scope="module")
def projects() -> dict[str, dict]:
    statuses = _load_project_status()
    devops = _load_devops_cache()
    timesheets = _load_timesheet_totals()
    return {pid: _build_project(pid, statuses, devops, timesheets) for pid in statuses}


def test_sample_data_covers_expected_projects(projects):
    assert set(projects) == AT_RISK_IDS | HEALTHY_IDS


def test_velocity_drop_risk_detects_declining_trend(projects):
    assert velocity_drop_risk(projects["PBI-005"]["sprint_history"]) > 0.5
    assert velocity_drop_risk(projects["PBI-008"]["sprint_history"]) > 0.5
    assert velocity_drop_risk(projects["PBI-001"]["sprint_history"]) == 0.0


def test_velocity_drop_risk_needs_at_least_two_sprints():
    assert velocity_drop_risk([42]) == 0.0
    assert velocity_drop_risk([]) == 0.0


def test_bug_deadline_risk_boundaries():
    assert bug_deadline_risk(5, 10)
    assert not bug_deadline_risk(4, 10)
    assert not bug_deadline_risk(5, 11)


def test_bug_deadline_risk_against_sample_data(projects):
    assert bug_deadline_risk(
        projects["PBI-005"]["open_bugs"], projects["PBI-005"]["days_to_deadline"]
    )
    assert not bug_deadline_risk(
        projects["PBI-001"]["open_bugs"], projects["PBI-001"]["days_to_deadline"]
    )


def test_timesheet_overrun_risk_boundary():
    assert timesheet_overrun_risk(100, 90)
    assert not timesheet_overrun_risk(100, 89.9)


def test_timesheet_overrun_risk_against_sample_data(projects):
    assert timesheet_overrun_risk(
        projects["PBI-005"]["estimated_hours"], projects["PBI-005"]["logged_hours"]
    )
    assert timesheet_overrun_risk(
        projects["PBI-008"]["estimated_hours"], projects["PBI-008"]["logged_hours"]
    )
    assert not timesheet_overrun_risk(
        projects["PBI-001"]["estimated_hours"], projects["PBI-001"]["logged_hours"]
    )


def test_stale_status_risk_triggers_on_color_alone():
    assert stale_status_risk("2026-09-06", "Red", today=REFERENCE_DATE)
    assert stale_status_risk("2026-09-06", "Yellow", today=REFERENCE_DATE)


def test_stale_status_risk_triggers_on_age_alone():
    assert stale_status_risk("2026-08-20", "Green", today=REFERENCE_DATE)
    assert not stale_status_risk("2026-09-05", "Green", today=REFERENCE_DATE)


@pytest.mark.parametrize("project_id", sorted(AT_RISK_IDS))
def test_risk_score_flags_at_risk_projects(projects, project_id):
    score, reasons = risk_score(projects[project_id])
    assert score >= AT_RISK_THRESHOLD, f"{project_id} expected at-risk, got score={score}"
    assert reasons


@pytest.mark.parametrize("project_id", sorted(HEALTHY_IDS))
def test_risk_score_leaves_healthy_projects_low(projects, project_id):
    score, reasons = risk_score(projects[project_id])
    assert score < AT_RISK_THRESHOLD, (
        f"{project_id} expected healthy, got score={score} reasons={reasons}"
    )
