## ADDED Requirements

### Requirement: Sandbox directory structure exists
The system SHALL create sandbox workspace under the workspace directory.

#### Scenario: Sandbox created on startup
- **WHEN** agent starts
- **THEN** system creates `{workspace}/sandbox/scans/`
- **AND** creates `{workspace}/sandbox/downloads/`
- **AND** creates `{workspace}/sandbox/temp/`

#### Scenario: Read file within sandbox
- **WHEN** user triggers read_file with path inside sandbox
- **THEN** system reads and returns file contents

#### Scenario: Read file outside sandbox (blocked)
- **WHEN** user triggers read_file with path outside sandbox
- **THEN** system returns error "Access denied: path outside sandbox"

#### Scenario: Write scan output to sandbox
- **WHEN** tool produces output (nmap, nuclei)
- **THEN** system saves to `{sandbox}/scans/`
- **AND** includes file path in response

#### Scenario: Download saved to sandbox
- **WHEN** call_api fetches file
- **THEN** system saves to `{sandbox}/downloads/`

### Requirement: Sandbox configurable
The system SHALL allow sandbox path to be configured via config.yaml.

#### Scenario: Custom sandbox path
- **WHEN** config.yaml specifies `sandbox_path: /custom/path`
- **THEN** system uses that path for all sandbox operations

#### Scenario: Default sandbox path
- **WHEN** config.yaml does not specify sandbox_path
- **THEN** system defaults to `{workspace}/sandbox`
