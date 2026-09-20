"""ChromaDB Vector Store module for indexing and semantically searching project documents.

Provides grounded semantic search over SharePoint project status, DevOps sprint/bug metrics,
and D365 timesheets.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

class ProjectDocument:
    def __init__(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        self.doc_id = doc_id
        self.content = content
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
        }


class LocalVectorStore:
    """Local Vector Store wrapping ChromaDB with an in-memory fallback mechanism."""

    def __init__(self, collection_name: str = "project_delivery_docs"):
        self.collection_name = collection_name
        self.documents: List[ProjectDocument] = []
        self._use_chroma = False
        self._chroma_collection = None

        try:
            import chromadb

            client = chromadb.Client()
            self._chroma_collection = client.create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False

    def build_index(
        self,
        sharepoint_csv: Optional[Path] = None,
        devops_json: Optional[Path] = None,
        timesheets_csv: Optional[Path] = None,
    ) -> int:
        """Ingest all data sources and build document embeddings."""
        sp_path = sharepoint_csv or (DATA_DIR / "sharepoint" / "project_status.csv")
        devops_path = devops_json or (DATA_DIR / "devops" / "cached_sample.json")
        ts_path = timesheets_csv or (DATA_DIR / "d365_timesheets" / "timesheets.csv")

        statuses = {}
        if sp_path.exists():
            with sp_path.open(newline="", encoding="utf-8") as f:
                statuses = {r["project_id"]: r for r in csv.DictReader(f)}

        devops = {}
        if devops_path.exists():
            with devops_path.open(encoding="utf-8") as f:
                devops = json.load(f).get("projects", {})

        timesheets: Dict[str, Dict[str, float]] = {}
        if ts_path.exists():
            with ts_path.open(newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    pid = r["project_id"]
                    bucket = timesheets.setdefault(
                        pid, {"estimated_hours": 0.0, "logged_hours": 0.0}
                    )
                    bucket["estimated_hours"] += float(r["estimated_hours"])
                    bucket["logged_hours"] += float(r["logged_hours"])

        all_pids = set(statuses.keys()) | set(devops.keys()) | set(timesheets.keys())
        self.documents.clear()

        for pid in sorted(all_pids):
            sp = statuses.get(pid, {})
            do = devops.get(pid, {})
            ts = timesheets.get(pid, {"estimated_hours": 0.0, "logged_hours": 0.0})

            sprints = do.get("sprints", [])
            velocities = [s.get("velocity", 0) for s in sprints]
            open_bugs = do.get("open_bugs", 0)
            deadline = do.get("deadline", "N/A")
            last_updated = sp.get("last_updated", "N/A")
            status_color = sp.get("status_color", "Unknown")

            content = (
                f"Project {pid} Summary: "
                f"SharePoint Status Color: {status_color}, Last Updated: {last_updated}. "
                f"Azure DevOps: Open Bugs: {open_bugs}, Deadline: {deadline}, Sprint Velocities: {velocities}. "
                f"D365 Timesheets: Logged Hours: {ts['logged_hours']}h / Estimated Hours: {ts['estimated_hours']}h."
            )

            metadata = {
                "project_id": pid,
                "status_color": status_color,
                "last_updated": last_updated,
                "open_bugs": open_bugs,
                "deadline": deadline,
                "logged_hours": ts["logged_hours"],
                "estimated_hours": ts["estimated_hours"],
                "sprint_velocities": velocities,
            }

            doc = ProjectDocument(doc_id=pid, content=content, metadata=metadata)
            self.documents.append(doc)

            if self._use_chroma and self._chroma_collection:
                self._chroma_collection.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[pid],
                )

        return len(self.documents)

    def similarity_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search indexed documents by keyword/semantic relevance."""
        if not self.documents:
            self.build_index()

        query_terms = set(query.lower().split())

        if self._use_chroma and self._chroma_collection:
            try:
                res = self._chroma_collection.query(query_texts=[query], n_results=top_k)
                hits = []
                if res and res.get("documents"):
                    for i in range(len(res["documents"][0])):
                        hits.append(
                            {
                                "id": res["ids"][0][i],
                                "content": res["documents"][0][i],
                                "metadata": res["metadatas"][0][i],
                                "score": 0.95 - (i * 0.05),
                            }
                        )
                    return hits
            except Exception:
                pass

        # In-memory keyword/TF relevance scoring fallback
        scored = []
        for doc in self.documents:
            content_lower = doc.content.lower()
            score = sum(1 for t in query_terms if t in content_lower)
            if "at risk" in query.lower() or "health" in query.lower():
                if doc.metadata.get("status_color") in ["Red", "Yellow"] or doc.metadata.get("open_bugs", 0) >= 4:
                    score += 2
            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_docs = scored[:top_k]

        return [
            {
                "id": doc.doc_id,
                "content": doc.content,
                "metadata": doc.metadata,
                "score": score,
            }
            for score, doc in top_docs
        ]
