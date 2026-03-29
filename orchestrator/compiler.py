"""
Compiler — the final node in the orchestration graph.
Assembles all sub-agent outputs into a single coherent deliverable.
"""

import json

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .config import OPENAI_API_KEY, COMPILER_MODEL
from .prompts import COMPILER_PROMPT
from .state import OrchestratorState
from .utils import parse_json_response, truncate
from .events import emit


# Module-level reference to memory (set by graph_builder via make_compile_node)
_memory = None


def set_compiler_memory(memory):
    global _memory
    _memory = memory


def compile_node(state: OrchestratorState) -> dict:
    """LangGraph node function. Assembles final deliverable."""

    print("\n[COMPILER] Assembling final output ...")
    emit("compile_start", {})

    model = ChatOpenAI(
        model=COMPILER_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.3,
        max_tokens=4096,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    agent_outputs_text = ""
    for agent_id, output in state.get("agent_outputs", {}).items():
        role = output.get("role", agent_id)
        text = truncate(output.get("output", ""), 6000)
        agent_outputs_text += f"\n### {role} ({agent_id})\n{text}\n"

    plan = state.get("plan", {})
    plan_agents = plan.get("agents", [])
    plan_summary = ""
    for a in plan_agents:
        plan_summary += f"- {a['id']} ({a.get('role', '?')}): {a.get('objective', '?')}\n"

    # Memory context for compiler
    memory_section = ""
    if _memory is not None:
        compiler_ctx = _memory.get_compiler_context(state["task"])
        if compiler_ctx:
            memory_section = f"--- PAST COMPILATION INSIGHTS ---\n{compiler_ctx}"

    # Include shared memory if agents stored anything
    shared_mem = state.get("shared_memory", {})
    if shared_mem:
        memory_section += "\n\n--- SHARED WORKSPACE DATA ---\n"
        for key, data in shared_mem.items():
            val = data.get("value", str(data)) if isinstance(data, dict) else str(data)
            memory_section += f"[{key}]: {val[:300]}\n"

    prompt = COMPILER_PROMPT.format(
        task=state["task"],
        plan_summary=plan_summary or "No plan details available",
        agent_outputs=agent_outputs_text or "No agent outputs available",
        memory_section=memory_section,
    )

    messages = [
        SystemMessage(content="You are the Compiler Agent. Return valid JSON only."),
        HumanMessage(content=prompt),
    ]

    try:
        response = model.invoke(messages)
        result = parse_json_response(response.content)

        final_output = result.get("final_output", "")
        coverage = result.get("coverage_report", {})
        issues = result.get("known_issues", [])
        recommendations = result.get("recommendations", [])

        print(f"[COMPILER] Done — {len(final_output)} chars")
        emit("compile_done", {"output_preview": final_output[:500]})

        return {
            "final_output": final_output,
            "coverage_report": coverage,
            "known_issues": issues,
            "metadata": {"recommendations": recommendations},
        }

    except Exception as exc:
        print(f"[COMPILER] JSON parse failed ({exc}), using raw concatenation")

        raw_output = "# Task Output\n\n"
        for agent_id, output in state.get("agent_outputs", {}).items():
            role = output.get("role", agent_id)
            raw_output += f"## {role}\n{output.get('output', '')}\n\n"

        emit("compile_done", {"output_preview": raw_output[:500]})

        return {
            "final_output": raw_output,
            "coverage_report": {"quality_assessment": "Compilation failed, raw outputs returned"},
            "known_issues": [f"Compiler error: {exc}"],
        }
