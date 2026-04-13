## ADDED Requirements

### Requirement: Rate limiting SHALL prevent tool abuse
Tool execution SHALL be rate-limited to prevent abuse or excessive resource usage.

#### Scenario: Rate limiting enabled
- **WHEN** guardrails.rate_limit.enabled is true in config.yaml
- **THEN** tools SHALL enforce rate limits

#### Scenario: Under limit allowed
- **WHEN** user makes tool request within rate limit
- **THEN** system SHALL execute tool normally

#### Scenario: Over limit blocked
- **WHEN** user exceeds rate limit (max_per_minute)
- **THEN** system SHALL return ToolOutput with status="blocked", output=rate limit message

#### Scenario: Per-tool rate limiting
- **WHEN** rate limiting is active
- **THEN** each tool SHALL have independent rate limit counter

#### Scenario: Rate limit reset
- **WHEN** minute window passes
- **THEN** rate limit counter SHALL reset