# Architecture

This project runs as a two-process local system:

- Process 1: CLI agent for prompt orchestration and policy checks
- Process 2: FastAPI tool server for external actions

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
    MCPSERVER --> TOOL3[run_nmap]
    MAIN --> LOG[(logs/agent.log)]
```

## Startup-Time Prompt Assembly

One important detail in the current implementation is that the system prompt is assembled when `agent/core.py` is imported.

```mermaid
flowchart TD
    A[Import agent/core.py] --> B[discover_tools()]
    B --> C[GET /tools from MCP server]
    C --> D[build_tools_section()]
    D --> E[BASE_SYSTEM_PROMPT + YAML tool section]
    E --> F[system_prompt cached in module]
```

This means the tool server should already be running before `main.py` imports `agent.core`, or the prompt may be built without tool metadata for that process.

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
        Core->>Core: buffer full response
        Core->>Core: extract JSON-shaped block with regex

        alt valid tool JSON found
            Core->>Guard: validate_tool_call
            alt blocked tool request
                Guard-->>Core: False + reason
                Core-->>User: guard block message
            else allowed
                Core->>MCP: POST /tools/{tool}
                MCP->>Server: HTTP request with args
                Server-->>MCP: JSON {output|error}
                MCP-->>Core: parsed response
                Core->>Guard: filter_output(output)
                Core-->>User: print tool result
            end
        else no valid tool JSON
            Core-->>User: print normal model response
        end
    end
```

## Agent Internal Flow

```mermaid
flowchart TD
    A[User input] --> B{Input valid?}
    B -- no --> C[Print guard message and stop]
    B -- yes --> D[Use cached system_prompt]
    D --> E[Send messages to Ollama]
    E --> F[Buffer streamed response]
    F --> G{Regex finds JSON block?}
    G -- no --> H[Print plain response]
    G -- yes --> I{JSON parses and has tool key?}
    I -- no --> H
    I -- yes --> J{Tool call allowed?}
    J -- no --> K[Print block message]
    J -- yes --> L[call_tool via MCP client]
    L --> M{Tool returned error?}
    M -- yes --> N[Print tool error]
    M -- no --> O[Filter output and print]
```

## Deployment Boundary

```mermaid
flowchart LR
    subgraph Agent_Runtime[Agent Runtime]
      MAIN[main.py]
      CORE[agent/core.py]
      BASE[base_prompt.py]
      PB[prompt_builder.py]
      GUARD[guardrails.py]
      MCPCLIENT[mcp_client.py]
    end

    subgraph Tool_Runtime[Tool Server Runtime]
      API[FastAPI app]
      LIST[GET /tools]
      RF[POST /tools/read_file]
      CA[POST /tools/call_api]
      NM[POST /tools/run_nmap]
    end

    CORE --> BASE
    CORE --> PB
    CORE --> GUARD
    CORE --> MCPCLIENT
    MCPCLIENT --> API
    API --> LIST
    API --> RF
    API --> CA
    API --> NM
```

## Module Responsibilities

- `main.py`
  - starts the CLI loop
  - logs user inputs
  - delegates each prompt to `agent_stream_chat`
- `agent/core.py`
  - builds the system prompt from discovered tools
  - validates user input
  - calls Ollama
  - extracts and dispatches tool calls
  - filters and prints tool output
- `agent/base_prompt.py`
  - defines the base tool-usage policy and JSON output rules
- `agent/prompt_builder.py`
  - converts discovered tools into YAML for prompt injection
- `agent/mcp_client.py`
  - discovers tools from one or more MCP servers
  - caches discovered tool metadata
  - executes tool POST requests
- `agent/guardrails.py`
  - blocks common prompt-injection phrases
  - blocks selected scan targets
  - filters sensitive phrases from output
- `tool-servers/core_server/server.py`
  - publishes tool metadata
  - implements `read_file`, `call_api`, and `run_nmap`

## Interface Contracts

### Model To Agent

Expected tool payload:

```json
{
  "tool": "<tool_name>",
  "args": {
    "key": "value"
  }
}
```

The active prompt is built from `BASE_SYSTEM_PROMPT` and the discovered tool YAML. `agent/prompt.py` is present in the repo, but it is not the primary runtime prompt source.

### Agent To Tool Server

- request path: `POST /tools/<tool_name>`
- request body: tool args as JSON
- success response: `{ "output": ... }`
- error response: `{ "error": ... }`

### Tool Discovery Format

`GET /tools` returns:

```json
{
  "tools": [
    {
      "name": "read_file",
      "description": "Read file contents from disk",
      "args": ["file_path"]
    }
  ]
}
```

The client adds a `server` field to each discovered tool entry before caching it.

## Security And Guardrails

- Input filtering blocks known prompt-injection strings.
- `run_nmap` targets are blocked if they include `127.0.0.1`, `localhost`, or `169.254.169.254`.
- `run_nmap` options are restricted server-side to `-sV`, `-sS`, `-Pn`, `-F`, and `-O`.
- Output filtering replaces responses containing selected sensitive phrases.

## Current Limitations

1. Tool discovery is cached for the lifetime of the process, so prompt-visible tool changes require an agent restart.
2. The Ollama response is buffered completely before any user-visible output is printed, even though streaming is enabled upstream.
3. Tool-call extraction uses a greedy regex and broad exception handling, so mixed prose plus JSON can degrade into silent non-tool behavior.
4. Logging currently captures user inputs only.
5. `call_api` performs a raw GET and returns the response body as text without additional policy or shaping.
