## Why

The current agent implementation uses hand-rolled JSON parsing, custom YAML tool schema building, and manual tool dispatch logic. As the system scales to more tools and multi-step reasoning, this becomes fragile and harder to maintain. LangChain provides battle-tested abstractions for tool calling, prompt management, and agent orchestration that eliminate this complexity.

## What Changes

- Add `langchain` and `langchain-ollama` dependencies to requirements.txt
- Create `langchain_agent/` module with `@tool` decorated functions replacing the FastAPI tool server
- Replace `create_react_agent` for tool-calling orchestration
- Port existing guardrails (input validation, nmap target blocking) as pre-tool hooks
- Delete `agent/` directory and `tool-servers/core_server/` (no longer needed)
- Simplify `main.py` to a thin CLI loop invoking the LangChain agent
- Config stays in `agent/config.py` initially, moved to env vars in future iteration

## Capabilities

### New Capabilities

- `langchain-agent`: Full agent implementation using LangChain ReAct pattern with Ollama, replacing all current agent/ and tool-servers/ code

## Impact

- **Dependencies**: Adds `langchain-core`, `langchain-ollama`, `langchain-community`, `langgraph`
- **Code removed**: `agent/` (7 files), `tool-servers/core_server/` (1 file)
- **Code added**: `langchain_agent/` (tools.py, agent.py, config.py, guardrails.py)
- **CLI changes**: `main.py` simplified to single `agent_executor.invoke()` call
- **Removed**: FastAPI tool server (uvicorn process no longer needed)
