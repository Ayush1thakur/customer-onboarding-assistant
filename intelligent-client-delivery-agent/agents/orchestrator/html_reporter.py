"""Executive HTML Status Report Generator.

Generates visual delivery project dashboards with risk scores, metric breakdown,
and AI recommendations.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def generate_html_report(
    projects_evaluated: List[Dict[str, Any]],
    query: str,
    output_path: Path,
) -> Path:
    """Render and save executive HTML status report."""
    total_projects = len(projects_evaluated)
    at_risk_projects = [p for p in projects_evaluated if p["is_at_risk"]]
    healthy_projects = [p for p in projects_evaluated if not p["is_at_risk"]]

    at_risk_count = len(at_risk_projects)
    healthy_count = len(healthy_projects)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows_html = ""
    for p in projects_evaluated:
        pid = p["project_id"]
        score = p["risk_score"]
        is_risk = p["is_at_risk"]
        reasons = p["reasons"]

        badge_class = "risk-badge-red" if is_risk else "risk-badge-green"
        status_text = "AT RISK" if is_risk else "HEALTHY"

        reasons_list_html = (
            "".join([f"<li>{r}</li>" for r in reasons])
            if reasons
            else "<li>No risk flags triggered. Project performing on schedule.</li>"
        )

        rows_html += f"""
        <tr class="project-row {'row-at-risk' if is_risk else ''}">
            <td class="pid-cell">{pid}</td>
            <td><span class="status-badge {badge_class}">{status_text}</span></td>
            <td class="score-cell"><strong>{score}</strong> / 100</td>
            <td>{p['open_bugs']} bugs | {p['days_to_deadline']} days left</td>
            <td>{p['logged_hours']}h / {p['estimated_hours']}h</td>
            <td><ul class="reasons-list">{reasons_list_html}</ul></td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MAQ Software - Intelligent Client Delivery Status Report</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-red: #f43f5e;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
            --border-color: #334155;
        }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 30px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);
        }}
        .header h1 {{
            margin: 0 0 8px 0;
            color: var(--accent-blue);
            font-size: 26px;
        }}
        .header p {{
            margin: 4px 0;
            color: var(--text-muted);
            font-size: 14px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .metric-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }}
        .metric-card .val {{
            font-size: 36px;
            font-weight: bold;
            margin-top: 8px;
        }}
        .val-total {{ color: var(--accent-blue); }}
        .val-risk {{ color: var(--accent-red); }}
        .val-healthy {{ color: var(--accent-green); }}

        .table-container {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th {{
            background-color: #0f172a;
            color: var(--accent-blue);
            padding: 16px;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border-color);
        }}
        td {{
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
            font-size: 14px;
            vertical-align: top;
        }}
        tr:last-child td {{ border-bottom: none; }}
        .project-row:hover {{ background-color: #283548; }}
        .row-at-risk {{ background-color: rgba(244, 63, 94, 0.05); }}
        .pid-cell {{ font-weight: bold; font-family: monospace; font-size: 15px; color: var(--accent-blue); }}
        .score-cell {{ font-size: 16px; }}
        
        .status-badge {{
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
        }}
        .risk-badge-red {{
            background-color: rgba(244, 63, 94, 0.2);
            color: #f43f5e;
            border: 1px solid #f43f5e;
        }}
        .risk-badge-green {{
            background-color: rgba(16, 185, 129, 0.2);
            color: #10b981;
            border: 1px solid #10b981;
        }}

        .reasons-list {{
            margin: 0;
            padding-left: 18px;
            color: var(--text-muted);
        }}
        .reasons-list li {{ margin-bottom: 4px; }}

        .footer {{
            margin-top: 24px;
            text-align: center;
            color: var(--text-muted);
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MAQ Software — Intelligent Client Delivery Agent</h1>
            <p><strong>Query:</strong> "{query}"</p>
            <p><strong>Generated At:</strong> {generated_at} | <strong>Grounding:</strong> SharePoint + Azure DevOps FastMCP + D365 Timesheets</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="title">Active Projects Monitored</div>
                <div class="val val-total">{total_projects}</div>
            </div>
            <div class="metric-card">
                <div class="title">Projects At Risk</div>
                <div class="val val-risk">{at_risk_count}</div>
            </div>
            <div class="metric-card">
                <div class="title">Healthy Projects</div>
                <div class="val val-healthy">{healthy_count}</div>
            </div>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Project ID</th>
                        <th>Health Status</th>
                        <th>Risk Score</th>
                        <th>DevOps Telemetry</th>
                        <th>Logged / Estimated Hours</th>
                        <th>Risk Flags & Mitigation Reasons</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>

        <div class="footer">
            MAQ Software Delivery Intelligence Engine • Step Up Stack Available for Production (Azure AI Foundry + Entra ID)
        </div>
    </div>
</body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    return output_path
