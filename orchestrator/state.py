from __future__ import annotations
from typing import Annotated, TypedDict


def merge_dicts(left: dict, right: dict) -> dict:
    """Reducer that merges two dicts. Used so parallel agents can write to agent_outputs concurrently."""
    merged = left.copy()
    merged.update(right)
    return merged


def merge_lists(left: list, right: list) -> list:
    """Reducer that concatenates two lists."""
    return left + right


class OrchestratorState(TypedDict):
    task: str
    plan: dict
    agent_outputs: Annotated[dict, merge_dicts]
    final_output: str
    coverage_report: dict
    known_issues: Annotated[list, merge_lists]
    metadata: Annotated[dict, merge_dicts]
    shared_memory: Annotated[dict, merge_dicts]
