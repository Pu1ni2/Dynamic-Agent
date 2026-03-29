"""
Agent Factory — creates LangGraph react agents from plan specs + forged tools.

Each sub-agent is a `create_react_agent` instance that handles the
ReAct tool-calling loop internally.  The factory also produces *node
wrapper functions* that bridge the outer OrchestratorState with each
agent's internal MessagesState.
"""

from __future__ import annotations
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from .config import OPENAI_API_KEY, TIER_TO_MODEL, MAX_AGENT_STEPS
from .prompts import AGENT_SYSTEM_PROMPT
from .state import OrchestratorState
from .utils import truncate


def create_all_agents(
    plan: dict,
    agent_tools: dict[str, list],
    mcp_tools: list | None = None,
) -> dict[str, dict]:
    """Build react agents for every agent in the plan.

    Returns {agent_id: {"agent": CompiledGraph, "spec": dict}}
    """
    agents = {}
    task = plan.get("task_analysis", {}).get("domain", "")

    for spec in plan.get("agents", []):
        agent_id = spec["id"]
        model_name = TIER_TO_MODEL.get(spec.get("model_tier", "BALANCED"), "gpt-4o")

        model = ChatOpenAI(
            model=model_name,
            api_key=OPENAI_API_KEY,
            temperature=0.5,
        )

        # Combine forged tools + any MCP tools
        tools = list(agent_tools.get(agent_id, []))
        if mcp_tools:
            tools.extend(mcp_tools)

        # Build system prompt
        tool_names = ", ".join(t.name for t in tools) if tools else "none"
        system_prompt = AGENT_SYSTEM_PROMPT.format(
            role=spec.get("role", "Agent"),
            persona=spec.get("persona", ""),
            objective=spec.get("objective", ""),
            task=task,
            context_section="",  # filled at runtime by node wrapper
            tool_names=tool_names,
            expected_output=spec.get("expected_output", ""),
        )

        # Create the react agent
        agent = create_react_agent(
            model=model,
            tools=tools if tools else [],
            prompt=system_prompt,
        )

        agents[agent_id] = {"agent": agent, "spec": spec}
        print(f"[FACTORY] {agent_id} ({spec.get('role', '?')}) created "
              f"| model={model_name} | tools={len(tools)}")

    return agents


def make_agent_node(agent_id: str, agent_bundle: dict) -> Any:
    """Return a node function compatible with the outer OrchestratorState graph.

    The node function:
      1. Reads dependent agent outputs from state.
      2. Builds an input message with task context.
      3. Invokes the react agent.
      4. Writes the output back to state["agent_outputs"].
    """
    agent = agent_bundle["agent"]
    spec = agent_bundle["spec"]
    depends_on = spec.get("depends_on", [])
    role = spec.get("role", agent_id)
    objective = spec.get("objective", "")

    def node_fn(state: OrchestratorState) -> dict:
        # Build context from upstream agent outputs
        context_parts = []
        for dep_id in depends_on:
            dep_output = state.get("agent_outputs", {}).get(dep_id)
            if dep_output:
                dep_role = dep_output.get("role", dep_id)
                dep_text = truncate(dep_output.get("output", ""), 8000)
                context_parts.append(f"=== Output from {dep_role} ({dep_id}) ===\n{dep_text}")

        context_block = "\n\n".join(context_parts) if context_parts else ""

        # Compose the user message
        user_msg = (
            f"TASK: {state['task']}\n\n"
            f"YOUR ROLE: {role}\n"
            f"YOUR OBJECTIVE: {objective}\n"
        )
        if context_block:
            user_msg += f"\nCONTEXT FROM OTHER AGENTS:\n{context_block}\n"
        user_msg += "\nExecute your objective now.  Use your tools as needed."

        print(f"\n[AGENT] {agent_id} ({role}) starting ...")

        try:
            result = agent.invoke(
                {"messages": [HumanMessage(content=user_msg)]},
                config={"recursion_limit": MAX_AGENT_STEPS},
            )

            # Extract final answer from the last AI message
            final_content = ""
            for msg in reversed(result.get("messages", [])):
                if hasattr(msg, "content") and msg.content and msg.type == "ai":
                    final_content = msg.content
                    break

            if not final_content:
                final_content = "[Agent produced no output]"

            print(f"[AGENT] {agent_id} done ({len(final_content)} chars)")

        except Exception as exc:
            final_content = f"[Agent {agent_id} error: {exc}]"
            print(f"[AGENT] {agent_id} FAILED: {exc}")

        return {
            "agent_outputs": {
                agent_id: {
                    "role": role,
                    "output": final_content,
                }
            }
        }

    node_fn.__name__ = agent_id  # LangGraph uses the function name as node label
    return node_fn
