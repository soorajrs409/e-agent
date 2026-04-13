## MODIFIED Requirements

### Requirement: Approval pauses chain mid-execution
The agent SHALL pause chain execution when a tool requires approval and resume when approved, without crashing.

#### Scenario: Approval required mid-chain
- **WHEN** tool 2 of 3 requires approval
- **THEN** execution pauses after tool 1 completes
- **AND** approval message is displayed to user
- **AND** chain state is preserved

#### Scenario: Approval granted for nmap
- **WHEN** user runs `/approve <request_id>` for a pending nmap scan
- **THEN** the scan executes
- **AND** the output text is returned to the user (not the ToolOutput object repr)
- **AND** the log records the output character length correctly
- **AND** the saved-to path is displayed if present

#### Scenario: Approval denied
- **WHEN** user runs `/deny <request_id>`
- **THEN** chain terminates
- **AND** error message reports denial