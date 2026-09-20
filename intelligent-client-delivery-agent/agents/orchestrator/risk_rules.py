"""Pure, unit-testable risk heuristics for Power BI delivery projects.

Thresholds below are the agreed defaults for the capstone demo (see review
notes) and are intended to be tuned later against real project data.
"""
from __future__ import annotations

from datetime import date, datetime

# --- Tunable thresholds -----------------------------------------------------

VELOCITY_DROP_PCT_THRESHOLD = 0.20  # 20% drop vs trailing average -> max score
VELOCITY_DECLINE_STREAK_MAX = 3  # 3+ consecutive declining sprints -> max score
VELOCITY_PCT_WEIGHT = 0.6
VELOCITY_STREAK_WEIGHT = 0.4

BUG_COUNT_THRESHOLD = 5
BUG_DEADLINE_DAYS_THRESHOLD = 10

TIMESHEET_OVERRUN_RATIO_THRESHOLD = 0.9

STALE_DAYS_THRESHOLD = 7
STALE_RISK_COLORS = {"red", "yellow"}

# Weights used to combine the four signals into a single 0-100 risk_score.
RISK_WEIGHTS = {
    "velocity_drop": 40,
    "bug_deadline": 25,
    "timesheet_overrun": 20,
    "stale_status": 15,
}

# Any single triggered signal (the smallest weight is stale_status) is enough
# to call a project "at risk"; consumers (e.g. the report generator) can use
# this to classify risk_score() output.
AT_RISK_THRESHOLD = 15


def velocity_drop_risk(sprint_history: list[float]) -> float:
    """Score (0.0-1.0) combining % drop vs the trailing average and a
    consecutive decline streak, ending on the latest sprint."""
    if len(sprint_history) < 2:
        return 0.0

    latest = sprint_history[-1]
    prior = sprint_history[:-1]
    avg_prior = sum(prior) / len(prior)

    if avg_prior <= 0:
        pct_drop_score = 0.0
    else:
        pct_drop = (avg_prior - latest) / avg_prior
        pct_drop_score = max(0.0, min(1.0, pct_drop / VELOCITY_DROP_PCT_THRESHOLD))

    streak = 0
    for i in range(len(sprint_history) - 1, 0, -1):
        if sprint_history[i] < sprint_history[i - 1]:
            streak += 1
        else:
            break
    streak_score = min(1.0, streak / VELOCITY_DECLINE_STREAK_MAX)

    score = VELOCITY_PCT_WEIGHT * pct_drop_score + VELOCITY_STREAK_WEIGHT * streak_score
    return round(score, 3)


def bug_deadline_risk(open_bugs: int, days_to_deadline: int) -> bool:
    """True when the open bug count is high AND the deadline is close."""
    return open_bugs >= BUG_COUNT_THRESHOLD and days_to_deadline <= BUG_DEADLINE_DAYS_THRESHOLD


def timesheet_overrun_risk(estimated_hours: float, logged_hours: float) -> bool:
    """True when logged hours have consumed most/all of the estimate."""
    if estimated_hours <= 0:
        return logged_hours > 0
    return (logged_hours / estimated_hours) >= TIMESHEET_OVERRUN_RATIO_THRESHOLD


def stale_status_risk(
    last_updated: str | date, status_color: str, today: date | None = None
) -> bool:
    """True when the status hasn't been refreshed recently, or is already
    Red/Yellow (regardless of how recently it was updated)."""
    if status_color.strip().lower() in STALE_RISK_COLORS:
        return True

    if isinstance(last_updated, str):
        last_updated = datetime.strptime(last_updated, "%Y-%m-%d").date()
    reference = today or date.today()
    return (reference - last_updated).days > STALE_DAYS_THRESHOLD


def risk_score(project: dict) -> tuple[int, list[str]]:
    """Combine the four signals into a 0-100 weighted score plus the list of
    triggered reasons.

    Expected keys on `project`:
        sprint_history: list[float]
        open_bugs: int
        days_to_deadline: int
        estimated_hours: float
        logged_hours: float
        last_updated: str ("YYYY-MM-DD") or date
        status_color: str
        today: date | None (optional, for deterministic evaluation)
    """
    reasons: list[str] = []
    score = 0.0

    v_score = velocity_drop_risk(project["sprint_history"])
    if v_score > 0:
        score += RISK_WEIGHTS["velocity_drop"] * v_score
        reasons.append(f"Velocity drop risk (score={v_score})")

    if bug_deadline_risk(project["open_bugs"], project["days_to_deadline"]):
        score += RISK_WEIGHTS["bug_deadline"]
        reasons.append(
            f"{project['open_bugs']} open bugs with only "
            f"{project['days_to_deadline']} days to deadline"
        )

    if timesheet_overrun_risk(project["estimated_hours"], project["logged_hours"]):
        score += RISK_WEIGHTS["timesheet_overrun"]
        reasons.append(
            f"Logged {project['logged_hours']}h of {project['estimated_hours']}h estimated"
        )

    if stale_status_risk(project["last_updated"], project["status_color"], project.get("today")):
        score += RISK_WEIGHTS["stale_status"]
        reasons.append(
            f"Status '{project['status_color']}' last updated {project['last_updated']}"
        )

    return round(min(100.0, score)), reasons
