## Context

The current system is a two-process architecture:
- **CLI agent** (`agent/`) — handles prompting, JSON parsing, tool dispatch via HTTP
- **Tool server** (`tool-servers/core_server/`) — FastAPI exposing `read_file`, `call_api`, `run_nmap`

The agent relies on custom code to:
- Extract JSON tool calls from model output
- Build YAML tool schemas for the prompt
- Retry tool calls across multiple MCP servers

LangChain provides standardized abstractions for all of this.

## Goals / Non-Goals

**Goals:**
- Replace custom JSON parsing with LangChain's structured tool calling
- Replace hand-rolled YAML tool schemas with `@tool` decorators
- Eliminate the FastAPI tool server (single-process agent)
- Port existing guardrails (input validation, nmap target blocking)
- Achieve feature parity with current system

**Non-Goals:**
- Add conversation memory / history (future iteration)
- Add RAG / document retrieval (future iteration)
- Support multiple MCP servers (current code doesn't either)
- Streaming output to terminal (buffered output is fine)
- Full LangChain kitchen sink — lean dependencies only

## Decisions

### 1. Dependencies: LangChain Core + Ollama only

**Decision:** Use minimal packages:
```
langchain-core
langchain-ollama
langchain-community
langgraph
```

**Rationale:** This system has 3 tools and one model. Full LangChain adds 20+ packages for features we won't use. Community package is included for any utility functions.

**Alternatives:**
- Full `langchain` metapackage — overkill, more dependencies, harder to debug
- `langchain-experimental` — not production-ready

---

### 2. Kill the FastAPI Tool Server

**Decision:** Move tools from HTTP endpoints to Python `@tool` decorated functions in `langchain_agent/tools.py`.

**Rationale:**
- FastAPI was useful for MCP-style extensibility but adds HTTP overhead
- LangChain `@tool` decorators are cleaner and equally maintainable
- Single-process architecture is simpler to run and debug
- Current tools (file read, HTTP GET, nmap) are simple enough to be direct Python calls

**Alternatives:**
- Keep FastAPI server, call it from LangChain as HTTP tool — keeps HTTP overhead, two processes
- LangChain MCP server integration — over-engineered for this use case

---

### 3. Use `create_react_agent` (ReAct Pattern)

**Decision:** Use LangChain's `create_react_agent` factory with the Ollama chat model.

**Rationale:**
- ReAct (Reason + Act) is proven for tool-calling agents
- `create_react_agent` handles the full agent loop: think → act → observe → repeat
- Built-in tool calling support with structured output parsing
- No need to write custom agent executor logic

**Alternatives:**
- `create_tool_calling_agent` — more explicit but requires more setup
- Custom agent with `AgentExecutor` — reinvents the wheel
- LangGraph for complex workflows — overkill for linear tool calling

---

### 4. Port Guardrails as Tool Hooks

**Decision:** Wrap LangChain tools with pre-execution checks.

```python
def guarded_tool(tool_func, guard_check):
    def wrapper(*args, **kwargs):
        if not guard_check(*args, **kwargs):
            return {"error": "Guard blocked"}
        return tool_func(*args, **kwargs)
    return wrapper
```

**Rationale:**
- Current `guardrails.py` blocks `run_nmap` targets (localhost, 127.0.0.1, 169.254.169.254)
- Input validation (max 5000 chars, prompt injection phrases) stays in main.py before agent call
- LangChain doesn't have built-in concept of tool-level guards — wrapping is idiomatic

**Alternatives:**
- Modify `@tool` functions directly — pollutes tool logic with guard concerns
- Custom Pydantic schemas with validators — more complex than needed

---

### 5. Config: Port from `agent/config.py` to `langchain_agent/config.py`

**Decision:** Copy current config (MODEL_NAME, OLLAMA_HOST, AGENT_NAME, LOG_FILE) to new module.

**Rationale:** Keep it simple. Env vars can come later.

**Alternatives:**
- Pydantic settings with env var support — adds dependency, not needed yet
- Keep in `agent/config.py` and import — keeps dead code around

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| LangChain version churn / breaking changes | Pin versions in requirements.txt |
| Ollama tool calling support varies by model | Test with llama3; fallback to text prompts if needed |
| Debugging LangChain internals is harder than custom code | Add logging; keep agent simple |
| Removing HTTP tool server loses some isolation | Acceptable — local dev tool, not production |
| Learning curve for LangChain abstractions | Good docs; lean use of features |

## Open Questions

1. **Ollama model capability:** Does the installed llama3 model handle tool calling well? May need to test or try `llama3.1` / `llama3.2` which have better function calling support.

2. **Streaming:** Current code buffers output. LangChain streams by default. Should we disable streaming for cleaner terminal output, or embrace it?

3. **Error handling:** How granular should errors be? LangChain throws exceptions for various failures. Need to decide on error response format.

4. **Future memory:** The architecture should not preclude adding `ChatMessageHistory` later. Keep the agent invocation stateless for now.
