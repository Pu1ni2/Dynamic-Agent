"""
Verification script — confirms sub-agents are actually being created and run.
Uses a hardcoded plan so no API key is needed for the spawning logic itself.

Each SubAgent.run() is mocked to print proof it was instantiated.
"""

from clawforge.agent_spawner import AgentSpawner
from clawforge.sub_agent import SubAgent

# ── 1. Hardcoded plan (what DynamicAgent would normally produce) ───────────────

MOCK_PLAN = {
    "task_summary": "Research AI agent frameworks, compare them, and write a report",
    "execution_order": "sequential",
    "reasoning": "Each agent has a distinct role; sequential so each can build on the previous.",
    "agents": [
        {
            "id": "agent_1",
            "role": "Research Analyst",
            "goal": "Gather information on the top 3 AI agent frameworks",
            "tools": ["web_search"],
            "model": "gpt-4o-mini",
            "depends_on": [],
        },
        {
            "id": "agent_2",
            "role": "Comparator",
            "goal": "Compare the frameworks found by the Research Analyst",
            "tools": ["web_search", "analyze_code"],
            "model": "gpt-4o",
            "depends_on": ["agent_1"],
        },
        {
            "id": "agent_3",
            "role": "Report Writer",
            "goal": "Write a structured markdown report with the comparison findings",
            "tools": ["write_file"],
            "model": "gpt-4o-mini",
            "depends_on": ["agent_2"],
        },
    ],
}

# ── 2. Monkey-patch SubAgent.run so we skip real LLM calls ────────────────────

_original_run = SubAgent.run

def mock_run(self, task: str, context: str = "") -> str:
    print(f"\n  [OK] SubAgent CREATED & RUNNING:")
    print(f"     id    : {self.id}")
    print(f"     role  : {self.role}")
    print(f"     goal  : {self.goal}")
    print(f"     tools : {self.tools}")
    print(f"     model : {self.model}")
    print(f"     context received: {'yes (' + str(len(context)) + ' chars)' if context else 'none (first agent)'}")
    return f"[MOCK OUTPUT from {self.role}]"

SubAgent.run = mock_run

# ── 3. Run the spawner with the mock plan ─────────────────────────────────────

print("\n" + "=" * 60)
print("  CLAWFORGE — Sub-Agent Creation Verification")
print("=" * 60)
print(f"\n  Plan has {len(MOCK_PLAN['agents'])} agents to spawn\n")

spawner = AgentSpawner()
results = spawner.run_from_plan(MOCK_PLAN, original_task="Research AI agent frameworks")

# ── 4. Summary ────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("  VERIFICATION SUMMARY")
print("=" * 60)
print(f"\n  Agents in plan   : {len(MOCK_PLAN['agents'])}")
print(f"  Agents spawned   : {spawner.total_agents_spawned}")
print(f"  Results returned : {len(results)}")
print()
for role, output in results.items():
    print(f"  [{role}] -> {output}")

print()
assert spawner.total_agents_spawned == 3, "Expected 3 agents"
assert len(results) == 3, "Expected 3 results"
print("  [PASS] All assertions passed -- sub-agents are being created correctly\n")
