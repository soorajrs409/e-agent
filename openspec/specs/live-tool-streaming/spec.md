## ADDED Requirements

### Requirement: Tool execution yields real-time events
Each tool SHALL emit lifecycle events that are streamed to the user as they occur.

#### Scenario: Tool starts
- **WHEN** tool begins execution
- **THEN** message "[*] Running <tool_name>..." is displayed immediately

#### Scenario: Tool produces output
- **WHEN** tool produces output (including progress indicators)
- **THEN** output is streamed to user in real-time

#### Scenario: Tool completes successfully
- **WHEN** tool completes successfully
- **THEN** message "[✓] <tool_name> completed" is displayed

#### Scenario: Tool fails
- **WHEN** tool returns error
- **THEN** message "[✗] <tool_name> failed: <error>" is displayed

### Requirement: Streaming is consistent for all tools
The streaming behavior SHALL be consistent regardless of tool type.

#### Scenario: Single tool call streams
- **WHEN** user makes single tool request
- **THEN** tool output streams live (not batched until complete)

#### Scenario: Multiple tool chain streams
- **WHEN** user requests tool chain
- **THEN** each tool's start/complete events are visible
- **AND** each tool's output is visible between start and complete events

#### Scenario: Approval requested during tool
- **WHEN** tool requests approval mid-execution
- **THEN** tool pauses
- **AND** approval request is displayed with chain progress