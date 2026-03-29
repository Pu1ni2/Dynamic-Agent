"""Data structures for the HIVEMIND memory system."""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


@dataclass
class Episode:
    """A complete record of one pipeline execution."""
    episode_id: str
    task: str
    task_domain: str = ""
    task_complexity: str = ""
    plan: dict = field(default_factory=dict)
    agent_outputs: dict = field(default_factory=dict)
    final_output: str = ""
    coverage_report: dict = field(default_factory=dict)
    known_issues: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    user_feedback: str | None = None
    success_score: float | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Episode:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class MemoryEntry:
    """A distilled lesson or pattern extracted from an episode."""
    entry_id: str
    memory_type: str  # plan_pattern | tool_outcome | agent_strategy | user_preference | lesson_learned
    content: str
    context: dict = field(default_factory=dict)
    source_episode_id: str | None = None
    relevance_decay: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    access_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> MemoryEntry:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SharedMemoryItem:
    """A single item in the shared workspace between agents."""
    key: str
    value: str
    author_agent_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: list = field(default_factory=list)
