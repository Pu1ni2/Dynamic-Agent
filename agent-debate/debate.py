import json
from config import MAX_ROUNDS
from state import create_debate_state, add_to_history
from agents import call_da, call_evaluator


def run_debate(task: str) -> dict:
    """
    Run the DA ↔ Evaluator debate loop.
    Returns the final debate state with the approved (or best-effort) plan.
    """
    state = create_debate_state(task)

    while state["round"] < MAX_ROUNDS and not state["approved"]:
        state["round"] += 1
        print(f"\n--- Round {state['round']} ---")

        # Step 1: DA proposes / revises plan
        da_response = call_da(task, state["history"])
        state["plan"] = da_response.get("plan")
        da_content = json.dumps(da_response)
        add_to_history(state, role="da", content=da_content)
        print(f"[DA]        {da_content}")

        # Step 2: Evaluator critiques or approves
        eval_response = call_evaluator(task, state["history"])
        eval_content = json.dumps(eval_response)
        add_to_history(state, role="evaluator", content=eval_content)
        print(f"[Evaluator] {eval_content}")

        if eval_response.get("approved"):
            state["approved"] = True
            print("\nEvaluator APPROVED the plan.")
        else:
            print(f"\nEvaluator REJECTED. Critique: {eval_response.get('critique')}")

    if not state["approved"]:
        print(f"\nMax rounds ({MAX_ROUNDS}) reached. Using last plan as-is.")

    return state


if __name__ == "__main__":
    task = "Research the top 3 AI frameworks in 2025 and summarize their pros and cons."
    final_state = run_debate(task)

    print("\n=== FINAL STATE ===")
    print(json.dumps(final_state, indent=2))
