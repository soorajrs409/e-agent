# AI Agent Dev

Local CLI AI agent powered by Ollama with LangChain for tool-calling orchestration.

## Overview

This project uses LangChain's ReAct agent pattern with Ollama for natural language understanding and tool execution. Tools are defined as Python functions with `@tool` decorators.

## Architecture At A Glance

```mermaid
flowchart LR
    U[User] --> CLI[main.py]
    CLI --> GUARD[langchain_agent/<br/>guardrails.py]
    CLI --> AGENT[langchain_agent/<br/>agent.py<br/>LangChain]
    AGENT --> LLM[ChatOllama]
    AGENT --> TOOLS[langchain_agent/<br/>tools.py<br/>@tool decorators]
    TOOLS --> TF[read_file]
    TOOLS --> TA[call_api]
    TOOLS --> TN[run_nmap]
    CLI --> LOG[(logs/agent.log)]
```

## Repository Layout

```text
.
├── main.py
├── requirements.txt
├── README.md
├── AGENTS.md
├── langchain_agent/
│   ├── __init__.py
│   ├── agent.py        # LangChain ReAct agent setup
│   ├── config.py       # Configuration (model, host)
│   ├── tools.py        # @tool decorated functions
│   └── guardrails.py   # Input/target validation
└── docs/
    ├── ARCHITECTURE.md
    └── RUNBOOK.md
```

## Runtime Flow

1. `main.py` starts CLI loop, logs user input to `logs/agent.log`
2. Input validated by `guardrails.validate_input()`
3. User message sent to LangChain `AgentExecutor`
4. Model decides: respond directly or call tool
5. If tool call: LangChain executes `@tool` function
6. Tool result returned to model for final response
7. Response displayed to user

## Setup

### 1. Create and activate virtual environment

```bash
uv venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
uv pip install -r requirements.txt
```

### 3. Start Ollama

```bash
ollama serve
ollama pull llama3.1
```

### 4. Start the agent CLI

```bash
python main.py
```

Type `exit` to quit.

## Configuration

From `langchain_agent/config.py`:

- `MODEL_NAME = "llama3.1"`
- `OLLAMA_HOST = "http://127.0.0.1:11434"`
- `AGENT_NAME = "electron-agent"`
- `LOG_FILE = "logs/agent.log"`

## Available Tools

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents from disk |
| `call_api` | Make HTTP GET request to a URL |
| `run_nmap` | Run network scan (ports/services) |

## Guardrails

### Input validation
- Rejects input > 5000 characters
- Blocks prompt injection phrases

### Tool restrictions
- `run_nmap` blocks targets: `localhost`, `127.0.0.1`, `169.254.169.254`
- `run_nmap` only allows flags: `-sV`, `-sS`, `-Pn`, `-F`, `-O`

## Additional Docs

- Architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Operations: [`docs/RUNBOOK.md`](docs/RUNBOOK.md)
