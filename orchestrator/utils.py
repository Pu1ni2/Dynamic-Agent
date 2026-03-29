"""Shared helpers used across the orchestrator package."""

import json
import re


def parse_json_response(text: str) -> dict:
    """Parse JSON from an LLM response, stripping markdown fences if present."""
    text = text.strip()

    # Strip ```json ... ``` or ``` ... ```
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()

    return json.loads(text)


def truncate(text: str, max_chars: int = 12000) -> str:
    """Truncate text to max_chars, appending an ellipsis if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n... [truncated]"
