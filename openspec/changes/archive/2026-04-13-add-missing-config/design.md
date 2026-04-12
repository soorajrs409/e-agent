## Context

The project uses config.yaml for configuration but some important values remain hardcoded:
- HTTP timeout in tools.py (20s)
- nmap timeout in tools.py (600s)
- nuclei timeout in tools.py (600s)
- log rotation in main.py (7 days, 7 backups)

Current config.yaml structure already has `tools` and `agent` sections.

## Goals / Non-Goals

**Goals:**
- All timeouts configurable via config.yaml
- Logging settings configurable via config.yaml
- Backward compatible - use defaults when config missing

**Non-Goals:**
- No new tools or features
- No schema changes to existing config format

## Decisions

### D1: Config Structure
**Decision:** Add nested `tools` section with timeout settings

```yaml
tools:
  call_api:
    timeout: 20
  nmap:
    timeout: 600
  nuclei:
    timeout: 600

logging:
  rotation_days: 7
  backup_count: 7
```

**Rationale:** Groups related config together. Matches existing YAML style.

### D2: Default Values
**Decision:** Use current hardcoded values as defaults

- call_api.timeout: 20 (current)
- nmap.timeout: 600 (current)
- nuclei.timeout: 600 (current)
- logging.rotation_days: 7 (current)
- logging.backup_count: 7 (current)

**Rationale:** No behavior change for existing users.

## Risks / Trade-offs

[Risk] Invalid config values → Mitigation: Use type validation with default fallback
[Risk] Users not knowing new options → Update docs/README

## Migration Plan

1. Add new config sections to config.yaml.example
2. Update config.py to load new values
3. Update tools.py to use config values
4. Update main.py to use config values
5. Verify tests still pass
6. Update documentation

No rollback needed - backward compatible.

## Open Questions

None - straightforward config addition.