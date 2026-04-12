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
- `langchain_agent/config.py` = model/host configuration

## Key Ports

| Service | Host | Port |
|---------|------|------|
| Ollama API | 127.0.0.1 | 11434 |

## Tool Chaining (LangGraph)

```
User Input → StateGraph Agent
    │
    ├─→ should_continue() → decides: continue/end
    ├─→ call_llm() → ChatOllama with tools
    ├─→ execute_tool_node() → executes tools
    │       ├─→ emits ToolEvent (started/completed/failed)
    │       └─→ stores result in state
    └─→ Max chain: 5 tools enforced
```

## Tool Events

Live streaming of tool lifecycle:

```python
class ToolEvent:
    tool_name: str      # "run_nmap", "read_file"
    event_type: str   # "started", "completed", "failed"
    message: str      # error message if failed
    timestamp: str    # ISO timestamp
```

Usage in code:

```python
from langchain_agent.agent import stream_agent, ToolEvent

def cb(event: ToolEvent):
    print(event.format())  # [*] Running tool...

for chunk in stream_agent("prompt", event_callback=cb):
    print(chunk)
```

## Guardrails

- `guardrails.py` blocks targets: `127.0.0.1`, `localhost`, `169.254.169.254`
- `run_nmap` allows flags: `-sV`, `-sS`, `-Pn`, `-F`, `-O`
- Input max 5000 chars; prompt-injection blocked
- Max 5 tools per chain

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
- Error triggers fallback attempt
- Approval pauses mid-chain

## Testing

Verify LangGraph:
```bash
curl -s http://127.0.0.1:11434/api/tags  # Ollama health
python -c "from langchain_agent.agent import create_langgraph_agent; print('OK')"  # agent
python -c "from langchain_agent.tools import ToolEvent; print('OK')"  # events
```

Test chain:
```bash
python -c "
from langchain_agent.agent import stream_agent, ToolEvent
events = []
for chunk in stream_agent('read sandbox/test.txt', event_callback=lambda e: events.append(e.format())):
    pass
print(events)
"
```

## OpenSpec Workflow

Repository uses OpenSpec:
- `/openspec-propose` - create change proposal
- `/opsx-apply` - implement tasks from change
- `/opsx-archive` - archive completed changes
- `/opsx-explore` - explore ideas

Changes: `openspec/changes/`, specs: `openspec/specs/`