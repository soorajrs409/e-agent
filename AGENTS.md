# Agent Context

## Startup Order

1. `ollama serve` (or already running)
2. `python main.py`

Single process only — no tool server needed.

## Architecture

- `main.py` = CLI loop (logging, input validation)
- `langchain_agent/agent.py` = LangChain agent with `create_agent` + system prompt
- `langchain_agent/tools.py` = `@tool` decorated functions
- `langchain_agent/guardrails.py` = input/target validation
- `langchain_agent/config.py` = model/host configuration

## Key Ports

| Service | Host | Port |
|---------|------|------|
| Ollama API | 127.0.0.1 | 11434 |

## Guardrails

- `langchain_agent/guardrails.py` blocks `run_nmap` targets: `127.0.0.1`, `localhost`, `169.254.169.254`
- `run_nmap` only allows flags: `-sV`, `-sS`, `-Pn`, `-F`, `-O`
- Input max 5000 chars; prompt-injection phrases blocked

## Tool Usage Guidelines

The agent has a system prompt that guides when to use tools:
- Use tools for: file reads, URL fetching, network scans
- Don't use tools for: greetings, casual conversation, general knowledge

## Dependencies

Install with:
```bash
uv venv .venv && source .venv/bin/activate && uv pip install -r requirements.txt
```

Requires: `langchain`, `langchain-core`, `langchain-ollama`, `langgraph`

## Testing

No test framework configured. Verify manually:
- `curl -s http://127.0.0.1:11434/api/tags` - Ollama health
- `source .venv/bin/activate && python -c "from langchain_agent import agent_executor; print('OK')"` - imports

## OpenSpec Workflow

This repo uses OpenSpec for change management. Skills:
- `/openspec-propose` - create a new change proposal
- `/opsx-apply-change` - implement tasks from a change
- `/opsx-archive-change` - archive completed changes
- `/opsx-explore` - explore ideas before proposing

Changes live in `openspec/changes/`, specs in `openspec/specs/`.
