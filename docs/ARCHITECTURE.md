# Architecture

This document describes the current two-process architecture:

- Process 1: CLI Agent (LLM orchestration)
- Process 2: Tool Server (HTTP tool execution)

## High-Level Topology

```mermaid
flowchart LR
    U[User Terminal] --> MAIN[main.py]
    MAIN --> CORE[agent/core.py]
    CORE --> GUARD[agent/guardrails.py]
    CORE --> OLLAMA[Ollama Chat API]
    CORE --> MCPCLIENT[agent/mcp_client.py]
    MCPCLIENT --> MCPSERVER[FastAPI Tool Server]
    MCPSERVER --> TOOL1[read_file]
    MCPSERVER --> TOOL2[call_api]
    MCPSERVER --> TOOL3[run_nmap logic]
    MAIN --> LOG[(logs/agent.log)]
```

## Request Lifecycle

```mermaid
sequenceDiagram
    participant User
    participant Main as main.py
    participant Core as agent/core.py
    participant Guard as agent/guardrails.py
    participant LLM as Ollama
    participant MCP as agent/mcp_client.py
    participant Server as tool server

    User->>Main: prompt
    Main->>Main: log USER entry
    Main->>Core: agent_stream_chat(prompt)
    Core->>Guard: validate_user_input

    alt blocked
        Guard-->>Core: False + reason
        Core-->>User: guard block message
    else allowed
        Guard-->>Core: True
        Core->>LLM: chat(stream=True)
        LLM-->>Core: streamed chunks
        Core-->>User: print streamed response

        Core->>Core: parse full response as JSON
        alt tool call present
            Core->>Guard: validate_tool_call
            alt blocked tool request
                Guard-->>Core: False + reason
                Core-->>User: guard block message
            else allowed
                Core->>MCP: POST /tools/{tool}
                MCP->>Server: HTTP request with args
                Server-->>MCP: {output|error}
                MCP-->>Core: JSON response
                Core->>Guard: filter_output(output)
                Core-->>User: print tool result
            end
        else no tool JSON
            Core-->>User: done
        end
    end
```

## Agent Internal Flow

```mermaid
flowchart TD
    A[User input] --> B{Input valid?}
    B -- no --> C[Print guard message and stop]
    B -- yes --> D[Send to Ollama with system prompt]
    D --> E[Stream and accumulate full response]
    E --> F{JSON parse succeeds?}
    F -- no --> G[Return plain model answer]
    F -- yes --> H{Tool key present?}
    H -- no --> G
    H -- yes --> I{Tool call allowed?}
    I -- no --> J[Print block message]
    I -- yes --> K[call_tool via MCP client]
    K --> L{Server error?}
    L -- yes --> M[Print tool error]
    L -- no --> N[Filter output and print]
```

## Deployment Boundary

```mermaid
flowchart LR
    subgraph Agent_Runtime[Agent Runtime]
      MAIN[main.py]
      CORE[agent/core.py]
      GUARD[guardrails]
      MCPCLIENT[mcp_client]
    end

    subgraph Tool_Runtime[Tool Server Runtime]
      API[FastAPI app]
      RF[read_file endpoint]
      CA[call_api endpoint]
      NM[run_nmap function]
    end

    CORE --> MCPCLIENT
    MCPCLIENT --> API
    API --> RF
    API --> CA
    API --> NM
```

## Current Interface Contracts

### LLM to Agent

Expected tool call payload:

```json
{
  "tool": "<tool_name>",
  "args": { "key": "value" }
}
```

### Agent to Tool Server

- `POST /tools/<tool_name>`
- Body: `args` object
- Response: `{ "output": ... }` or `{ "error": ... }`

## Module Map

- `main.py`
  - input loop
  - user logging
  - calls `agent_stream_chat`
- `agent/core.py`
  - guard checks
  - LLM streaming
  - tool JSON parsing and dispatch
- `agent/mcp_client.py`
  - HTTP bridge to MCP server
- `agent/guardrails.py`
  - input policy, tool-call policy, output filtering
- `tool-servers/core_server/server.py`
  - FastAPI tool endpoints and execution logic

## Known Architectural Gaps

1. `run_nmap` route is not currently exposed as `POST /tools/run_nmap`.
2. Option validation error in `run_nmap` references undefined variable `e`.
3. JSON parse path in `agent/core.py` uses broad `except`, masking parsing failures.

