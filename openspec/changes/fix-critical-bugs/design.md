## Context

The guardrails system uses simple substring matching (`blocked_string in target`) to block internal network targets. This has two failure modes: false negatives (alternate IP representations bypass checks) and false positives (legitimate hostnames containing blocked substrings). The approval handler for nmap has a copy-paste bug from the nuclei handler that crashes on `len(ToolOutput)` and returns the object repr instead of the output string. The `call_api` tool creates filenames from URL paths without sanitizing query strings.

### Current State

- `validate_url`: checks `hostname.startswith("127.")`, `hostname == "localhost"`, `hostname.startswith("169.254.")` — misses IPv6, hex/octal IPs, `0.0.0.0`, `None` hostname
- `validate_nmap_target` / `validate_nuclei_target`: checks `blocked in target_lower` — substring match causes false positives on hosts like `not-localhost.com`
- `handle_approve` (main.py:82-86): nmap branch uses `len(output)` on ToolOutput (crash) and returns `output` instead of `output.output`
- `call_api`: `url.split("/")[-1]` preserves `?`, `&`, `#` in filenames
- `parse_command`: `/deny` uses `[5:]` instead of `[6:]` (masked by `.strip()` but inconsistent)

## Goals / Non-Goals

**Goals:**
- Block all known SSRF bypass vectors (IPv6 loopback, hex/octal/decimal IPs, `0.0.0.0`, empty hostname, IPv6-mapped IPv4)
- Eliminate false positives in target validation (word-boundary matching instead of substring)
- Fix nmap approval handler crash and wrong return value
- Fix `/deny` slicing for consistency
- Sanitize `call_api` download filenames

**Non-Goals:**
- DNS rebanding protection (requires async DNS resolution — out of scope)
- Private IP range blocking (10.x, 172.16-31.x, 192.168.x) — could break legitimate scanning use cases
- Refactoring the approval system to support mid-chain resume (separate concern)
- Adding response size limits to `call_api`

## Decisions

### Decision 1: Resolve hostnames to IPs for validation (instead of pattern matching)

**Choice**: Use `socket.getaddrinfo()` to resolve hostnames, then check resolved IPs against blocked ranges.

**Rationale**: Pattern matching on strings cannot catch all IP representations. DNS resolution is the only reliable way to detect that `0x7f000001` or `[::1]` resolve to localhost. This also eliminates false positives because we check the resolved IP, not the string.

**Alternatives considered**:
- Expand regex patterns for hex/octal/decimal IPs — fragile, always incomplete
- Use `ipaddress` module on parsed URLs — doesn't handle DNS names that resolve to internal IPs
- Block all private ranges (10.x, etc.) — too aggressive for a security scanning tool

**Approach**: Try `socket.getaddrinfo()` first. If resolution fails (no network), fall back to string-based checks as a safety net. Resolution has a 3-second timeout to avoid blocking.

### Decision 2: Word-boundary matching for nmap/nuclei target validation

**Choice**: Use regex word boundaries (`\b`) instead of `in` for substring checks.

**Rationale**: `"localhost" in "not-localhost.com"` incorrectly blocks. `\blocalhost\b` correctly allows `not-localhost.com` while blocking `localhost` as a standalone host.

### Decision 3: Sanitize filenames with `urllib.parse` and character replacement

**Choice**: Parse the URL path component and replace non-alphanumeric characters (except `-`, `_`, `.`) with underscores.

**Rationale**: Simple, deterministic, no filesystem risk. Preserves readability while eliminating `?`, `&`, `#`, spaces, etc.

### Decision 4: Minimal fix for nmap approval handler

**Choice**: Match the nuclei handler pattern exactly — use `output.output` and `output.saved_to`.

**Rationale**: The nuclei handler is correct. Just align the nmap handler to the same pattern.

## Risks / Trade-offs

- **[DNS resolution latency]** → Mitigate with 3-second timeout; if resolution times out, fall back to string checks (conservative: block on match)
- **[DNS rebinding]** → Out of scope. An attacker could point `evil.com` at `127.0.0.1` after validation passes. This requires TOFU (trust-on-first-use) or pinning — deferred.
- **[IPv6 edge cases]** → `::1` (loopback) and `::ffff:127.0.0.1` (IPv6-mapped IPv4) are blocked. Link-local `fe80::` is not blocked since it could be legitimate scanning targets.
- **[Offline operation]** → `socket.getaddrinfo()` requires network. If unavailable, string-based fallback still catches the common cases.