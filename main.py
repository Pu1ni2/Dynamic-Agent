"""
HIVEMIND — Autonomous Multi-Agent Orchestration Engine

Usage:
    python main.py
    python main.py "Organize a tech conference for 500 people"
    python main.py "Build a startup plan for an AI tutoring company"
"""

import sys
from orchestrator import run_task

DEFAULT_TASK = (
    "Organize a tech conference for 200 people in San Francisco. "
    "Create a complete plan including venue selection, budget breakdown, "
    "speaker lineup strategy, marketing plan, and day-of logistics."
)

task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TASK

result = run_task(task)

print("\n" + "=" * 70)
print("  FINAL DELIVERABLE")
print("=" * 70)
print(result["final_output"])

if result.get("known_issues"):
    print("\n--- KNOWN ISSUES ---")
    for issue in result["known_issues"]:
        print(f"  - {issue}")

if result.get("metadata"):
    meta = result["metadata"]
    print(f"\n--- STATS ---")
    print(f"  Total time: {meta.get('total_time_s', '?')}s")
    print(f"  Agents: {meta.get('total_agents', '?')}")
    print(f"  Tools forged: {meta.get('total_tools', '?')}")
