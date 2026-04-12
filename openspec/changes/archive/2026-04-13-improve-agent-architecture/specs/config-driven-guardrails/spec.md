## ADDED Requirements

### Requirement: Guardrails SHALL be configurable via config.yaml
Guardrail parameters SHALL be defined in config.yaml under a "guardrails" section, allowing customization without code changes.

#### Scenario: max_input_length configurable
- **WHEN** guardrails.max_input_length is set in config.yaml
- **THEN** validate_input SHALL enforce that length limit

#### Scenario: blocked_targets configurable
- **WHEN** guardrails.blocked_targets list is set in config.yaml
- **THEN** validate_nmap_target and validate_nuclei_target SHALL block those targets

#### Scenario: nmap allowed_flags configurable
- **WHEN** guardrails.nmap.allowed_flags is set in config.yaml
- **THEN** run_nmap SHALL only allow those flags

#### Scenario: default values when config missing
- **WHEN** guardrails config section is missing or values are not set
- **THEN** system SHALL use safe defaults (current hardcoded values)