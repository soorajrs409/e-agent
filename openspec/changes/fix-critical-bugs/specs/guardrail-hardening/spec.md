## ADDED Requirements

### Requirement: URL validation blocks alternate IP representations of internal hosts
`validate_url` SHALL block URLs that resolve to internal addresses regardless of representation.

#### Scenario: IPv6 loopback blocked
- **WHEN** URL hostname is `::1` or `[::1]`
- **THEN** validation returns `(False, "Internal URL target is not allowed")`

#### Scenario: IPv6-mapped IPv4 loopback blocked
- **WHEN** URL hostname is `::ffff:127.0.0.1` or `[::ffff:127.0.0.1]`
- **THEN** validation returns `(False, "Internal URL target is not allowed")`

#### Scenario: Hex decimal IP blocked
- **WHEN** URL hostname is `0x7f000001` (hex representation of 127.0.0.1)
- **THEN** validation returns `(False, "Internal URL target is not allowed")`

#### Scenario: Octal IP blocked
- **WHEN** URL hostname is `017700000001` (octal representation of 127.0.0.1)
- **THEN** validation returns `(False, "Internal URL target is not allowed")`

#### Scenario: Decimal IP blocked
- **WHEN** URL hostname is `2130706433` (decimal representation of 127.0.0.1)
- **THEN** validation returns `(False, "Internal URL target is not allowed")`

#### Scenario: All-interfaces IP blocked
- **WHEN** URL hostname is `0.0.0.0`
- **THEN** validation returns `(False, "Internal URL target is not allowed")`

#### Scenario: Empty hostname blocked
- **WHEN** URL has no hostname (e.g. `http:///etc/passwd`)
- **THEN** validation returns `(False, "URL hostname is required")`

#### Scenario: DNS name resolving to internal IP blocked
- **WHEN** URL hostname resolves via DNS to a blocked IP address
- **THEN** validation returns `(False, "Internal URL target is not allowed")`

#### Scenario: DNS resolution timeout falls back to string check
- **WHEN** DNS resolution times out (3 seconds)
- **THEN** validation falls back to string-based blocked target checks

### Requirement: Nmap and nuclei target validation uses word-boundary matching
`validate_nmap_target` and `validate_nuclei_target` SHALL use word-boundary regex matching instead of substring matching.

#### Scenario: Legitimate hostname containing "localhost" is allowed
- **WHEN** target is `not-localhost.example.com`
- **THEN** validation returns `(True, "")`

#### Scenario: Exact localhost is blocked
- **WHEN** target is `localhost`
- **THEN** validation returns `(False, "Blocked target: 'localhost' is not allowed")`

#### Scenario: Hostname starting with blocked string is blocked
- **WHEN** target starts with `127.0.0.1` as a host prefix
- **THEN** validation blocks the target

### Requirement: Nmap and nuclei target validation blocks alternate IP representations
Both validators SHALL block targets that resolve to internal addresses, consistent with URL validation.

#### Scenario: Hex IP in nmap target blocked
- **WHEN** nmap target is `0x7f000001`
- **THEN** validation returns `(False, reason)`

#### Scenario: IPv6 loopback in nuclei target blocked
- **WHEN** nuclei target is `http://[::1]/`
- **THEN** validation returns `(False, reason)`

### Requirement: Download filenames are sanitized
`call_api` SHALL produce safe filenames from URLs by removing or replacing invalid characters.

#### Scenario: URL with query string
- **WHEN** URL is `http://example.com/api/data?key=value`
- **THEN** filename does not contain `?` or `&` characters

#### Scenario: URL with fragment
- **WHEN** URL is `http://example.com/page#section`
- **THEN** filename does not contain `#` character

#### Scenario: URL with no path
- **WHEN** URL is `http://example.com/`
- **THEN** filename defaults to `download-YYYYMMDD-HHMMSS`

### Requirement: Deny command uses correct string offset
`parse_command` SHALL use consistent string offsets for all slash commands.

#### Scenario: /deny command with request ID
- **WHEN** user input is `/deny abc123`
- **THEN** request_id is `abc123` (no leading/trailing whitespace artifacts)