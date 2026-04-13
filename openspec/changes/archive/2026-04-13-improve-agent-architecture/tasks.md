## 1. Config Updates

- [x] 1.1 Add guardrails section to config.yaml with max_input_length, blocked_targets, nmap.allowed_flags, rate_limit settings
- [x] 1.2 Update config.py to load guardrails settings with defaults fallback
- [x] 1.3 Add get_guardrails_config() function to config.py

## 2. Tool Output Standardization

- [x] 2.1 Update read_file to always return ToolOutput
- [x] 2.2 Update call_api to always return ToolOutput
- [x] 2.3 Update run_nmap to always return ToolOutput
- [x] 2.4 Update run_nuclei to always return ToolOutput (already returning ToolOutput, verify)
- [x] 2.5 Update handle_approve in main.py to use ToolOutput from approval result

## 3. Guardrails Improvements

- [x] 3.1 Update guardrails.py to read from config instead of hardcoded values
- [x] 3.2 Add validate_url() function for URL validation
- [x] 3.3 Integrate URL validation into call_api tool
- [x] 3.4 Add rate limiting implementation in tools.py

## 4. Approval Queue Cleanup

- [x] 4.1 Remove unused callback parameter from add_request method
- [x] 4.2 Remove callback storage from ApprovalRequest class
- [x] 4.3 Clean up approval_queue.py to remove callback-related code

## 5. Execution Model Unification

- [x] 5.1 Update _execute_nuclei to run synchronously (wait for result)
- [x] 5.2 Update nuclei tool output message to reflect sync execution

## 6. Testing

- [x] 6.1 Add tests/test_tools.py with ToolOutput return tests
- [x] 6.2 Add tests/test_guardrails.py with validation tests
- [x] 6.3 Add tests/test_approval_queue.py with queue tests
- [x] 6.4 Add tests/test_config.py with config loading tests
- [x] 6.5 Add tests/test_rate_limiter.py with rate limit tests
- [x] 6.6 Run all tests and verify passing

## 7. Manual Verification

- [x] 7.1 Start agent and test read_file
- [x] 7.2 Start agent and test call_api with valid URL
- [x] 7.3 Start agent and test call_api with blocked URL
- [x] 7.4 Verified tool imports work
- [x] 7.5 Rate limiting verified
- [x] 7.6 Verified config values load correctly
- [x] 7.7 All tests pass (46/46)