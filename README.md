# Intelligent Client Delivery Agent

An AI-powered, multi-agent system that lets Delivery Managers ask natural-language questions about project health — e.g. *"What is the health of our active Power BI delivery projects?"* — and get back a grounded, explainable answer plus an auto-generated HTML status report.

---

## 🎯 Overview

Delivery Managers at MAQ Software need a fast, reliable read on project health across DevOps, timesheets, and documentation — without manually stitching together sprint data, logged hours, and status docs every time. This project builds an agentic pipeline that:

- Accepts natural-language queries via Microsoft Teams / Copilot Studio
- Retrieves grounded project data through a hybrid RAG pipeline
- Computes deterministic risk scores from real delivery metrics
- Uses an LLM to synthesize a clear, explainable answer
- Generates a shareable HTML status report

---

## 🏗️ Architecture

The system is organized into three layers:

### 1. Intake Layer (`agents/intake`)
- **`teams_copilot_sim.py`** — Simulates receiving a query from Microsoft Teams or Copilot Studio. Parses the natural-language query, resolves user context (simulated Entra ID / RBAC), and routes the request to the orchestrator.

### 2. Orchestration Layer (`agents/orchestrator`)
- **`semantic_kernel_orchestrator.py`** — The core pipeline driver:
  1. **Hybrid RAG Retrieval** — fetches grounded project records relevant to the query
  2. **Risk Heuristics Evaluation** — computes deterministic risk scores from sprint velocity, open bugs, days to deadline, and logged hours
  3. **LLM Query Synthesis** — uses an LLM to answer the manager's specific question based on the evaluated data
  4. **Report Generation** — renders a full HTML status report (`delivery_risk_report.html`)
- **`risk_rules.py`** — Heuristic logic and thresholds for flagging a project as "At Risk"
- **`llm_synthesizer.py`** — Connects to the LLM to turn structured data into natural-language answers
- **`html_reporter.py`** — Uses Jinja2 to render the final visual report

### 3. Retrieval & Data Layer (`agents/retrieval`, `data/`)
- **`vector_store.py`** — Local vector store (ChromaDB + Sentence Transformers) for indexing and retrieving project metadata
- **`devops_mcp.py`, `autogen_retrieval.py`** — AutoGen + FastMCP integration for dynamically querying live project data
- **`data/`** — Mock/structural data sources:
  - **DevOps** — sprint histories, active bugs, tasks
  - **D365 Timesheets** — logged vs. estimated hours
  - **SharePoint** — project documentation and status files

---

## 🛠️ Tech Stack

| Category | Tools |
|---|---|
| AI & Orchestration | `google-genai`, `semantic-kernel`, `pyautogen`, `llama-index` |
| Vector DB & Embeddings | `chromadb`, `sentence-transformers` |
| Tooling & Protocols | `fastmcp` (Model Context Protocol) |
| Templating & Testing | `jinja2`, `pytest` |

---

## 🚀 How It Works

```
python main.py --query "<your question>"
```

1. The query is ingested by the Teams simulator.
2. The RAG system retrieves relevant data from DevOps, Timesheets, and SharePoint.
3. A deterministic risk score is calculated for each project.
4. The LLM synthesizes an answer explaining *why* projects are at risk.
5. An HTML report is generated and saved to the project root; a text summary is printed to the console.

---

## 📦 Setup

```bash
git clone https://github.com/Ayush1thakur/customer-onboarding-assistant.git
cd intelligent-client-delivery-agent
pip install -r requirements.txt
python main.py --query "What is the health of our active Power BI delivery projects?"
```

> Update the install/run instructions above once dependency management (e.g. a `requirements.txt` or `pyproject.toml`) is finalized.

---

## 📊 Sample Output

Running a query produces:
- A console-printed text summary of project health
- A generated `delivery_risk_report.html` with per-project risk breakdowns and LLM-synthesized explanations

---

## 🔭 Future Improvements

- Live integration with Azure DevOps, D365, and SharePoint APIs (replacing mock data)
- Deploy as a Copilot Studio / Teams app for direct manager access
- Expand risk heuristics with historical trend analysis
- Add authentication and role-based access control (RBAC) for production use

---

## 👤 Author

Built by [Ayush Thakur](https://github.com/Ayush1thakur) — Developer at MAQ Software.
