import json
import anthropic
from config import CLAUDE_MODEL

client = anthropic.Anthropic()


def call_da(task: str, history: list) -> dict:
    """
    Dynamic Agent: proposes or revises a plan.
    Returns a dict with key 'plan' (list of sub-tasks).
    """
    system = (
        "You are a Dynamic Agent (DA). Your job is to decompose a user task into a clear, "
        "structured execution plan for sub-agents. "
        "You must respond ONLY with valid JSON in this exact format:\n"
        '{"plan": [{"id": 1, "role": "...", "objective": "..."}]}'
    )

    messages = _build_messages(task, history, speaker="da")

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=system,
        messages=messages,
    )

    return json.loads(response.content[0].text)


def call_evaluator(task: str, history: list) -> dict:
    """
    Evaluator Agent: critiques or approves the DA's plan.
    Returns a dict with 'approved' (bool) and optionally 'critique' (str).
    """
    system = (
        "You are an Evaluator Agent. Your job is to critically review execution plans. "
        "Check for: missing steps, ambiguous roles, edge cases not handled, and logical gaps. "
        "You must respond ONLY with valid JSON in one of these two formats:\n"
        '{"approved": true}\n'
        'or\n'
        '{"approved": false, "critique": "specific issues here"}'
    )

    messages = _build_messages(task, history, speaker="evaluator")

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        system=system,
        messages=messages,
    )

    return json.loads(response.content[0].text)


def _build_messages(task: str, history: list, speaker: str) -> list:
    """
    Convert debate history into the message format Claude expects.
    The 'speaker' param tells us whose turn it is next (so we frame context correctly).
    """
    messages = [{"role": "user", "content": f"Task: {task}"}]

    for entry in history:
        # Map debate roles to Claude's user/assistant alternation
        role = "assistant" if entry["role"] == speaker else "user"
        messages.append({"role": role, "content": entry["content"]})

    return messages
