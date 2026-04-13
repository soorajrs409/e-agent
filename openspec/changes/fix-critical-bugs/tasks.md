## 1. Guardrail Validation Overhaul

- [x] 1.1 Add `resolve_host_to_ips()` helper in `guardrails.py` that uses `socket.getaddrinfo()` with 3-second timeout, returns list of IP addresses
- [x] 1.2 Add `is_blocked_ip()` helper that checks an IP address against blocked ranges: `127.0.0.0/8`, `::1`, `::ffff:127.0.0.0/104`, `0.0.0.0`, `169.254.0.0/16`; uses `ipaddress` module for proper CIDR matching
- [x] 1.3 Rewrite `validate_url()` to: parse hostname with `urlparse`, check for `None`/empty hostname, resolve DNS, check resolved IPs with `is_blocked_ip()`, fall back to string checks on timeout
- [x] 1.4 Rewrite `validate_nmap_target()` and `validate_nuclei_target()` to: use hostname-boundary regex for blocked string matching, then resolve target via DNS and check with `is_blocked_ip()`
- [x] 1.5 Add `import socket` and `import ipaddress` to `guardrails.py`

## 2. Nmap Approval Handler Fix

- [x] 2.1 Fix `main.py:84` logger line: change `len(output)` to `len(output.output)` for nmap branch
- [x] 2.2 Fix `main.py:86` return line: change `f"Executing {tool_name}...\n{output}"}` to use `output.output` and append `saved_to` like the nuclei handler pattern

## 3. Deny Command Slicing Fix

- [x] 3.1 Fix `main.py:140`: change `user_input[5:]` to `user_input[6:]` for `/deny` command parsing

## 4. Call API Filename Sanitization

- [x] 4.1 Add filename sanitization in `call_api()`: extract path component from URL via `urlparse`, replace `?`, `&`, `#`, and other non-safe characters with underscores, keep alphanumeric/dash/underscore/dot only

## 5. Tests

- [x] 5.1 Add test cases in `test_guardrails.py` for: IPv6 loopback, hex IP, octal IP, decimal IP, `0.0.0.0`, empty hostname, DNS resolution blocking
- [x] 5.2 Add test cases for false positive fixes: `not-localhost.com`, `localhost.example.com` should be allowed
- [x] 5.3 Add test cases in `test_tools.py` for `call_api` filename sanitization (query strings, fragments)
- [x] 5.4 Add test for nmap approval handler in `test_agent.py` verifying output type and log format
- [x] 5.5 Add test for `/deny` command parsing in `test_agent.py`
- [x] 5.6 Run full test suite and verify all tests pass