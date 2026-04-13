## Why

The guardrails system has multiple bypass vulnerabilities that allow scanning internal/localhost resources (SSRF), and the approval handler for nmap crashes with a TypeError when approving scans. Additionally, target validation produces false positives on legitimate hostnames containing blocked substrings. These are security and reliability bugs that need immediate fixes.

## What Changes

- Fix SSRF bypass in `validate_url`, `validate_nmap_target`, and `validate_nuclei_target` that allows internal scanning via IPv6 `::1`, hex/octal/decimal IPs, `0.0.0.0`, and empty hostname
- Fix nmap approval handler crash: `len(output)` on `ToolOutput` raises `TypeError`, and the handler returns `ToolOutput` repr instead of the actual output string
- Fix false positive blocking: substring matching (`"localhost" in target`) blocks legitimate hosts like `not-localhost.com`
- Fix `/deny` command off-by-one slicing: `[5:]` should be `[6:]` for consistency with `/approve` pattern
- Fix `call_api` filename generation: URLs with query strings (`?`, `&`, `#`) create invalid filenames

## Capabilities

### New Capabilities

- `guardrail-hardening`: Enhanced guardrail validation that blocks alternate IP representations, private ranges, IPv6 loopback, and uses word-boundary matching to eliminate false positives

### Modified Capabilities

- `multi-tool-chains`: Fix nmap approval handler crash that breaks the approval-then-resume flow

## Impact

- `langchain_agent/guardrails.py` — complete rewrite of all three validation functions
- `langchain_agent/tools.py` — fix `call_api` filename sanitization
- `main.py` — fix nmap approval handler (`len(output)` → `len(output.output)`, return `output.output` instead of `output`), fix `/deny` slicing
- Tests in `tests/test_guardrails.py`, `tests/test_tools.py` — add cases for bypass scenarios and false positives