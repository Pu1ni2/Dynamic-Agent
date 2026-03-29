"""Semantic search via ChromaDB — finds similar tasks and relevant memories."""

from __future__ import annotations
import json
import os

from .types import Episode, MemoryEntry

_chroma_client = None
_collection = None


def _get_collection(persist_dir: str):
    """Lazy-init ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        os.makedirs(persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        _collection = _chroma_client.get_or_create_collection(
            name="hivemind_memory",
            metadata={"hnsw:space": "cosine"},
        )
        return _collection
    except ImportError:
        return None
    except Exception:
        return None


class SemanticIndex:
    """Vector search over episodes and memory entries."""

    def __init__(self, persist_dir: str):
        self._persist_dir = persist_dir
        self._available = None

    def _col(self):
        col = _get_collection(self._persist_dir)
        if col is not None:
            self._available = True
        else:
            self._available = False
        return col

    @property
    def available(self) -> bool:
        if self._available is None:
            self._col()
        return self._available

    def index_episode(self, episode: Episode):
        col = self._col()
        if col is None:
            return

        # Index the task description
        docs = [
            episode.task,
            json.dumps({"domain": episode.task_domain, "complexity": episode.task_complexity,
                         "agents": [a.get("role", "") for a in episode.plan.get("agents", [])]}),
        ]
        ids = [
            f"ep-task-{episode.episode_id}",
            f"ep-plan-{episode.episode_id}",
        ]
        metadatas = [
            {"type": "episode_task", "episode_id": episode.episode_id,
             "domain": episode.task_domain, "timestamp": episode.timestamp},
            {"type": "episode_plan", "episode_id": episode.episode_id,
             "domain": episode.task_domain, "timestamp": episode.timestamp},
        ]

        try:
            col.upsert(documents=docs, ids=ids, metadatas=metadatas)
        except Exception:
            pass

    def index_memory_entry(self, entry: MemoryEntry):
        col = self._col()
        if col is None:
            return
        try:
            col.upsert(
                documents=[entry.content],
                ids=[f"mem-{entry.entry_id}"],
                metadatas=[{
                    "type": "memory_entry",
                    "memory_type": entry.memory_type,
                    "entry_id": entry.entry_id,
                    "source_episode_id": entry.source_episode_id or "",
                }],
            )
        except Exception:
            pass

    def search(self, query: str, n_results: int = 5, filter_type: str | None = None) -> list[dict]:
        col = self._col()
        if col is None:
            return []
        try:
            where = {"type": filter_type} if filter_type else None
            results = col.query(query_texts=[query], n_results=n_results, where=where)
            out = []
            for i in range(len(results["ids"][0])):
                out.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
            return out
        except Exception:
            return []

    def search_similar_tasks(self, task: str, n_results: int = 3) -> list[dict]:
        return self.search(task, n_results=n_results, filter_type="episode_task")

    def search_relevant_memories(self, context: str, memory_type: str | None = None, n_results: int = 5) -> list[dict]:
        filter_type = "memory_entry" if not memory_type else None
        results = self.search(context, n_results=n_results, filter_type=filter_type)
        if memory_type:
            results = [r for r in results if r.get("metadata", {}).get("memory_type") == memory_type]
        return results
