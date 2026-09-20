"""LLM Synthesizer — Google Gemini-powered query reasoning layer.

Takes the user's natural language query and the structured project data produced
by the risk evaluation pipeline, then asks Gemini to produce a direct,
grounded answer.  Falls back to a plain summary when no API key is present.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

# Load .env so GEMINI_API_KEY is available even when running from CLI
try:
    from dotenv import load_dotenv

    _env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(dotenv_path=_env_path, override=False)
except ImportError:
    pass  # python-dotenv not installed yet; key must already be in env

_FALLBACK_MSG = (
    "[LLM not available — set GEMINI_API_KEY in .env to enable AI answers]"
)


def _build_context(projects: List[Dict[str, Any]]) -> str:
    """Serialize evaluated projects as a compact JSON string for the prompt."""
    rows = []
    for p in projects:
        rows.append(
            {
                "project_id": p["project_id"],
                "open_bugs": p["open_bugs"],
                "risk_score": p["risk_score"],
                "is_at_risk": p["is_at_risk"],
                "estimated_hours": p["estimated_hours"],
                "logged_hours": p["logged_hours"],
                "days_to_deadline": p["days_to_deadline"],
                "status_color": p["status_color"],
                "risk_reasons": p["reasons"],
            }
        )
    return json.dumps(rows, indent=2)


def _build_prompt(query: str, context: str) -> str:
    return (
        "You are an intelligent delivery manager assistant for MAQ Software.\n"
        "You have access to the following Power BI project delivery data:\n\n"
        f"{context}\n\n"
        "Answer the following manager query accurately and concisely, "
        "using ONLY the data provided above. "
        "If the query asks for a filtered total (e.g. 'except PBI-009'), "
        "exclude those projects before computing. "
        "Be specific — include numbers, project IDs, and reasons.\n\n"
        f"Manager Query: {query}\n\n"
        "Answer:"
    )


class LLMSynthesizer:
    """Calls Google Gemini via the new google-genai SDK to answer queries."""

    MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash"]

    def __init__(self) -> None:
        self._client = None
        self._ready = False
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[LLMSynthesizer] GEMINI_API_KEY not set — LLM answers disabled.")
            return
        try:
            from google import genai  # type: ignore

            self._client = genai.Client(api_key=api_key)
            self._ready = True
            print(f"[LLMSynthesizer] Ready — primary model: {self.MODELS[0]}")
        except ImportError:
            print(
                "[LLMSynthesizer] google-genai not installed. "
                "Run: pip install google-genai"
            )

    def answer(self, query: str, projects: List[Dict[str, Any]]) -> str:
        """Return a natural-language answer to *query* grounded in *projects*."""
        if not self._ready or self._client is None:
            return _FALLBACK_MSG

        context = _build_context(projects)
        prompt = _build_prompt(query, context)

        import time

        last_error = None
        for model in self.MODELS:
            for attempt in range(2):
                try:
                    response = self._client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    return response.text.strip()
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    # If unavailable or high demand, wait a moment or try next model
                    err_msg = str(exc).lower()
                    if "503" in err_msg or "unavailable" in err_msg or "high demand" in err_msg:
                        time.sleep(1.5)
                        continue
                    break  # Try next model if it's 404 or unsupported

        return f"[LLM error: {last_error}]"
