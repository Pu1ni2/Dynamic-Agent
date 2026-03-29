"""
DA <-> Evaluator debate loop.

The Dynamic Agent proposes a plan, the Evaluator critiques it.
They iterate until the plan is approved or MAX_DEBATE_ROUNDS is reached.
"""

import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .config import OPENAI_API_KEY, PLANNER_MODEL, EVALUATOR_MODEL, MAX_DEBATE_ROUNDS
from .prompts import DA_PLAN_PROMPT, EVALUATOR_CRITIQUE_PROMPT
from .utils import parse_json_response


def run_debate(task: str) -> dict:
    """Run the DA <-> Evaluator debate and return the approved plan dict."""

    da_model = ChatOpenAI(
        model=PLANNER_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.7,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    eval_model = ChatOpenAI(
        model=EVALUATOR_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.3,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    # ── Phase 1: DA generates initial plan ──────────────────────────────
    print("\n[DA] Generating initial plan ...")
    da_messages = [
        SystemMessage(content=DA_PLAN_PROMPT),
        HumanMessage(content=f"Task:\n{task}"),
    ]

    da_response = da_model.invoke(da_messages)
    plan = parse_json_response(da_response.content)
    _print_plan_summary(plan)

    # ── Phase 2: Debate rounds ──────────────────────────────────────────
    for round_num in range(1, MAX_DEBATE_ROUNDS + 1):
        print(f"\n[EVALUATOR] Critique round {round_num} ...")

        eval_messages = [
            SystemMessage(content=EVALUATOR_CRITIQUE_PROMPT),
            HumanMessage(
                content=(
                    f"Task:\n{task}\n\n"
                    f"Plan:\n{json.dumps(plan, indent=2)}"
                )
            ),
        ]

        eval_response = eval_model.invoke(eval_messages)
        critique = parse_json_response(eval_response.content)

        score = critique.get("score", 0)
        approved = critique.get("approved", False)
        verdict = critique.get("verdict", "NEEDS_REVISION")
        issues = critique.get("issues", [])

        print(f"  Score: {score}/10 | Verdict: {verdict}")
        for issue in issues:
            sev = issue.get("severity", "?")
            desc = issue.get("description", "")
            print(f"  [{sev}] {desc}")

        if approved or verdict == "APPROVED":
            # Use the evaluator's modified plan if it's a polished version
            if critique.get("modified_plan") and isinstance(critique["modified_plan"], dict):
                # Only use it if it actually has agents
                if critique["modified_plan"].get("agents"):
                    plan = critique["modified_plan"]
            print(f"\n[DEBATE] Plan APPROVED in round {round_num}")
            return plan

        # ── Plan needs revision ─────────────────────────────────────────
        if critique.get("modified_plan") and isinstance(critique["modified_plan"], dict):
            if critique["modified_plan"].get("agents"):
                plan = critique["modified_plan"]
                print(f"  -> Using evaluator's revised plan")
                continue

        # Ask DA to revise based on critique
        print(f"  -> DA revising plan ...")
        da_messages.append(AIMessage(content=json.dumps(plan)))
        da_messages.append(
            HumanMessage(
                content=(
                    f"The Evaluator found issues with your plan.\n\n"
                    f"Critique:\n{json.dumps(critique, indent=2)}\n\n"
                    f"Revise the plan to address ALL issues.  "
                    f"Return the complete updated plan JSON."
                )
            )
        )

        da_response = da_model.invoke(da_messages)
        plan = parse_json_response(da_response.content)
        _print_plan_summary(plan)

    print(f"\n[DEBATE] Max rounds ({MAX_DEBATE_ROUNDS}) reached — using last plan")
    return plan


def _print_plan_summary(plan: dict) -> None:
    """Print a compact summary of the plan."""
    agents = plan.get("agents", [])
    analysis = plan.get("task_analysis", {})
    print(f"  Domain: {analysis.get('domain', '?')} | "
          f"Complexity: {analysis.get('complexity', '?')} | "
          f"Agents: {len(agents)}")
    for a in agents:
        tools = [t["name"] for t in a.get("tools_needed", [])]
        print(f"    {a['id']}: {a['role']} | tools={tools} | group={a.get('parallel_group')}")
