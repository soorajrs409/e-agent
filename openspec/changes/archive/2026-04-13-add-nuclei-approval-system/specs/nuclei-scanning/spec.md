## ADDED Requirements

### Requirement: Nuclei tool exists
The system SHALL provide a `run_nuclei` tool that executes nuclei vulnerability scanner against a target URL or host.

#### Scenario: Run nuclei with default severity
- **WHEN** user requests vulnerability scan on "https://example.com"
- **THEN** system runs `nuclei -severity critical,high,medium,low` against target and returns output

#### Scenario: Run nuclei with custom severity
- **WHEN** user specifies severity filter "critical,high" in options
- **THEN** system runs nuclei with only those severity levels

#### Scenario: Run nuclei with specific templates
- **WHEN** user specifies template IDs like "CVE-2021-44228"
- **THEN** system runs nuclei with `-templates` flag using those IDs

#### Scenario: Nuclei tool requires approval
- **WHEN** user triggers `run_nuclei` tool
- **THEN** system returns "[APPROVAL REQUIRED] ID: {uuid}" instead of executing
- **AND** places the execution request in approval queue

#### Scenario: Nuclei execution after approval
- **WHEN** user approves with `/approve {id}`
- **THEN** system executes nuclei command and returns output
- **AND** logs the approval and execution

#### Scenario: Nuclei denied
- **WHEN** user denies with `/deny {id}`
- **THEN** system does not execute the command
- **AND** logs the denial

#### Scenario: Approval timeout
- **WHEN** approval is not given within 5 minutes
- **THEN** the queued request expires
- **AND** user must re-issue the command

### Requirement: Full template selection
The system SHALL allow users to specify which nuclei templates to run via options string.

#### Scenario: Template by category
- **WHEN** user specifies category like "cves,exposed-panels"
- **THEN** system passes `-templates` with category path

#### Scenario: Template by tags
- **WHEN** user specifies tags like "cve,jwt"
- **THEN** system uses `-template-tags` flag

#### Scenario: Custom template path
- **WHEN** user provides path to custom template file
- **THEN** system runs nuclei with that template path

### Requirement: Output to sandbox
The system SHALL write nuclei scan results to the sandbox directory.

#### Scenario: Scan output saved
- **WHEN** nuclei scan completes
- **THEN** output is saved to `{sandbox}/scans/nuclei-{timestamp}.txt`
- **AND** file path is included in tool response
