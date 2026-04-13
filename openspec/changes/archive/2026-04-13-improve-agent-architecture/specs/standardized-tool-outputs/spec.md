## ADDED Requirements

### Requirement: All tools SHALL return standardized ToolOutput format
All agent tools SHALL return a consistent response format using the ToolOutput pydantic model with fields: status (str), tool (str), output (str), saved_to (Optional[str]).

#### Scenario: read_file returns ToolOutput
- **WHEN** user requests file read of existing file within sandbox
- **THEN** system returns ToolOutput with status="success", tool="read_file", output=file contents, saved_to=None

#### Scenario: read_file returns error ToolOutput
- **WHEN** user requests file read of non-existent file
- **THEN** system returns ToolOutput with status="error", tool="read_file", output=error message, saved_to=None

#### Scenario: call_api returns ToolOutput
- **WHEN** user makes HTTP request via call_api
- **THEN** system returns ToolOutput with status="success", tool="call_api", output=response body, saved_to=file path if saved

#### Scenario: run_nmap returns ToolOutput
- **WHEN** user runs nmap scan
- **THEN** system returns ToolOutput with status="success" or "error", tool="run_nmap", output=scan results, saved_to=save file path

#### Scenario: run_nuclei returns ToolOutput
- **WHEN** user runs nuclei scan
- **THEN** system returns ToolOutput with status="success" or "error", tool="run_nuclei", output=status message, saved_to=output file path