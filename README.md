# HiveMind

**A dynamic multi-agent orchestration engine with adversarial debate, runtime tool forging, plan-driven sub-agent spawning, persistent cross-run memory, and real-world integration capabilities.**

Built with LangGraph, FastAPI, and OpenAI GPT-4o.

---

## The Problem

Multi-agent AI systems fail in three recurring ways:

1. **Static rosters** — Frameworks like CrewAI and AutoGen require agents to be predefined. The roster can't adapt to the task; the task is forced to fit the roster.
2. **Unvalidated decomposition** — Orchestrators decompose tasks and execute immediately with no quality gate. Bad plans only fail at the end, after wasting time and tokens.
3. **Memory isolation** — Sub-agents work in silos. Agent A produces research, Agent B never sees it. No framework learns across runs — every task starts cold.

---

## How HiveMind Solves It

### Full Pipeline

```
Task Input
    ↓
Quick Classifier  (one tool call? skip the swarm)
    ↓
Adversarial Debate  (DA proposes → EA critiques → iterate up to 3 rounds)
    ↓
Tool Forge  (GPT-4o writes Python tools from specs, AST-validated)
    ↓
Agent Factory  (creates ReAct agents from approved plan)
    ↓
Graph Builder  (dependency-aware DAG, parallel where possible)
    ↓
Execution  (LangGraph state machine, shared workspace)
    ↓
Compiler  (synthesizes all agent outputs into final deliverable)
    ↓
Output  (with coverage report, known issues, recommendations)
```

### Key Innovations

**1. Adversarial Debate Gate**
Before any agent runs, a Dynamic Agent (DA) proposes a plan and a separate Evaluator Agent (EA) critiques it across 7 dimensions: coverage, agent roles, tool feasibility, dependency logic, overkill, underkill, and tool description specificity. The EA can rewrite the plan. Debate converges at score ≥ 6 with no CRITICAL issues, or after a hard cap of 3 rounds.

**2. Quick Action Intelligence**
A GPT-4o classifier checks whether the task needs a full swarm at all. If it can be resolved with 1–3 direct tool calls (send email, search web, create form), it executes those directly and returns — bypassing debate, forge, and graph construction entirely.

**3. Runtime Tool Forge**
Sub-agents never use hardcoded tools. After debate, the Tool Forge asks GPT-4o to write a Python function for each tool spec, validates it with `ast.parse()` + an AST visitor that blocks dangerous imports/calls, and execs it into a capability namespace. The result is a typed LangChain `StructuredTool`. Tools are cached by name.

**4. Persistent Cross-Run Memory**
Two memory layers run simultaneously:
- **Short-term (intra-run):** Shared workspace — agents call `remember(key, value)` / `recall(key)` as injected LangChain tools
- **Long-term (cross-run):** SQLite episodic store + ChromaDB vector search — episodes are distilled into `plan_pattern`, `lesson_learned`, `agent_strategy`, `user_preference` entries that shape future runs

**5. Real-Time Transparency**
Every phase streams to the frontend over WebSocket: debate rounds with character-level plan diffs, per-tool forge status, streaming agent tokens, tool call previews, and the final compiled output. Post-run, users can open an interactive chat with any individual agent.

---

## Architecture

### Agent Roles

| Agent | Role | Config |
|---|---|---|
| Dynamic Agent (DA) | Proposes ExecutionPlan JSON, defends in debate | GPT-4o, temp 0.7, memory context injected |
| Evaluator Agent (EA) | Adversarial reviewer, scores 7 dimensions, rewrites plan | GPT-4o, temp 0.3, "find problems" mandate |
| Quick Classifier | Pre-pipeline mode selector (quick vs full_pipeline) | GPT-4o, temp 0, JSON mode |
| Tool Forge | Generates Python tools from specs, AST-validates, execs | GPT-4o, temp 0, max_tokens 2048, 1 retry |
| Sub-Agents (SA-1..N) | ReAct workers spawned from approved plan at runtime | create_react_agent(), MAX_AGENT_STEPS=25 |
| Compiler | Synthesizes all agent outputs into coherent deliverable | GPT-4o, temp 0.3, JSON mode |
| Memory Manager | Cross-run learning via SQLite + ChromaDB | Episodic store + semantic vector search |

### Directory Structure

```
├── api/
│   └── app.py               # FastAPI server (REST + WebSocket)
├── orchestrator/
│   ├── pipeline.py          # Main entry point: run_task()
│   ├── debate.py            # DA ↔ EA debate loop
│   ├── quick_actions.py     # Quick action classifier + executor
│   ├── tool_forge.py        # LLM code generation → StructuredTool
│   ├── agent_factory.py     # ReAct agent creation from specs
│   ├── graph_builder.py     # LangGraph DAG construction
│   ├── compiler.py          # Final output synthesis
│   ├── capabilities.py      # 13 built-in capability functions
│   ├── integrations.py      # Email, Slack, Calendar, webhooks
│   ├── events.py            # WebSocket event bus
│   ├── mcp_client.py        # Model Context Protocol client
│   ├── state.py             # LangGraph state schema
│   ├── config.py            # Models, limits, env loading
│   └── memory/
│       ├── store.py         # SQLite episodic storage
│       ├── episodic.py      # Episode recording
│       ├── long_term.py     # Cross-run learning
│       ├── short_term.py    # Intra-run shared workspace
│       └── embeddings.py    # ChromaDB semantic search
├── frontend/
│   ├── index.html           # Dashboard UI
│   ├── css/style.css        # Dark-theme styling
│   └── js/app.js            # WebSocket streaming + diff rendering
├── main.py                  # CLI entry point
├── run_server.py            # Start web server
├── evaluate.py              # Single-LLM vs pipeline benchmark
└── requirements.txt
```

---

## Built-In Capabilities

Available to all forged tools via capability namespace injection:

| Capability | Description |
|---|---|
| `search_web(query)` | DuckDuckGo search with HTML fallback |
| `scrape_url(url)` | Fetch + extract webpage text |
| `save_file(filename, content)` | Write to `output/` (sandboxed) |
| `read_file(filepath)` | Read from `output/` |
| `fetch_json(url)` | HTTP GET → JSON |
| `compute(code_str)` | Restricted Python (math, stats, datetime) |
| `create_html_form(...)` | Generate interactive HTML forms |
| `send_email(...)` | SMTP email (degrades to draft file) |
| `send_slack_message(...)` | Slack webhook (degrades to draft file) |
| `create_calendar_event(...)` | `.ics` file for Google/Outlook/Apple |
| `create_spreadsheet(...)` | CSV/Excel via openpyxl |
| `create_kanban_board(...)` | Interactive drag-and-drop HTML board |
| `read_pdf(filepath)` | PDF text extraction via pdfplumber |

All integrations degrade gracefully — useful artifacts are always produced even without external credentials.

---

## API Reference

### REST

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/run` | Synchronous task execution |
| `POST` | `/api/chat` | Chat with an individual agent post-run |
| `GET` | `/api/files` | List generated output files |
| `GET` | `/api/files/{filename}` | Retrieve file content |
| `POST` | `/api/feedback` | Rate a run (creates `user_preference` memory) |
| `GET` | `/api/memory/episodes` | Browse past executions |
| `GET` | `/api/memory/search?query=...` | Semantic search across memory |
| `GET` | `/api/memory/stats` | Memory system statistics |

### WebSocket

```
WebSocket /ws
Send:    {"task": "<string>"}
Receive: {"type": "<event>", "data": {...}, "ts": "<ISO>"}
```

**Streamed event types:** `pipeline_start`, `quick_detect_start/done`, `quick_action`, `debate_start`, `debate_da_response`, `debate_eval_response`, `debate_complete`, `forge_start`, `forge_tool_start/done`, `forge_complete`, `graph_built`, `agent_token`, `agent_tool_call`, `agent_tool_result`, `compile_start/done`, `memory_recall/store`, `episode_saved`, `pipeline_done/error`

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- OpenAI API key

### Install

```bash
git clone <repo-url>
cd Dynamic-Agent

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env — set OPENAI_API_KEY at minimum
```

### Environment Variables

**Required:**

```env
OPENAI_API_KEY=sk-...
```

**Optional integrations:**

```env
# Email (degrades to draft files if not set)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASS=app-password
SMTP_FROM=you@example.com

# Slack (degrades to draft files if not set)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Google Calendar (optional — .ics always works)
GOOGLE_CALENDAR_CREDENTIALS=path/to/service-account.json

# MCP servers config
MCP_CONFIG_PATH=mcp_servers.json
```

### MCP Servers (optional)

```bash
cp mcp_servers.json.example mcp_servers.json
# Edit to enable filesystem, Slack, GitHub, Notion, etc.
```

---

## Running HiveMind

### Web UI (recommended)

```bash
python run_server.py
# Open http://localhost:8000
```

Enter a task, watch the full pipeline execute in real time — debate rounds with plan diffs, tool forge progress, streaming agent tokens — then chat with individual agents post-run.

### CLI

```bash
# Default demo task
python main.py

# Custom task
python main.py "Build a competitive analysis of three SaaS CRMs"
```

### Benchmark

```bash
# Compare single-LLM vs full pipeline
python evaluate.py

# Run full benchmark suite
python run_benchmark.py
```

---

## System Config

Defaults in [orchestrator/config.py](orchestrator/config.py):

```python
PLANNER_MODEL   = "gpt-4o"
EVALUATOR_MODEL = "gpt-4o"
COMPILER_MODEL  = "gpt-4o"
FORGE_MODEL     = "gpt-4o"

TIER_TO_MODEL = {
    "FAST":     "gpt-4o-mini",
    "BALANCED": "gpt-4o",
    "HEAVY":    "gpt-4o",
}

MAX_DEBATE_ROUNDS = 3
MAX_AGENTS        = 8
MAX_AGENT_STEPS   = 25
```

---

## Safety

The Tool Forge validates all LLM-generated code before execution:

- **Syntax check:** `ast.parse()` on every generated function
- **Forbidden imports blocked:** `subprocess`, `shutil`, `ctypes`, `importlib`, `pickle`, `shelve`, `multiprocessing`, `signal`, `socket`
- **Forbidden calls blocked:** `os.system`, `os.remove`, `__import__`, `eval`, `exec`
- **File I/O sandboxed** to the `output/` directory
- **Session TTL:** Sessions expire after 1 hour; max 20 concurrent sessions
- **Tool error wrapping:** All tool exceptions caught and stringified — agents never crash on tool failure

---

## Competitive Positioning

| System | Gap HiveMind fills |
|---|---|
| LangGraph | No native adversarial debate; new templates still require predefined patterns |
| CrewAI | Static roster; no plan validation; no cross-run memory |
| AutoGen v0.4 | Group chat is unstructured — no confidence-scored approval gate |
| Reflexion | Same agent critiques itself, sharing the proposer's biases |
| MetaGPT | Domain-specific to code generation; no general-purpose spawning |

**HiveMind is the only system combining adversarial debate + plan-driven dynamic tool forging + context-aware memory + persistent cross-run learning on top of LangGraph with MCP interoperability.**

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph 1.0+, LangChain 1.2+ |
| LLM | OpenAI GPT-4o (gpt-4o-mini for FAST tier) |
| Backend | FastAPI 0.110+, Uvicorn, Pydantic 2.0+ |
| Memory | SQLite (episodic), ChromaDB (vector search) |
| Integrations | SMTP, Slack webhooks, iCalendar, openpyxl, pdfplumber |
| MCP | `mcp` 1.0+ |
| Frontend | Vanilla HTML/CSS/JS, WebSocket, Marked.js |
| Search | DuckDuckGo (primary), Tavily (optional) |
