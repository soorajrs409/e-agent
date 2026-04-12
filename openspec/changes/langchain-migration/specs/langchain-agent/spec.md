## ADDED Requirements

### Requirement: LangChain Agent with Tool Calling

The agent SHALL use LangChain's `create_react_agent` with ChatOllama to handle user requests and invoke tools when appropriate.

#### Scenario: Agent responds without tools
- **WHEN** user asks an informational question (e.g., "what is DNS?")
- **THEN** agent responds with a direct text answer without calling any tool

#### Scenario: Agent calls a tool
- **WHEN** user request requires external action (file read, API call, network scan)
- **THEN** agent outputs valid JSON with `tool` and `args` keys
- **THEN** LangChain parses the structured output and executes the tool
- **THEN** tool result is displayed to user

### Requirement: Available Tools

The agent SHALL have access to three tools:

#### Scenario: read_file tool
- **WHEN** user requests file content
- **THEN** `read_file` tool is called with `file_path` argument
- **THEN** file contents are returned as output

#### Scenario: call_api tool
- **WHEN** user requests HTTP fetch
- **THEN** `call_api` tool is called with `url` argument
- **THEN** HTTP GET response body is returned as output

#### Scenario: run_nmap tool
- **WHEN** user requests network scan
- **THEN** `run_nmap` tool is called with `target` and `options` arguments
- **THEN** nmap output is returned as output

### Requirement: Guardrails for Network Scans

The agent SHALL block `run_nmap` targets that resolve to restricted addresses.

#### Scenario: Block localhost target
- **WHEN** user requests nmap scan with target containing "localhost"
- **THEN** tool execution SHALL be blocked with error message

#### Scenario: Block 127.0.0.1 target
- **WHEN** user requests nmap scan with target containing "127.0.0.1"
- **THEN** tool execution SHALL be blocked with error message

#### Scenario: Block metadata endpoint target
- **WHEN** user requests nmap scan with target containing "169.254.169.254"
- **THEN** tool execution SHALL be blocked with error message

#### Scenario: Allow valid target
- **WHEN** user requests nmap scan with target "scanme.nmap.org"
- **THEN** scan SHALL proceed and return results

### Requirement: Nmap Flag Restrictions

The agent SHALL only allow specific nmap flags.

#### Scenario: Allowed flags
- **WHEN** nmap options contain only `-sV`, `-sS`, `-Pn`, `-F`, or `-O`
- **THEN** scan SHALL execute

#### Scenario: Disallowed flag
- **WHEN** nmap options contain any flag not in allowed list
- **THEN** execution SHALL be blocked with error indicating disallowed switch

### Requirement: Input Validation

The agent SHALL validate user input before processing.

#### Scenario: Input length limit
- **WHEN** user input exceeds 5000 characters
- **THEN** agent SHALL reject with error message

#### Scenario: Prompt injection detection
- **WHEN** user input contains prompt injection phrases (e.g., "ignore previous instructions")
- **THEN** agent SHALL reject with error message

#### Scenario: Valid input
- **WHEN** user input is within length limit and contains no injection phrases
- **THEN** agent SHALL process the request normally

### Requirement: Error Handling

The agent SHALL handle errors gracefully.

#### Scenario: Tool returns error
- **WHEN** a tool returns an error payload
- **THEN** error message SHALL be displayed to user

#### Scenario: Tool not found
- **WHEN** model requests a non-existent tool
- **THEN** agent SHALL respond with error indicating unknown tool

#### Scenario: Ollama connection failure
- **WHEN** Ollama API is unreachable
- **THEN** agent SHALL display connection error message
- **THEN** agent session SHALL remain active for retry

### Requirement: Configuration

The agent SHALL read configuration from `langchain_agent/config.py`.

#### Scenario: Model configuration
- **WHEN** agent starts
- **THEN** it SHALL connect to Ollama using configured host and model name
- **THEN** default values: model="llama3", host="http://127.0.0.1:11434"

#### Scenario: Agent naming
- **WHEN** CLI starts
- **THEN** it SHALL display configured agent name
- **THEN** default value: agent_name="electron-agent"

### Requirement: Logging

The agent SHALL log user input to file.

#### Scenario: User input logged
- **WHEN** user submits a prompt
- **THEN** prompt SHALL be appended to logs/agent.log with timestamp
- **THEN** format: `[timestamp][USER] [prompt]`
