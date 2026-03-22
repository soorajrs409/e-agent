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

## Prompt Assembly And Refresh

The current implementation builds the system prompt lazily on demand, then reuses it. If discovery returns no tools, the agent can force a refresh and rebuild the prompt.

```mermaid
flowchart TD
    A[agent_stream_chat] --> B[get_system_prompt()]
    B --> C{system_prompt cached?}
    C -- no --> D[discover_tools force_refresh=True]
    C -- yes --> E[discover_tools from cache]
    E --> F{tools empty?}
    F -- yes --> D
    F -- no --> G[reuse cached prompt]
    D --> H[build_tools_section()]
    H --> I[BASE_SYSTEM_PROMPT + YAML tool section]
    I --> J[cache system_prompt]
    J --> K[return prompt]
    G --> K
```

Starting the tool server before the CLI still gives the cleanest startup, but the runtime can now recover from an earlier failed discovery attempt.

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
        Core->>Core: decode JSON candidates from response text

        alt valid tool JSON found
            Core->>Guard: validate_tool_call
            alt blocked tool request
                Guard-->>Core: False + reason
                Core-->>User: guard block message
            else allowed
                Core->>MCP: POST /tools/{tool}
                MCP->>Server: HTTP request with args
                alt server returns success payload
                    Server-->>MCP: JSON output payload
                    MCP-->>Core: parsed response
                else server fails
                    Server-->>MCP: error, bad status, or invalid body
                    MCP->>Server: try next configured MCP server
                end
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
    B -- yes --> D[Get or rebuild system_prompt]
    D --> E{Ollama request succeeds?}
    E -- no --> F[Print Ollama error]
    E -- yes --> G[Buffer streamed response]
    G --> H{Valid tool JSON found?}
    H -- no --> I[Print plain response]
    H -- yes --> J{Tool call allowed?}
    J -- no --> K[Print block message]
    J -- yes --> L[call_tool via MCP client]
    L --> M{Any MCP server returns valid output?}
    M -- no --> N[Print tool error]
    M -- yes --> O[Filter output and print]
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
  - builds and refreshes the system prompt from discovered tools
  - validates user input
  - calls Ollama with request-level error handling
  - extracts and dispatches tool calls
  - filters and prints tool output
- `agent/base_prompt.py`
  - defines the base tool-usage policy and JSON output rules
- `agent/prompt_builder.py`
  - converts discovered tools into YAML for prompt injection
- `agent/mcp_client.py`
  - discovers tools from one or more MCP servers
  - caches discovered tool metadata
  - executes tool POST requests with retry/failover across configured servers
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

The active prompt is built from `BASE_SYSTEM_PROMPT` and the discovered tool YAML. `agent/prompt.py` is still present in the repo, but it is not the primary runtime prompt source.

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

The client adds a `server` field to each discovered tool entry before caching it. Discovery can also be force-refreshed when the runtime needs to rebuild the prompt.

## Security And Guardrails

- Input filtering blocks known prompt-injection strings.
- `run_nmap` targets are blocked if they include `127.0.0.1`, `localhost`, or `169.254.169.254`.
- `run_nmap` options are restricted server-side to `-sV`, `-sS`, `-Pn`, `-F`, and `-O`.
- Output filtering replaces responses containing selected sensitive phrases.

## Current Limitations

1. Tool discovery is cached for the lifetime of the process, so prompt-visible tool changes require an agent restart.
2. The Ollama response is buffered completely before any user-visible output is printed, even though streaming is enabled upstream.
3. Logging currently captures user inputs only.
4. `call_api` performs a raw GET and returns the response body as text without additional policy or shaping.
5. `agent/prompt.py` remains as an older prompt definition and may confuse future maintenance unless it is removed or clearly deprecated.
