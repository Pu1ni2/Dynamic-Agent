def create_debate_state(task: str) -> dict:
    """Initialize a fresh debate state for a given task."""
    return {
        "round": 0,
        "task": task,
        "plan": None,       # DA's current plan (dict)
        "history": [],      # list of {"role": "da"|"evaluator", "content": str}
        "approved": False,
    }


def add_to_history(state: dict, role: str, content: str) -> None:
    """Append a message to the debate history in-place."""
    state["history"].append({"role": role, "content": content})
