## Why

The agent has architectural inconsistencies and technical debt that make it harder to maintain and extend. The approval system has unused code, tool outputs are inconsistently typed, configuration values are hardcoded, and there's no testing. These are internal improvements that will make the codebase cleaner and more reliable.

## What Changes

1. **Remove unused approval callback** - The callback lambda passed to `queue.add_request` is never used; main.py re-executes directly. Simplify this flow.
2. **Standardize tool output types** - All tools should return consistent types (either all strings or all Pydantic models, not mixed).
3. **Move hardcoded values to config** - Allowed nmap flags, blocked targets, max input length should be in config.yaml.
4. **Add URL validation guardrails** - `call_api` currently has no input validation; add URL scheme and format validation.
5. **Unify execution model** - Make nmap and nuclei execution consistent (both sync or both async).
6. **Add rate limiting** - Basic rate limiting to prevent abuse.
7. **Add unit tests** - Create tests for core functionality.

## Capabilities

### New Capabilities
- `standardized-tool-outputs`: All tools return consistent response types
- `config-driven-guardrails`: Guardrail values configurable via config.yaml
- `url-validation`: Input validation for HTTP requests
- `rate-limiting`: Basic rate limiting for tool usage
- `tool-testing`: Unit tests for tools and guardrails

### Modified Capabilities
- (none - these are internal refactoring changes)

## Impact

- `langchain_agent/tools.py` - Refactor tool returns, add rate limiting
- `langchain_agent/guardrails.py` - Make values configurable, add URL validation
- `langchain_agent/approval_queue.py` - Remove unused callback code
- `langchain_agent/config.py` - Add new config options
- `config.yaml` - Add new configuration values
- New test files in `tests/`