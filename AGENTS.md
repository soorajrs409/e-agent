# Agent Context

## Startup Order

1. `ollama serve` (or already running)
2. `python main.py`

Single process only — no tool server needed.

## Architecture

- `main.py` = CLI loop (logging, input validation, event callbacks)
- `langchain_agent/agent.py` = LangGraph StateGraph with tool chaining
- `langchain_agent/tools.py` = `@tool` functions + ToolEvent class
- `langchain_agent/guardrails.py` = input/target validation
- `langchain_agent/approval_queue.py` = approval system + chain state
- `langchain_agent/rate_limiter.py` = per-tool rate limiting
- `langchain_agent/config.py` = model/host configuration

## Key Ports

| Service | Host | Port |
|---------|------|------|
| Ollama API | 127.0.0.1 | 11434 |

## Tool Chaining (LangGraph)

```
User Input → StateGraph Agent
    │
    ├─→ greeting_check() → decides: greeting or continue
    │       ├─→ greeting_response() → direct reply, then END
    │       └─→ call_llm() → ChatOllama with tools
    │
    ├─→ should_continue() → decides: continue or END
    │       ├─→ has tool_calls → continue
    │       ├─→ pending_approval → END
    │       ├─→ last_error → END
    │       └─→ max chain depth → END
    │
    ├─→ execute_tool_node() → executes tools
    │       ├─→ emits ToolEvent (started/completed/failed)
    │       └─→ stores result in state
    │
    └─→ Max chain: 5 tools enforced
```

## Tool Events

Live streaming of tool lifecycle:

```python
class ToolEvent:
    def __init__(self, tool_name: str, event_type: str, message: str = ""):
        self.tool_name = tool_name    # "run_nmap", "read_file"
        self.event_type = event_type  # "started", "completed", "failed"
        self.message = message        # error message if failed (default: "")
        self.timestamp = datetime.now().isoformat()  # set automatically
```

Usage in code:

```python
from langchain_agent.agent import stream_agent
from langchain_agent.tools import ToolEvent
events = []
for chunk in stream_agent('read sandbox/test.txt', event_callback=lambda e: events.append(e.format())):
    pass
print(events)
```

## Guardrails

- `guardrails.py` validates targets with DNS resolution + CIDR blocking:
  - Blocks `127.0.0.0/8` (all loopback), `::1`, `::ffff:127.0.0.0/104`, `0.0.0.0`, `169.254.0.0/16`
  - Resolves hostnames via `socket.getaddrinfo()` to detect alternate IP representations (hex, octal, decimal, IPv6-mapped)
  - Falls back to string-based checks on DNS timeout
  - Uses hostname-boundary matching (`(?:^|\.)blocked(?:$|\.)`) to avoid false positives (e.g. `not-localhost.com` is allowed)
- `validate_url()` blocks empty hostnames, non-HTTP schemes, and resolves hostnames to check IPs
- `validate_nmap_target()` / `validate_nuclei_target()` use same DNS+CIDR resolution + boundary matching
- `run_nmap` allows flags: `-sV`, `-sS`, `-Pn`, `-F`, `-O`
- Input max 5000 chars; prompt-injection blocked
- Max 5 tools per chain; errors terminate chain

## Dependencies

```bash
uv venv .venv && source .venv/bin/activate && uv pip install -r requirements.txt
```

Requires: `langchain`, `langchain-core`, `langchain-ollama`, `langgraph`

## Tool Usage Guidelines

The agent uses LangGraph for multi-tool chains:
- LLM decides when to call 2+ tools
- Tools execute sequentially with events
- Output from one tool feeds to next
- Errors terminate the chain (no retry)
- Approval pauses mid-chain (single tool only on resume)
- LLM receives a system prompt with tool descriptions and parameter names to reduce hallucinated tool calls

## Streaming Output

- nmap and nuclei scan output streams live to the terminal during `/approve` execution
- Scan progress (banner, templates loaded, results) prints line-by-line via `subprocess.Popen` with `stderr=subprocess.STDOUT`
- Empty scan result files are reported as "No vulnerabilities found" instead of blank output

## Testing

Verify LangGraph:
```bash
curl -s http://127.0.0.1:11434/api/tags  # Ollama health
python -c "from langchain_agent.agent import create_langgraph_agent; print('OK')"  # agent
python -c "from langchain_agent.tools import ToolEvent; print('OK')"  # events
```

## OpenSpec Workflow

Repository uses OpenSpec:
- `/openspec-propose` - create change proposal
- `/opsx-apply` - implement tasks from change
- `/opsx-archive` - archive completed changes
- `/opsx-explore` - explore ideas

Changes: `openspec/changes/`, specs: `openspec/specs/`