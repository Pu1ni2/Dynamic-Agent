"""
ClawForge — Dynamic Agent Creation
────────────────────────────────────
Run:
    python main.py
    python main.py "Your custom task here"

Flow:
    1. DynamicAgent  → analyzes the task → produces a JSON agent plan
    2. AgentSpawner  → reads the plan → spawns + runs each sub-agent
    3. Each SubAgent → uses tools, optionally self-spawns specialists
    4. Results       → aggregated and printed
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

from clawforge import DynamicAgent, AgentSpawner


DEFAULT_TASK = (
    "Research the latest trends in AI agent frameworks, "
    "compare their key capabilities, and write a structured report "
    "with findings and recommendations."
)


def main():
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TASK

    print("\n" + "═" * 70)
    print("  CLAWFORGE  —  Dynamic Agent Creation")
    print("═" * 70)
    print(f"\n  Task: {task}\n")

    # ── Step 1: Dynamic Agent creates the plan ────────────────────────────────
    print("─" * 70)
    print("  STEP 1 — Dynamic Agent: analyzing task and creating agent plan")
    print("─" * 70)

    planner = DynamicAgent()
    plan    = planner.create_plan(task)

    print(f"\n  Summary : {plan['task_summary']}")
    print(f"  Order   : {plan['execution_order']}")
    print(f"  Agents  : {len(plan['agents'])}\n")

    for i, agent in enumerate(plan["agents"], 1):
        tools_str = ", ".join(agent["tools"]) or "none"
        print(f"  {i}. [{agent['id']}] {agent['role']}")
        print(f"     Goal : {agent['goal']}")
        print(f"     Tools: {tools_str}  |  Model: {agent['model']}")
        if agent.get("depends_on"):
            print(f"     Deps : {agent['depends_on']}")
        print()

    print(f"  Planner reasoning: {plan['reasoning']}\n")

    # ── Step 2: Spawn and run agents ──────────────────────────────────────────
    print("─" * 70)
    print("  STEP 2 — AgentSpawner: spawning and running sub-agents")
    print("─" * 70)

    spawner = AgentSpawner()
    results = spawner.run_from_plan(plan, task)

    # ── Step 3: Show results ──────────────────────────────────────────────────
    print("\n" + "═" * 70)
    print("  STEP 3 — Final Results")
    print("═" * 70)

    for role, output in results.items():
        print(f"\n  ┌─ {role}")
        for line in output.splitlines():
            print(f"  │  {line}")
        print(f"  └─")

    print(f"\n  Total agents used: {spawner.total_agents_spawned}")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    main()
