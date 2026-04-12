## Why

Several timeout and logging values are hardcoded in the codebase instead of being configurable via config.yaml. This limits flexibility - users can't adjust timeouts for slow networks or customize logging rotation without code changes.

## What Changes

1. Add `tools.call_api.timeout` - HTTP request timeout (currently hardcoded at 20s)
2. Add `tools.nmap.timeout` - nmap scan timeout (currently hardcoded at 600s)
3. Add `tools.nuclei.timeout` - nuclei scan timeout (currently hardcoded at 600s)
4. Add `logging.rotation_days` - log rotation interval (currently hardcoded at 7 days)
5. Add `logging.backup_count` - number of backup logs to keep (currently hardcoded at 7)
6. Update config.py to load these new settings
7. Update tools.py and main.py to use config values

## Capabilities

### New Capabilities
(None - this is implementation-only, making existing functionality configurable via config)

### Modified Capabilities
(None - no behavior change, just config loading)

## Impact

- `config.yaml` - add new settings sections
- `langchain_agent/config.py` - load new config values
- `langchain_agent/tools.py` - use config for timeouts
- `main.py` - use config for logging settings