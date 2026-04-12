## 1. Config Expansion

- [x] 1.1 Expand config.yaml with sandbox path, tool categories, approval settings
- [x] 1.2 Create config.yaml.example with all new options documented

## 2. Sandbox Setup

- [x] 2.1 Add sandbox directory creation on startup in main.py
- [x] 2.2 Create sandbox/scans/, sandbox/downloads/, sandbox/temp/ directories
- [x] 2.3 Implement sandbox path getter function in config module

## 3. Approval System Core

- [x] 3.1 Create approval_queue module (langchain_agent/approval_queue.py)
- [x] 3.2 Implement in-memory queue with UUID generation
- [x] 3.3 Add approval expiry check (5 minute timeout)
- [x] 3.4 Implement /approve command handler
- [x] 3.5 Implement /deny command handler
- [x] 3.6 Implement /approve-all command handler

## 4. Tool: Nuclei

- [x] 4.1 Add run_nuclei tool to tools.py
- [x] 4.2 Implement option parsing for severity, templates, tags
- [x] 4.3 Add guardrails for target validation
- [x] 4.4 Implement sandbox output writing
- [x] 4.5 Integrate with approval system (returns "[APPROVAL REQUIRED] ID: xxx" if approval needed)

## 5. Guardrails Update

- [x] 5.1 Add validate_nuclei_target to guardrails.py
- [x] 5.2 Update tool category checking logic
- [x] 5.3 Add sandbox path enforcement to read_file

## 6. Main CLI Integration

- [x] 6.1 Update main.py to parse approval commands before agent
- [x] 6.2 Wire up approval queue to CLI loop
- [x] 6.3 Add approval queue check before each agent call

## 7. Logging Enhancement

- [x] 7.1 Update logging to use TimedRotatingFileHandler (7-day rotation)
- [x] 7.2 Add structured log format with timestamps
- [x] 7.3 Log approvals and denials with UUID
- [x] 7.4 Log tool executions with output size

## 8. Testing

- [x] 8.1 Test auto tools (read_file, call_api, run_nmap) still work
- [x] 8.2 Test nuclei requires approval
- [x] 8.3 Test /approve executes command
- [x] 8.4 Test /deny blocks command
- [x] 8.5 Test /approve-all enables auto-run
- [x] 8.6 Test approval timeout after 5 minutes
- [x] 8.7 Test sandbox file writes
- [x] 8.8 Test log rotation

## 9. Documentation

- [x] 9.1 Update README with new commands (/approve, /deny, /approve-all)
- [x] 9.2 Document config.yaml changes
- [x] 9.3 Add nuclei prerequisites to README
- [x] 9.4 Updated config.yaml.example with run_nmap as approval_required
