"""
DynamicAgent (Planner)
─────────────────────
Takes a user prompt and produces a structured JSON plan that describes
which sub-agents to spawn, their roles, goals, tools, and execution order.

This is the ONLY hardcoded agent — everything it produces is spawned at runtime.
"""

import json
import os
from openai import OpenAI


PLANNING_SYSTEM_PROMPT = """\
You are ClawForge's Dynamic Agent — the Planner.

Your job: analyze the user's task and design the optimal team of AI sub-agents
to accomplish it. You must think about:
  - What distinct roles are needed?
  - What tools does each role require?
  - What is the best execution order?
  - Which model tier fits each agent (powerful vs. fast)?

Output ONLY a valid JSON object with this exact structure — no extra text:

{
  "task_summary": "One-sentence summary of what needs to be done",
  "agents": [
    {
      "id": "agent_1",
      "role": "Descriptive role name (e.g. 'Research Analyst')",
      "goal": "Specific goal this agent must achieve",
      "tools": ["tool_a", "tool_b"],
      "model": "gpt-4o-mini",
      "depends_on": []
    }
  ],
  "execution_order": "sequential",
  "reasoning": "Why this team composition is optimal for the task"
}

Available tools (assign only what each agent actually needs):
  - web_search       : Search the web for information
  - read_file        : Read a local file's contents
  - write_file       : Write output to a local file
  - analyze_code     : Analyze code for bugs, patterns, or security issues
  - run_shell        : Execute a shell command and return output
  - spawn_specialist : Spawn a new expert agent mid-task if needed

Model guidelines:
  - "gpt-4o"      → complex reasoning, planning, analysis
  - "gpt-4o-mini" → summarization, formatting, writing, simple tasks

Rules:
  - Minimum 2 agents, maximum 6 agents.
  - Each agent must have a unique, focused role — no overlap.
  - "depends_on" lists agent IDs this agent needs output from.
  - Output ONLY the JSON — no markdown fences, no explanation.
"""


class DynamicAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),  # None = default OpenAI
        )
        self.planner_model = os.getenv("PLANNER_MODEL", "gpt-4o")

    def create_plan(self, user_task: str) -> dict:
        """
        Analyze the user's task and return a JSON plan for the agent team.

        Args:
            user_task: The raw prompt from the user.

        Returns:
            A dict with keys: task_summary, agents, execution_order, reasoning.
        """
        print(f"  [Planner] Analyzing task with {self.planner_model}...")

        response = self.client.chat.completions.create(
            model=self.planner_model,
            temperature=0.2,          # Low temp for consistent JSON
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
                {"role": "user",   "content": f"Design an agent team for this task:\n\n{user_task}"},
            ],
        )

        raw = response.choices[0].message.content
        plan = json.loads(raw)
        self._validate_plan(plan)
        return plan

    # ── private ───────────────────────────────────────────────────────────────

    def _validate_plan(self, plan: dict) -> None:
        required = {"task_summary", "agents", "execution_order", "reasoning"}
        missing = required - plan.keys()
        if missing:
            raise ValueError(f"Planner returned incomplete plan. Missing keys: {missing}")

        for agent in plan["agents"]:
            for field in ("id", "role", "goal", "tools", "model"):
                if field not in agent:
                    raise ValueError(f"Agent spec missing field '{field}': {agent}")
