# Architecture

This document is a concise, engineering-focused reference for how the agent is structured and how requests flow through the system.

## System Components

```mermaid
flowchart LR
    U[User / Terminal] --> M[main.py\nCLI loop + logging]
    M --> C[agent/core.py\nLLM stream + tool dispatch]
    C --> O[Ollama Client\nlocal model endpoint]
    C --> G[agent/guardrails.py\ninput/tool/output checks]
    C --> T[agent/tools.py\nread_file/call_api/run_nmap]
    M --> L[(logs/agent.log)]
```

## End-to-End Request Flow

```mermaid
sequenceDiagram
    participant User
    participant Main as main.py
    participant Guard as guardrails.py
    participant Core as core.py
    participant Ollama as Ollama Model
    participant Tools as tools.py

    User->>Main: Enter prompt
    Main->>Main: log_event("USER", input)
    Main->>Core: agent_stream_chat(input)
    Core->>Guard: validate_user_input(input)

    alt Input blocked
        Guard-->>Core: (False, reason)
        Core-->>User: print guard block message
    else Input allowed
        Guard-->>Core: (True, "")
        Core->>Ollama: chat(stream=True)
        Ollama-->>Core: streamed chunks
        Core-->>User: print streamed content

        Core->>Core: json.loads(full_response)
        alt Valid tool JSON with "tool"
            Core->>Guard: validate_tool_call(tool,args)
            alt Tool blocked
                Guard-->>Core: (False, reason)
                Core-->>User: print guard block message
            else Tool allowed
                Guard-->>Core: (True, "")
                Core->>Tools: execute_tool(tool,args)
                Tools-->>Core: tool result
                Core->>Guard: filter_output(result)
                Guard-->>Core: safe result
                Core-->>User: print tool result
            end
        else Not JSON / no tool
            Core-->>User: already printed natural response
        end
    end
```

## Core Decision Logic

```mermaid
flowchart TD
    A[Start agent_stream_chat] --> B{validate_user_input}
    B -- fail --> C[Print guard reason and return]
    B -- pass --> D[Send chat request with stream=True]
    D --> E[Accumulate and print full_response]
    E --> F{JSON parse succeeds?}
    F -- no --> G[Return - response treated as normal text]
    F -- yes --> H{Tool key present?}
    H -- no --> G
    H -- yes --> I[validate_tool_call]
    I -- fail --> J[Print guard reason and return]
    I -- pass --> K[execute_tool]
    K --> L[filter_output]
    L --> M[Print safe tool result]
```

## Guardrail Pipeline

```mermaid
flowchart LR
    In[User Input] --> V1{Injection/Length checks}
    V1 -- blocked --> B1[Stop + reason]
    V1 -- pass --> LLM[Model response]
    LLM --> P{Parsed tool call?}
    P -- no --> OUT[Normal output]
    P -- yes --> V2{Tool-specific checks}
    V2 -- blocked --> B2[Stop + reason]
    V2 -- pass --> TOOL[Execute tool]
    TOOL --> V3{Sensitive output check}
    V3 -- match --> F[Filtered placeholder]
    V3 -- no match --> OUT
```

## Module Map

- `main.py`
  - CLI loop
  - user input logging
  - invokes `agent_stream_chat`
- `agent/core.py`
  - LLM request and stream handling
  - tool-call JSON parsing
  - tool dispatch and output filtering
- `agent/guardrails.py`
  - `validate_user_input`
  - `validate_tool_call`
  - `filter_output`
- `agent/tools.py`
  - `read_file`
  - `call_api`
  - `run_nmap`
- `agent/prompt.py`
  - system behavior and tool-calling instruction prompt
- `agent/config.py`
  - model/host/name/log configuration

## Known Architectural Constraints

- Tool invocation depends on full-response JSON parse success.
- No multi-turn context persistence in `messages`.
- User prompts are logged; assistant/tool metadata is not yet logged.
- Prompt and code allowed options for `run_nmap` are slightly misaligned.
