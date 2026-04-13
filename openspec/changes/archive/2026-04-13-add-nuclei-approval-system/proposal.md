## Why

The agent currently supports basic tools (read_file, call_api, run_nmap) suitable for general use. For bug bounty hunting, users need vulnerability scanning capabilities (nuclei) and a sandboxed environment with approval-based execution for privileged commands to ensure safety when shared or self-hosted.

## What Changes

- Add `run_nuclei` tool with full template selection support
- Implement approval-based execution system for privileged tools (`/approve`, `/deny`, `/approve-all`)
- Expand `config.yaml` to include sandbox path, tool categories (auto/approval), approval timeout
- Create sandbox workspace structure at `{workspace}/sandbox/{scans,downloads,temp}`
- Implement 7-day rotating audit logs with approval/denial tracking
- Keep `run_nmap` as auto-run (non-privileged network scan)

## Capabilities

### New Capabilities
- `nuclei-scanning`: Vulnerability scanning with nuclei, full template selection
- `approval-system`: Queue-based approval for privileged tool execution
- `sandbox-workspace`: Isolated workspace for tool outputs and downloads
- `audit-logging`: Comprehensive logging with rotation

### Modified Capabilities
- (none yet - existing tools unchanged)

## Impact

- **Code**: `langchain_agent/tools.py` (add nuclei), `langchain_agent/guardrails.py` (expand), `main.py` (approval handling), `config.yaml` (expanded config)
- **Config**: Add sandbox path, tool categories, approval settings
- **Dependencies**: `nuclei` binary required on host
- **Documentation**: README updates for approval commands
