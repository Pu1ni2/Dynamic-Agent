"""
Tool definitions and executors for sub-agents.

Each tool has:
  - A JSON Schema definition (passed to the LLM so it knows how to call it)
  - An executor function (what actually runs when the LLM calls it)

The `spawn_specialist` tool is special — it creates a new SubAgent at runtime.
"""

import os
import subprocess


# ── JSON Schema definitions (what the LLM sees) ───────────────────────────────

ALL_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information on a topic. Returns a summary of findings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full contents of a local file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative or absolute file path"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a local file (creates or overwrites).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path":    {"type": "string", "description": "File path to write to"},
                    "content": {"type": "string", "description": "Text content to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_code",
            "description": "Analyze a snippet of code for bugs, security issues, or style problems.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code":  {"type": "string", "description": "The code to analyze"},
                    "focus": {
                        "type": "string",
                        "enum": ["security", "bugs", "performance", "style", "general"],
                        "description": "What to focus the analysis on",
                    },
                },
                "required": ["code", "focus"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Run a shell command and return stdout/stderr. Use with caution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spawn_specialist",
            "description": (
                "Spawn a new specialist sub-agent mid-task when you encounter work "
                "outside your expertise. The specialist runs immediately and returns its output."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "role":  {"type": "string", "description": "The specialist's role title"},
                    "goal":  {"type": "string", "description": "What this specialist must achieve"},
                    "tools": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tools the specialist needs",
                    },
                    "task":  {"type": "string", "description": "The specific task to hand off"},
                },
                "required": ["role", "goal", "tools", "task"],
            },
        },
    },
]


def get_schemas_for(tool_names: list[str]) -> list[dict]:
    """Return only the tool schemas the agent is allowed to use."""
    allowed = set(tool_names)
    return [t for t in ALL_TOOL_SCHEMAS if t["function"]["name"] in allowed]


# ── Executors ──────────────────────────────────────────────────────────────────

def execute_tool(name: str, args: dict, spawner=None) -> str:
    """
    Run a tool and return its result as a string.

    `spawner` is injected so that `spawn_specialist` can create real agents.
    """
    if name == "web_search":
        return _web_search(args["query"])

    if name == "read_file":
        return _read_file(args["path"])

    if name == "write_file":
        return _write_file(args["path"], args["content"])

    if name == "analyze_code":
        return _analyze_code(args["code"], args.get("focus", "general"))

    if name == "run_shell":
        return _run_shell(args["command"])

    if name == "spawn_specialist":
        if spawner is None:
            return "ERROR: spawn_specialist called but no spawner is available."
        return spawner.spawn_specialist(args)

    return f"ERROR: Unknown tool '{name}'"


# ── Tool implementations ───────────────────────────────────────────────────────

def _web_search(query: str) -> str:
    # Simulated — swap in a real search API (SerpAPI, Tavily, etc.) here
    return (
        f"[WEB SEARCH: '{query}']\n"
        "Simulated results — in production this calls a real search API.\n"
        "Key findings: multiple authoritative sources discuss this topic. "
        "Relevant papers and articles available. Proceed with analysis based on "
        "your training knowledge and flag that live search is simulated."
    )


def _read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content if content else "(file is empty)"
    except FileNotFoundError:
        return f"ERROR: File not found: {path}"
    except Exception as e:
        return f"ERROR reading {path}: {e}"


def _write_file(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to '{path}'"
    except Exception as e:
        return f"ERROR writing {path}: {e}"


def _analyze_code(code: str, focus: str) -> str:
    # Lightweight static summary — the sub-agent's LLM does the real reasoning
    lines = code.strip().splitlines()
    return (
        f"[CODE ANALYSIS — focus: {focus}]\n"
        f"Lines: {len(lines)} | Characters: {len(code)}\n"
        "Pass this code to the LLM for in-depth analysis using your expertise."
    )


def _run_shell(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout or ""
        errors = result.stderr or ""
        return (
            f"[EXIT CODE: {result.returncode}]\n"
            + (f"STDOUT:\n{output}" if output else "")
            + (f"STDERR:\n{errors}" if errors else "")
        ).strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 30 seconds"
    except Exception as e:
        return f"ERROR running command: {e}"
