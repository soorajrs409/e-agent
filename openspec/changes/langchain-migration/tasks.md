## 1. Setup

- [x] 1.1 Create `langchain_agent/` directory structure
- [x] 1.2 Add LangChain dependencies to requirements.txt (`langchain-core`, `langchain-ollama`, `langchain-community`)
- [x] 1.3 Verify pip install works in .venv

## 2. Config Module

- [x] 2.1 Create `langchain_agent/__init__.py`
- [x] 2.2 Create `langchain_agent/config.py` (port from `agent/config.py`)
  - MODEL_NAME, OLLAMA_HOST, AGENT_NAME, LOG_FILE

## 3. Tools Module

- [x] 3.1 Create `langchain_agent/tools.py`
- [x] 3.2 Implement `read_file` tool with `@tool` decorator
- [x] 3.3 Implement `call_api` tool with `@tool` decorator
- [x] 3.4 Implement `run_nmap` tool with `@tool` decorator
- [x] 3.5 Export tools list for agent binding

## 4. Guardrails Module

- [x] 4.1 Create `langchain_agent/guardrails.py`
- [x] 4.2 Port input validation (5000 char limit, prompt injection detection)
- [x] 4.3 Port nmap target blocking (localhost, 127.0.0.1, 169.254.169.254)
- [x] 4.4 Wrap tools with guard checks

## 5. Agent Module

- [x] 5.1 Create `langchain_agent/agent.py`
- [x] 5.2 Initialize ChatOllama with config
- [x] 5.3 Create `create_react_agent` with tools
- [x] 5.4 Implement streaming wrapper (buffer or stream to terminal)
- [x] 5.5 Add Ollama connection error handling

## 6. Main.py Updates

- [x] 6.1 Simplify `main.py` to import from `langchain_agent/agent.py`
- [x] 6.2 Keep logging functionality (user input → logs/agent.log)
- [x] 6.3 Keep input validation call before agent invoke
- [x] 6.4 Keep graceful exception handling
- [x] 6.5 Test CLI loop works end-to-end

## 7. Verification

- [x] 7.1 Test `read_file` tool (read README.md)
- [x] 7.2 Test `call_api` tool (fetch example.com)
- [x] 7.3 Test `run_nmap` tool with valid target (scanme.nmap.org -F)
- [x] 7.4 Test guardrail blocking (nmap localhost)
- [x] 7.5 Test input validation (long input, injection phrase)
- [x] 7.6 Verify Ollama connection errors handled gracefully

## 8. Cleanup

- [x] 8.1 Delete `agent/` directory (7 files)
- [x] 8.2 Delete `tool-servers/core_server/` directory
- [x] 8.3 Delete `agent/prompt.py` (legacy, not needed)
- [x] 8.4 Update README.md with new architecture diagram
- [x] 8.5 Update docs/ARCHITECTURE.md
- [x] 8.6 Update docs/RUNBOOK.md (remove FastAPI server startup instructions)

## 9. Archive

- [x] 9.1 Run `/openspec-archive-change` to finalize
