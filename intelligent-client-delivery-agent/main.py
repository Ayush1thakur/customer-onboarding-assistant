"""Main entrypoint for Intelligent Client Delivery Agent.

Usage:
    python main.py
    python main.py --query "What is the health of our active Power BI delivery projects?"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.intake.teams_copilot_sim import CopilotStudioIntakeSim


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Intelligent Client Delivery Agent for MAQ Software"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="What is the health of our active Power BI delivery projects?",
        help="Natural language manager query from Teams / Copilot Studio",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default="mgr_001",
        help="Simulated Entra ID user context identifier",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("  MAQ Software - Intelligent Client Delivery Agent [FREE STACK]")
    print("=" * 70)
    print(f"Query Intake : {args.query}")
    print(f"User Context : {args.user_id} (Simulated Entra ID / RBAC)")
    print("-" * 70)

    intake = CopilotStudioIntakeSim()
    response = intake.receive_teams_message(
        message_text=args.query,
        user_id=args.user_id,
    )

    print("\n[Teams Copilot Studio Reply]")
    print(response["teams_reply"])
    print("\n[Generated Report]")
    print(f"Report File: {response['pipeline_result']['report_path']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
