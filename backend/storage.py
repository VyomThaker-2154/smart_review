import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque

from config import settings


class InMemoryStore:
    """
    Thread-safe in-memory store for review history and batch results.
    Uses a deque with a max length to automatically evict oldest records.
    """

    def __init__(self):
        self._history: deque = deque(maxlen=settings.MAX_HISTORY_RECORDS)
        self._batches: Dict[str, Dict[str, Any]] = {}

    # ── History ──────────────────────────────────────────────────────────────

    def add_to_history(self, record: Dict[str, Any]) -> str:
        record_id = str(uuid.uuid4())
        record["id"] = record_id
        record["created_at"] = datetime.utcnow().isoformat() + "Z"
        self._history.appendleft(record)
        return record_id

    def get_history(
        self,
        page: int = 1,
        limit: int = 20,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        records = list(self._history)

        # Filter by date range if provided
        if date_from:
            records = [r for r in records if r.get("created_at", "") >= date_from]
        if date_to:
            records = [r for r in records if r.get("created_at", "") <= date_to + "Z"]

        total = len(records)
        start = (page - 1) * limit
        end = start + limit
        paginated = records[start:end]

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total > 0 else 1,
            "records": paginated,
        }

    # ── Batches ───────────────────────────────────────────────────────────────

    def create_batch(self, source: str = "api") -> str:
        batch_id = str(uuid.uuid4())
        self._batches[batch_id] = {
            "batch_id": batch_id,
            "source": source,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": None,
            "total": 0,
            "results": [],
        }
        return batch_id

    def update_batch(self, batch_id: str, results: List[Dict], status: str = "completed"):
        if batch_id not in self._batches:
            return
        batch = self._batches[batch_id]
        batch["results"] = results
        batch["total"] = len(results)
        batch["status"] = status
        batch["completed_at"] = datetime.utcnow().isoformat() + "Z"

        # Also log each result into history
        for idx, result in enumerate(results):
            self.add_to_history(
                {
                    "type": "bulk",
                    "batch_id": batch_id,
                    "review_index": idx,
                    "text": result.get("text", ""),
                    "sentiment": result.get("sentiment"),
                    "confidence": result.get("confidence"),
                    "summary": result.get("summary"),
                }
            )

    def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        return self._batches.get(batch_id)

    def list_batches(self) -> List[Dict[str, Any]]:
        return [
            {k: v for k, v in b.items() if k != "results"}
            for b in self._batches.values()
        ]


# Singleton instance used across all routers
store = InMemoryStore()
