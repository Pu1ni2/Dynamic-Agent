"""Shared workspace — thread-safe in-run memory for agent collaboration."""

from __future__ import annotations
import threading
from datetime import datetime, timezone

from .types import SharedMemoryItem


class SharedWorkspace:
    """Thread-safe shared memory that agents can read/write during a single pipeline run.

    Agents use `remember` and `recall` tools to interact with this workspace,
    enabling collaboration beyond the dependency graph.
    """

    def __init__(self):
        self._store: dict[str, SharedMemoryItem] = {}
        self._lock = threading.Lock()

    def write(self, key: str, value: str, author_agent_id: str, tags: list[str] | None = None) -> str:
        """Store a value in shared memory."""
        with self._lock:
            self._store[key] = SharedMemoryItem(
                key=key,
                value=value,
                author_agent_id=author_agent_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                tags=tags or [],
            )
        return f"Stored '{key}' in shared memory ({len(value)} chars)"

    def read(self, key: str) -> str:
        """Read a value from shared memory."""
        with self._lock:
            item = self._store.get(key)
        if item is None:
            return f"Key '{key}' not found in shared memory. Available keys: {', '.join(self._store.keys()) or 'none'}"
        return item.value

    def search_by_tag(self, tag: str) -> list[SharedMemoryItem]:
        """Find all items matching a tag."""
        with self._lock:
            return [item for item in self._store.values() if tag in item.tags]

    def list_keys(self) -> list[str]:
        with self._lock:
            return list(self._store.keys())

    def get_all(self) -> dict[str, SharedMemoryItem]:
        with self._lock:
            return dict(self._store)

    def get_summary(self) -> str:
        """Return a formatted summary of everything in the workspace."""
        with self._lock:
            if not self._store:
                return "Shared memory is empty. No other agents have stored anything yet."
            lines = ["=== Shared Memory Contents ==="]
            for key, item in self._store.items():
                preview = item.value[:200] + ("..." if len(item.value) > 200 else "")
                tags_str = f" [tags: {', '.join(item.tags)}]" if item.tags else ""
                lines.append(f"\n[{key}] (by {item.author_agent_id}){tags_str}\n{preview}")
            return "\n".join(lines)

    def to_dict(self) -> dict:
        """Snapshot for OrchestratorState."""
        with self._lock:
            return {
                key: {"value": item.value, "author": item.author_agent_id, "tags": item.tags}
                for key, item in self._store.items()
            }
