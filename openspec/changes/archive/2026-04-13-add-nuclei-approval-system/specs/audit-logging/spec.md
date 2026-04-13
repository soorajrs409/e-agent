## ADDED Requirements

### Requirement: All actions logged
The system SHALL log every user action, tool execution, and approval decision.

#### Scenario: User input logged
- **WHEN** user enters any input
- **THEN** system logs timestamp, session ID, and input text

#### Scenario: Approval logged
- **WHEN** user approves a request with `/approve {id}`
- **THEN** system logs "APPROVED: {id}" with timestamp

#### Scenario: Denial logged
- **WHEN** user denies a request with `/deny {id}`
- **THEN** system logs "DENIED: {id}" with timestamp

#### Scenario: Tool execution logged
- **WHEN** tool executes (auto or approved)
- **THEN** system logs tool name, target, and output size

#### Scenario: Tool output logged
- **WHEN** tool produces output
- **THEN** system logs full output or truncated for large outputs

### Requirement: Logs rotate every 7 days
The system SHALL automatically rotate log files to keep only 7 days of history.

#### Scenario: Log rotation
- **WHEN** new day begins and log file exists
- **THEN** system creates new log file with date suffix
- **AND** deletes logs older than 7 days

#### Scenario: Log file naming
- **WHEN** system creates log file
- **THEN** filename includes date: `agent-{YYYY-MM-DD}.log`

### Requirement: Log format structured
The system SHALL use structured log format for parsing.

#### Scenario: Log entry format
- **WHEN** logging any event
- **THEN** entry format is: `[TIMESTAMP] [SESSION] [TYPE] message`

### Requirement: Approval queue persisted
The system SHALL optionally persist approval queue across restarts.

#### Scenario: Queue not persisted (default)
- **WHEN** agent restarts
- **THEN** pending approval requests are lost
- **AND** user must re-issue commands

#### Scenario: Queue persisted
- **WHEN** config enables queue persistence
- **AND** agent restarts
- **THEN** pending requests remain in queue with original timestamps
