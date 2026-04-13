## ADDED Requirements

### Requirement: URL validation SHALL prevent unsafe HTTP requests
The call_api tool SHALL validate URLs before making HTTP requests, blocking dangerous schemes and internal targets.

#### Scenario: Only http and https allowed
- **WHEN** user provides URL with scheme other than http:// or https://
- **THEN** system SHALL return ToolOutput with status="blocked", output=validation error

#### Scenario: Block internal URLs
- **WHEN** user provides URL targeting internal/network addresses
- **THEN** system SHALL return ToolOutput with status="blocked", output=validation error

#### Scenario: Valid external URL allowed
- **WHEN** user provides valid external https:// URL
- **THEN** system SHALL make the HTTP request and return results

#### Scenario: Invalid URL format rejected
- **WHEN** user provides malformed URL
- **THEN** system SHALL return ToolOutput with status="blocked", output=validation error