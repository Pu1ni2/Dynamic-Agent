import json
from .sub_agent import SubAgent


class DynamicAgent:
    def __init__(self, plan_path: str):
        with open(plan_path, "r") as f:
            self.plan = json.load(f)

    def run(self):
        context = ""
        results = {}

        for agent_config in self.plan["agents"]:
            agent = SubAgent(role=agent_config["role"], goal=agent_config["goal"])
            print(f"\n[{agent.role}] running...")
            output = agent.run(self.plan["task"], context)
            print(output)
            results[agent.role] = output
            context += f"\n\n[{agent.role}]:\n{output}"

        return results
