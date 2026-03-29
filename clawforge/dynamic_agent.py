import json
import concurrent.futures
from .config import VALIDATION_MODEL, TIER_TO_MODEL
from .llm_client import call_llm_json
from .prompts import DA_COMPILE_FINAL_OUTPUT_PROMPT
from .sub_agent import SubAgent


def _emit(emitter, event: dict):
    if emitter:
        try:
            emitter(event)
        except Exception:
            pass


class DynamicAgent:
    def __init__(self, plan: dict, tool_executor=None, emitter=None):
        self.task = plan["task"]
        self.requirements = plan.get("requirements", {})
        self.agents_config = plan["plan"]
        self.execution_strategy = plan.get("execution_strategy", {})
        self.tool_executor = tool_executor
        self.emitter = emitter

    def run(self) -> dict:
        agents = self._resolve_agents()
        parallel_groups = self.execution_strategy.get("parallel_groups", {})

        if parallel_groups:
            results = self._run_grouped(agents, parallel_groups)
        else:
            results = self._run_sequential(agents)

        validated = self._validate(results)
        return validated

    def _resolve_agents(self) -> dict:
        agents = {}
        for a in self.agents_config:
            a["model"] = TIER_TO_MODEL.get(a.get("model_tier", "BALANCED"), TIER_TO_MODEL["BALANCED"])
            agents[a["id"]] = a
        return agents

    def _run_grouped(self, agents: dict, parallel_groups: dict) -> dict:
        outputs = {}

        for group_num in sorted(parallel_groups.keys(), key=lambda x: int(x)):
            agent_ids = parallel_groups[group_num]
            print(f"\n  Group {group_num}: agents {agent_ids}")

            group_agents = [agents[aid] for aid in agent_ids if aid in agents]

            with concurrent.futures.ThreadPoolExecutor() as pool:
                futures = {}
                for config in group_agents:
                    context = self._build_context(config, outputs)
                    agent = SubAgent(config, tool_executor=self.tool_executor)
                    print(f"  [{agent.role}] running...")
                    _emit(self.emitter, {
                        "type": "agent_started",
                        "agent_id": str(config["id"]),
                        "role": config["role"],
                    })
                    futures[pool.submit(agent.run, self.task, context)] = config

                for future in concurrent.futures.as_completed(futures):
                    config = futures[future]
                    try:
                        output = future.result()
                    except Exception as e:
                        output = f"Error: {e}"
                    outputs[config["id"]] = {"role": config["role"], "output": output}
                    print(f"  [{config['role']}] done")
                    _emit(self.emitter, {
                        "type": "agent_done",
                        "agent_id": str(config["id"]),
                        "role": config["role"],
                        "output": output,
                    })

        return outputs

    def _run_sequential(self, agents: dict) -> dict:
        outputs = {}
        for agent_id, config in agents.items():
            context = self._build_context(config, outputs)
            agent = SubAgent(config, tool_executor=self.tool_executor)
            print(f"\n  [{agent.role}] running...")
            _emit(self.emitter, {
                "type": "agent_started",
                "agent_id": str(agent_id),
                "role": config["role"],
            })
            output = agent.run(self.task, context)
            outputs[agent_id] = {"role": config["role"], "output": output}
            print(f"  [{config['role']}] done")
            _emit(self.emitter, {
                "type": "agent_done",
                "agent_id": str(agent_id),
                "role": config["role"],
                "output": output,
            })
        return outputs

    def _build_context(self, config: dict, outputs: dict) -> str:
        deps = config.get("context_from_agents", [])
        if not deps:
            return ""
        parts = []
        for dep_id in deps:
            if dep_id in outputs:
                dep = outputs[dep_id]
                parts.append(f"[{dep['role']}]:\n{dep['output']}")
        return "\n\n".join(parts)

    def _validate(self, outputs: dict) -> dict:
        agent_outputs = ""
        for aid, data in outputs.items():
            agent_outputs += f"\n[Agent {aid} — {data['role']}]:\n{data['output']}\n"

        print("\n  [DA] Validating and compiling final output...")
        _emit(self.emitter, {
            "type": "phase_start",
            "phase": "assembly",
            "label": "Final Assembly",
        })

        result = call_llm_json(
            VALIDATION_MODEL,
            messages=[
                {"role": "system", "content": DA_COMPILE_FINAL_OUTPUT_PROMPT},
                {"role": "user", "content": (
                    f"Original user request: {self.task}\n\n"
                    f"Requirements:\n{json.dumps(self.requirements, indent=2)}\n\n"
                    f"Plan:\n{json.dumps(self.agents_config, indent=2)}\n\n"
                    f"Sub-agent outputs:\n{agent_outputs}"
                )},
            ],
        )

        print("  [DA] Validation complete")
        final_output = result.get("final_output", "")
        _emit(self.emitter, {
            "type": "final_output",
            "content": final_output,
            "coverage_report": result.get("coverage_report", {}),
            "known_issues": result.get("known_issues", []),
        })

        return {
            "final_output": final_output,
            "coverage_report": result.get("coverage_report", {}),
            "known_issues": result.get("known_issues", []),
            "agent_outputs": outputs,
        }
