import json
import os
import concurrent.futures
from openai import OpenAI
from .sub_agent import SubAgent

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class DynamicAgent:
    def __init__(self, plan_path: str, tool_executor=None):
        with open(plan_path, "r") as f:
            self.plan = json.load(f)
        self.tool_executor = tool_executor  # comes from LangGraph

    def run(self):
        order = self.plan.get("execution_order", "sequential")

        if order == "parallel":
            results = self._run_parallel()
        else:
            results = self._run_sequential()

        validated = self._validate(results)
        return validated

    def _run_sequential(self):
        context = ""
        results = {}

        for agent_config in self.plan["agents"]:
            agent = SubAgent(
                role=agent_config["role"],
                goal=agent_config["goal"],
                tools=agent_config.get("tools", []),
                tool_executor=self.tool_executor,
            )
            print(f"\n[{agent.role}] running...")
            output = agent.run(self.plan["task"], context)
            print(output)
            results[agent.role] = output
            context += f"\n\n[{agent.role}]:\n{output}"

        return results

    def _run_parallel(self):
        results = {}
        agents = [
            SubAgent(role=a["role"], goal=a["goal"], tools=a.get("tools", []), tool_executor=self.tool_executor)
            for a in self.plan["agents"]
        ]

        print(f"\nRunning {len(agents)} agents in parallel...")

        with concurrent.futures.ThreadPoolExecutor() as pool:
            futures = {pool.submit(a.run, self.plan["task"]): a for a in agents}
            for future in concurrent.futures.as_completed(futures):
                agent = futures[future]
                output = future.result()
                print(f"\n[{agent.role}] done.")
                print(output)
                results[agent.role] = output

        return results

    def _validate(self, results: dict) -> dict:
        combined = ""
        for role, output in results.items():
            combined += f"\n[{role}]:\n{output}\n"

        print("\n[Dynamic Agent] validating results...")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "You are the Dynamic Agent. Your job is to validate the combined output "
                    "from all sub-agents. Check if the original task was fully answered. "
                    "If yes, return the final consolidated answer. "
                    "If something is missing or wrong, point out what needs fixing."
                )},
                {"role": "user", "content": (
                    f"Original task: {self.plan['task']}\n\n"
                    f"Sub-agent outputs:\n{combined}\n\n"
                    "Validate and return the final answer."
                )},
            ],
        )

        final_answer = response.choices[0].message.content
        print("\n[Dynamic Agent] validation complete.")
        return {"agent_results": results, "final_answer": final_answer}
