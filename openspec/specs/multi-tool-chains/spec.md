## ADDED Requirements

### Requirement: Agent executes tool chains sequentially
The agent SHALL execute multiple tools in sequence when user intent requires sequential operations.

#### Scenario: User requests two-tool chain
- **WHEN** user says "scan 192.168.1.1 and check for vulnerabilities"
- **THEN** agent executes run_nmap first, then run_nuclei on the nmap results
- **AND** each tool's output is available to the next tool

#### Scenario: User requests three-tool chain
- **WHEN** user says "read config.txt, extract the server IP, then scan it"
- **AND** config.txt contains an IP address
- **THEN** agent executes read_file, extracts IP, executes run_nmap, executes run_nuclei

### Requirement: Chain terminates on error
The agent SHALL terminate chain execution when a tool fails and no alternate tool is available.

#### Scenario: First tool fails no alternate
- **WHEN** tool 1 in chain returns error
- **AND** LLM determines no alternate tool
- **THEN** chain terminates immediately
- **AND** error message is returned to user with partial results

#### Scenario: Alternate tool exists
- **WHEN** tool 1 returns error
- **AND** LLM suggests alternate tool (e.g., different nmap flags)
- **THEN** alternate tool is attempted
- **AND** if alternate succeeds, chain continues
- **AND** if alternate fails, chain terminates

### Requirement: Approval pauses chain mid-execution
The agent SHALL pause chain execution when a tool requires approval and resume when approved.

#### Scenario: Approval required mid-chain
- **WHEN** tool 2 of 3 requires approval
- **THEN** execution pauses after tool 1 completes
- **AND** approval message is displayed to user
- **AND** chain state is preserved

#### Scenario: Approval granted
- **WHEN** user runs /approve <request_id>
- **THEN** chain resumes from tool 2
- **AND** execution continues to tool 3

#### Scenario: Approval denied
- **WHEN** user runs /deny <request_id>
- **THEN** chain terminates
- **AND** error message reports denial

### Requirement: Maximum chain length enforced
The agent SHALL limit chain execution to prevent runaway scenarios.

#### Scenario: Chain exceeds limit
- **WHEN** LLM determines more than 5 tools needed
- **THEN** agent executes first 5 tools
- **AND** reports "chain truncated, re-run for remaining steps"