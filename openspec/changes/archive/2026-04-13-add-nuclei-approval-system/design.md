## Context

The agent currently runs as a single-process CLI with basic tools (read_file, call_api, run_nmap). It lacks:
- Vulnerability scanning capabilities needed for bug bounty workflows
- Sandboxed workspace for tool outputs
- Approval system for privileged commands
- Comprehensive logging for audit trails

This change adds nuclei integration, sandbox workspace, and approval-based execution for self-hosted deployment where users want controlled access to scanning tools.

## Goals / Non-Goals

**Goals:**
- Add `run_nuclei` tool with full template selection support
- Implement in-CLI approval system (`/approve`, `/deny`, `/approve-all`)
- Create sandbox workspace structure for tool outputs
- Add 7-day rotating audit logs
- Expand config.yaml for sandbox path and tool categories

**Non-Goals:**
- User authentication (self-hosted = user's responsibility)
- Persistent approval queue across restarts
- Real-time notification system (polling via CLI acceptable)
- Web UI for approvals (CLI only for now)

## Decisions

### 1. Approval System: In-CLI Command Parsing

**Decision:** Handle approval commands in main.py CLI loop before passing to agent.

```python
if user_input.startswith("/approve "):
    handle_approval(user_input)
elif user_input.startswith("/deny "):
    handle_denial(user_input)
elif user_input.startswith("/approve-all "):
    handle_approve_all(user_input)
else:
    pass_to_agent(user_input)
```

**Rationale:**
- Simple to implement within existing main.py loop
- No additional processes or endpoints needed
- User stays in same CLI interface

**Alternatives:**
- Separate API endpoint for approvals — adds complexity, not needed for self-hosted
- File-based queue — harder to integrate with agent execution flow

---

### 2. Approval Queue: In-Memory with UUID

**Decision:** Store pending approvals in in-memory dict with UUID keys.

```python
approval_queue: dict[str, dict] = {
    "abc-123": {
        "tool": "run_nuclei",
        "args": {...},
        "timestamp": datetime.now(),
        "expires_at": datetime.now() + timedelta(minutes=5)
    }
}
```

**Rationale:**
- Simple, fast lookup by UUID
- 5-minute expiration easy to implement
- Self-hosted use = single user = no concurrency concerns

**Alternatives:**
- Database-backed queue — adds dependency, over-engineered for single-user
- File-based queue — harder to handle expiration, race conditions

---

### 3. Tool Categories: Config-Driven

**Decision:** Define tool categories in config.yaml:

```yaml
tools:
  auto:
    - read_file
    - call_api
    - run_nmap
  approval_required:
    - run_nuclei
```

**Rationale:**
- Easy to add new tools to approval required list
- User can reconfigure without code changes
- Clear separation of concerns

**Alternatives:**
- Hardcoded in Python — harder to maintain
- Per-session flags — too volatile, hard to audit

---

### 4. Sandbox Path: Workspace-relative with config override

**Decision:** Default to `{workspace}/sandbox/`, configurable via `config.yaml`.

```yaml
sandbox:
  path: ./sandbox  # or absolute path like /home/user/bounty-sandbox
```

**Rationale:**
- Self-hosted users likely want to separate sandbox from repo
- Relative path works for simple setup
- Absolute path for production deployments

---

### 5. Logging: TimedRotatingFileHandler

**Decision:** Use Python's logging.handlers.TimedRotatingFileHandler with 7-day retention.

```python
handler = logging.handlers.TimedRotatingFileHandler(
    "logs/agent.log",
    when="midnight",
    interval=7,
    backupCount=7
)
```

**Rationale:**
- Built-in rotation, no manual cleanup needed
- Meets 7-day requirement
- Structured log format for parsing

---

### 6. Nuclei Tool: Shell Execution with Guard

**Decision:** Execute nuclei via subprocess, validate all arguments.

```python
@tool
def run_nuclei(target: str, options: str = "-severity critical,high,medium,low") -> str:
    # Guard: check target not blocked
    # Guard: parse options, validate template flags
    # Execute: subprocess.run(["nuclei", ...])
    # Output: save to sandbox/scans/
```

**Rationale:**
- Follows existing nmap pattern for consistency
- Option validation prevents injection
- Sandbox write ensures output doesn't pollute host

---

### 7. Read File Sandbox Enforcement

**Decision:** Add path validation to read_file tool to restrict to sandbox.

```python
@tool
def read_file(file_path: str) -> str:
    resolved = Path(file_path).resolve()
    sandbox = get_sandbox_path().resolve()
    if not str(resolved).startswith(str(sandbox)):
        return "Access denied: path outside sandbox"
    # ... read file
```

**Rationale:**
- Critical for shared/self-hosted security
- Prevents reading of config files, credentials, etc.
- Works with configurable sandbox path

---

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| User runs nuclei against wrong target | Self-hosted = user's responsibility; add warning in prompt |
| Approval queue grows unbounded | 5-minute timeout auto-expires stale requests |
| Large tool output fills logs | Truncate logs at 10KB, full output in sandbox |
| Sandbox path doesn't exist | Create directories on startup |
| Nuclei binary not installed | Detect missing binary, show install instructions |

---

## Migration Plan

1. **Backup**: Users backup existing config.yaml (if customized)
2. **Update config**: Add new sections to config.yaml (merge carefully)
3. **Install nuclei**: Ensure nuclei binary in PATH
4. **Test auto tools**: Verify read_file, call_api, run_nmap still work
5. **Test approval**: Trigger nuclei, approve, verify execution
6. **Verify logs**: Check log files created and rotating

**Rollback**: Revert config.yaml, remove new code files.

---

## Open Questions

1. **Approve-all session scope**: Should approve-all persist across CLI restarts? (Design: no, session-only for simplicity)

2. **Output truncation**: How much tool output to log? Full vs. truncated? (Design: truncate at 10KB in log, full in sandbox file)

3. **Config migration**: Should we auto-update config.yaml or require manual edit? (Design: manual merge, safer for users)

4. **Nuclei rate limiting**: Should we add between-scan delays? (Design: not in v1, user's responsibility)
