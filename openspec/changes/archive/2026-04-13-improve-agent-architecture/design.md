## Context

The e-agent is a CLI tool powered by LangChain + Ollama with tools for file reading, HTTP calls, nmap scanning, and nuclei vulnerability scanning. It uses an approval queue for potentially dangerous tools.

Current state issues identified:
1. **Approval callback unused** - `approval_queue.py` accepts callback but it's never called; main.py re-executes
2. **Inconsistent tool outputs** - `read_file` returns string, `call_api` returns string, `run_nmap` returns string, `run_nuclei` returns `ToolOutput` pydantic
3. **Hardcoded values** - Allowed nmap flags in `tools.py:81`, blocked targets in `guardrails.py:3`, max input in `guardrails.py:4`
4. **No URL validation** - `call_api` accepts any URL string
5. **Mixed execution** - `run_nmap` is synchronous (waits), `run_nuclei` is async (fires and returns PID)
6. **No tests** - No test coverage

## Goals / Non-Goals

**Goals:**
- Remove unused code (approval callback)
- Standardize all tool outputs to return `ToolOutput` model
- Move hardcoded values to config.yaml
- Add URL validation for call_api
- Unify execution (both sync or both async - choose sync for consistency)
- Add basic rate limiting
- Add unit tests for tools and guardrails

**Non-Goals:**
- No new tools
- No changes to agent prompting or LLM behavior
- No persistence layer changes
- No UI changes

## Decisions

### D1: Tool Output Standardization
**Decision:** All tools return `ToolOutput` pydantic model (status, tool, output, saved_to)

**Rationale:** Pydantic provides validation, clear schema, and IDE autocomplete. Consistent typing is more maintainable than mixed string/model returns.

**Alternative considered:** All tools return plain strings - rejected because loses metadata like `saved_to` path.

### D2: Config Location for Guardrails
**Decision:** Add new `guardrails` section to config.yaml

**Rationale:** Keeps related config together. Clear separation from tool config.

**Alternative considered:** Extend existing `tools` section - rejected because guardrails aren't tools.

```yaml
guardrails:
  max_input_length: 5000
  blocked_targets:
    - "127.0.0.1"
    - "localhost"
    - "169.254.169.254"
  nmap:
    allowed_flags:
      - "-sV"
      - "-sS"
      - "-Pn"
      - "-F"
      - "-O"
  rate_limit:
    enabled: true
    max_per_minute: 30
```

### D3: Execution Model
**Decision:** Make both `run_nmap` and `run_nuclei` synchronous (wait for result)

**Rationale:** Simpler mental model for CLI tool. User sees result immediately. Easier to test.

**Alternative considered:** Keep nuclei async - rejected for inconsistency.

### D4: URL Validation
**Decision:** Allow only http:// and https:// schemes; block local/network URLs

**Rationale:** prevent SSRF attacks, match guardrails philosophy for blocking local targets.

```python
def validate_url(url: str) -> tuple[bool, str]:
    # Block file://, ftp://, etc
    # Block internal IPs in URL
    # Block localhost, 127.x.x.x
```

### D5: Rate Limiting Implementation
**Decision:** Simple in-memory counter per tool, per minute window

**Rationale:** CLI tool has single user - no distributed rate limiting needed. Simple is enough.

**Alternative considered:** Redis-backed - rejected - adds dependency and complexity for single-user CLI.

## Risks / Trade-offs

[R1] Config validation - Users may provide invalid config → Add validation with defaults fallback

[R2] Breaking change if someone parses tool output → Document that outputs are now pydantic-derived dicts

[R3] Rate limiting resets on restart → Acceptable for CLI use case

[Trade-off] Sync execution slower perceived - But ensures accurate status reporting

## Migration Plan

1. Add config schema changes first
2. Update tools to use config values
3. Refactor tool outputs
4. Add guardrails
5. Add tests
6. Verify manually

No rollback needed - all internal changes.

## Open Questions

- Q: Should rate limiting apply per-tool or globally?
  - A: Per-tool (each tool has own limit) is more useful for CLI