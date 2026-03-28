"""
AgentSpawner
────────────
Reads the plan produced by DynamicAgent and:
  1. Instantiates a SubAgent for every agent in the plan.
  2. Runs them in the declared execution order, passing prior outputs as context.
  3. Handles mid-task self-spawning when a SubAgent calls spawn_specialist().

AgentSpawner is injected into every SubAgent so they can call spawn_specialist()
at any point during execution.
"""

import os
from .sub_agent import SubAgent


class AgentSpawner:
    def __init__(self):
        self._spawned: list[SubAgent] = []   # all agents created (plan + self-spawned)

    # ── public ────────────────────────────────────────────────────────────────

    def run_from_plan(self, plan: dict, original_task: str) -> dict[str, str]:
        """
        Instantiate and run every agent in the plan.

        Args:
            plan:          JSON plan produced by DynamicAgent.
            original_task: The original user prompt (passed to every agent).

        Returns:
            Dict mapping role → output for every agent that ran.
        """
        agents_config   = plan["agents"]
        execution_order = plan.get("execution_order", "sequential")

        print(f"\n  Spawning {len(agents_config)} agent(s) — order: {execution_order}")

        results: dict[str, str] = {}
        context = ""                          # grows as each agent completes

        if execution_order == "sequential":
            for config in agents_config:
                agent  = self._create_agent(config)
                output = agent.run(original_task, context)
                results[agent.role] = output
                context += f"\n\n[{agent.role}]:\n{output}"

        elif execution_order == "parallel":
            # Run all agents with empty context (they can't see each other's output)
            import concurrent.futures
            agents = [self._create_agent(c) for c in agents_config]
            with concurrent.futures.ThreadPoolExecutor() as pool:
                futures = {pool.submit(a.run, original_task, ""): a for a in agents}
                for future, agent in futures.items():
                    results[agent.role] = future.result()

        else:
            # Fallback: treat unknown order as sequential
            for config in agents_config:
                agent  = self._create_agent(config)
                output = agent.run(original_task, context)
                results[agent.role] = output
                context += f"\n\n[{agent.role}]:\n{output}"

        return results

    def spawn_specialist(self, spec: dict) -> str:
        """
        Called by a SubAgent at runtime via the spawn_specialist tool.
        Creates a new SubAgent on the fly and runs it immediately.

        Args:
            spec: dict with keys role, goal, tools, task.

        Returns:
            The specialist's output as a string.
        """
        idx = len(self._spawned) + 1
        config = {
            "id":    f"specialist_{idx}",
            "role":  spec["role"],
            "goal":  spec["goal"],
            "tools": spec.get("tools", []),
            "model": os.getenv("DEFAULT_AGENT_MODEL", "gpt-4o-mini"),
        }

        print(f"\n  *** SELF-SPAWN #{idx}: '{spec['role']}' created mid-task ***")

        specialist = self._create_agent(config)
        output     = specialist.run(spec["task"])

        print(f"  *** SELF-SPAWN #{idx} complete ***")
        return f"[Specialist '{spec['role']}' output]:\n{output}"

    @property
    def total_agents_spawned(self) -> int:
        return len(self._spawned)

    # ── private ───────────────────────────────────────────────────────────────

    def _create_agent(self, config: dict) -> SubAgent:
        agent = SubAgent(config, spawner=self)
        self._spawned.append(agent)
        return agent
