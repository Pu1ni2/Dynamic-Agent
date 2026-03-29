import json
from .debate import run_debate, _emit
from .dynamic_agent import DynamicAgent
from .prompts import (
    DA_GENERATE_REQUIREMENTS_PROMPT,
    EVALUATOR_CRITIQUE_REQUIREMENTS_PROMPT,
    DA_GENERATE_SUBAGENTS_PROMPT,
    EVALUATOR_CRITIQUE_SUBAGENTS_PROMPT,
)


def run_pipeline(task: str, tool_executor=None, emitter=None) -> dict:
    # ── Phase 1-2: Requirements Debate ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PHASE 1-2: Requirements Debate")
    print("=" * 60)

    _emit(emitter, {
        "type": "phase_start",
        "phase": "debate_requirements",
        "label": "Requirements Debate",
    })

    requirements = run_debate(
        task=task,
        generator_prompt=DA_GENERATE_REQUIREMENTS_PROMPT,
        critic_prompt=EVALUATOR_CRITIQUE_REQUIREMENTS_PROMPT,
        modified_key="modified_requirements",
        emitter=emitter,
        phase_name="requirements",
    )

    print(f"\n  Requirements approved.")

    # ── Phase 3-4: Plan Debate ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PHASE 3-4: Sub-Agent Plan Debate")
    print("=" * 60)

    _emit(emitter, {
        "type": "phase_start",
        "phase": "debate_plan",
        "label": "Sub-Agent Plan Debate",
    })

    req_context = f"Approved Requirements:\n{json.dumps(requirements, indent=2)}"

    plan_result = run_debate(
        task=task,
        generator_prompt=DA_GENERATE_SUBAGENTS_PROMPT,
        critic_prompt=EVALUATOR_CRITIQUE_SUBAGENTS_PROMPT,
        modified_key="modified_plan",
        input_context=req_context,
        emitter=emitter,
        phase_name="plan",
    )

    agents_list = plan_result.get("plan", []) if plan_result else []
    execution_strategy = plan_result.get("execution_strategy", {}) if plan_result else {}

    print(f"\n  Plan approved: {len(agents_list)} agents")

    _emit(emitter, {
        "type": "agents_spawned",
        "agents": [
            {
                "id": str(a.get("id", i)),
                "role": a.get("role", f"Agent {i}"),
                "model_tier": a.get("model_tier", "BALANCED"),
            }
            for i, a in enumerate(agents_list)
        ],
    })

    # ── Phase 5-6: Execute + Assemble ────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PHASE 5-6: Execution + Validation")
    print("=" * 60)

    _emit(emitter, {
        "type": "phase_start",
        "phase": "execution",
        "label": "Parallel Execution",
    })

    full_plan = {
        "task": task,
        "requirements": requirements,
        "plan": agents_list,
        "execution_strategy": execution_strategy,
    }

    da = DynamicAgent(full_plan, tool_executor=tool_executor, emitter=emitter)
    result = da.run()

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)

    return result
