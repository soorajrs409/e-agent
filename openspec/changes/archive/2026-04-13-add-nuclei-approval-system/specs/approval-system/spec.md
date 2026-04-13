## ADDED Requirements

### Requirement: Approval queue exists
The system SHALL maintain an approval queue for privileged tool executions.

#### Scenario: Approval queue empty at start
- **WHEN** agent starts with no pending requests
- **THEN** queue is empty

#### Scenario: Request queued for approval
- **WHEN** user triggers privileged tool (nuclei)
- **THEN** system generates unique request ID (UUID)
- **AND** returns "[APPROVAL REQUIRED] ID: {uuid}" to user
- **AND** stores request in queue with timestamp

#### Scenario: User approves request
- **WHEN** user enters `/approve {uuid}`
- **THEN** system finds matching request in queue
- **AND** executes the tool command
- **AND** removes request from queue

#### Scenario: User denies request
- **WHEN** user enters `/deny {uuid}`
- **THEN** system finds matching request in queue
- **AND** does NOT execute the tool
- **AND** removes request from queue

#### Scenario: Approve-all for tool type
- **WHEN** user enters `/approve-all nuclei`
- **THEN** system marks nuclei as auto-approved for this session
- **AND** subsequent nuclei commands execute without approval

#### Scenario: Deny non-existent request
- **WHEN** user tries to approve/deny unknown UUID
- **THEN** system returns "Request not found"

#### Scenario: Approval timeout
- **WHEN** request sits in queue > 5 minutes
- **THEN** request expires and is removed from queue
- **AND** user must re-issue command

### Requirement: Approval applies to specific tools only
The system SHALL categorize tools into auto-run and approval-required.

#### Scenario: Auto-run tools execute immediately
- **WHEN** user triggers read_file, call_api, or run_nmap
- **THEN** system executes immediately without approval

#### Scenario: Approval-required tools wait
- **WHEN** user triggers run_nuclei
- **THEN** system queues for approval

#### Scenario: Tool category configurable
- **WHEN** config specifies tool category
- **THEN** system applies that category at runtime

### Requirement: Approval commands work in CLI
The system SHALL accept approval commands in the same CLI interface.

#### Scenario: Approve command accepted
- **WHEN** user inputs "/approve abc-123"
- **THEN** system parses command and handles approval

#### Scenario: Deny command accepted
- **WHEN** user inputs "/deny abc-123"
- **THEN** system parses command and handles denial

#### Scenario: Approve-all command accepted
- **WHEN** user inputs "/approve-all nuclei"
- **THEN** system enables auto-approval for that tool
