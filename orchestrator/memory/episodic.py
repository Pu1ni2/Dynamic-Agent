"""Episode recorder — captures pipeline execution for later storage."""

from __future__ import annotations
import time
import uuid

from .types import Episode


class EpisodeRecorder:
    """Captures events during a single pipeline run and assembles an Episode."""

    def __init__(self):
        self.episode_id: str = uuid.uuid4().hex[:12]
        self.task: str = ""
        self.plan: dict = {}
        self.agent_outputs: dict = {}
        self.errors: list[str] = []
        self.start_time: float = 0

    def start(self, task: str):
        self.task = task
        self.start_time = time.time()

    def record_plan(self, plan: dict):
        self.plan = plan

    def record_agent_output(self, agent_id: str, role: str, output: str):
        self.agent_outputs[agent_id] = {"role": role, "output": output}

    def record_error(self, agent_id: str, error: str):
        self.errors.append(f"{agent_id}: {error}")

    def finalize(self, result: dict) -> Episode:
        """Build a complete Episode from recorded data + pipeline result."""
        plan = result.get("plan", self.plan)
        task_analysis = plan.get("task_analysis", {})

        # Auto-generate tags from domain + agent roles
        tags = []
        domain = task_analysis.get("domain", "")
        if domain:
            tags.append(domain.lower())
        for agent in plan.get("agents", []):
            role = agent.get("role", "")
            if role:
                tags.append(role.lower().replace(" ", "_"))

        return Episode(
            episode_id=self.episode_id,
            task=self.task,
            task_domain=domain,
            task_complexity=task_analysis.get("complexity", ""),
            plan=plan,
            agent_outputs=result.get("agent_outputs", self.agent_outputs),
            final_output=result.get("final_output", ""),
            coverage_report=result.get("coverage_report", {}),
            known_issues=result.get("known_issues", []) + self.errors,
            metadata={
                **result.get("metadata", {}),
                "episode_id": self.episode_id,
                "wall_time_s": round(time.time() - self.start_time, 2),
            },
            tags=tags,
        )
