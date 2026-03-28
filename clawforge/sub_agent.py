"""
SubAgent
────────
A single spawned agent. Each instance has a fixed role, goal, and tool set.
It runs an agentic tool-use loop: calls the LLM, executes any tools it requests,
feeds results back, and repeats until the LLM is done.

Sub-agents can also call spawn_specialist() to create new agents mid-task.
"""

import json
import os
from openai import OpenAI
from .tools import get_schemas_for, execute_tool


class SubAgent:
    def __init__(self, config: dict, spawner=None):
        """
        Args:
            config:  Agent spec from the plan — must include id, role, goal, tools, model.
            spawner: AgentSpawner reference so this agent can call spawn_specialist.
        """
        self.id      = config["id"]
        self.role    = config["role"]
        self.goal    = config["goal"]
        self.tools   = config.get("tools", [])
        self.model   = config.get("model", os.getenv("DEFAULT_AGENT_MODEL", "gpt-4o-mini"))
        self.spawner = spawner
        self._client = None   # created lazily on first run() call

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
            )
        return self._client

    # ── public ────────────────────────────────────────────────────────────────

    def run(self, task: str, context: str = "") -> str:
        """
        Execute the agent's task.

        Args:
            task:    The original user task (shared across all agents).
            context: Aggregated output from agents that ran before this one.

        Returns:
            The agent's final text output.
        """
        print(f"\n  ► [{self.id}] {self.role}")
        print(f"    Goal : {self.goal}")
        print(f"    Tools: {', '.join(self.tools) or 'none'}")
        print(f"    Model: {self.model}")

        tool_schemas = get_schemas_for(self.tools)
        messages     = self._build_initial_messages(task, context)

        # Agentic loop — keep going until the LLM stops calling tools
        iteration = 0
        while True:
            iteration += 1
            kwargs = dict(
                model=self.model,
                messages=messages,
                temperature=0.3,
            )
            if tool_schemas:
                kwargs["tools"]       = tool_schemas
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            message  = response.choices[0].message

            # No tool calls → the agent is done
            if not message.tool_calls:
                result = message.content or "(agent produced no output)"
                print(f"    ✓ Done after {iteration} iteration(s)")
                return result

            # Execute every tool call the LLM requested
            messages.append(message)  # add assistant message with tool_calls

            for tc in message.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)

                print(f"    → tool: {tool_name}({_short(tool_args)})")
                result = execute_tool(tool_name, tool_args, spawner=self.spawner)
                print(f"      ✓ {_short_str(result)}")

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      result,
                })

    # ── private ───────────────────────────────────────────────────────────────

    def _build_initial_messages(self, task: str, context: str) -> list[dict]:
        system = (
            f"You are the **{self.role}** in a multi-agent system.\n\n"
            f"Your goal: {self.goal}\n\n"
            "Use your assigned tools to accomplish this goal thoroughly.\n"
            "If you encounter work that requires expertise outside your role, "
            "use `spawn_specialist` to delegate it — do not guess.\n"
            "When finished, write a clear, structured summary of your output."
        )

        user_content = f"Task: {task}"
        if context:
            user_content += f"\n\n---\nContext from agents that ran before you:\n{context}"

        return [
            {"role": "system",  "content": system},
            {"role": "user",    "content": user_content},
        ]


# ── helpers ───────────────────────────────────────────────────────────────────

def _short(d: dict, max_len: int = 80) -> str:
    s = ", ".join(f"{k}={repr(v)[:30]}" for k, v in d.items())
    return s[:max_len] + "…" if len(s) > max_len else s


def _short_str(s: str, max_len: int = 60) -> str:
    s = s.replace("\n", " ")
    return s[:max_len] + "…" if len(s) > max_len else s
