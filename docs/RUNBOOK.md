# Runbook

Operational guide for running and troubleshooting the e-agent.

## Startup Order

### 1. Create the environment

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. Start Ollama

```bash
ollama serve
ollama pull llama3.1
```

### 3. Start the CLI agent

```bash
python main.py
```

Type `exit` to quit.

## Quick Health Checks

### Ollama

```bash
curl -s http://127.0.0.1:11434/api/tags
```

Expected: JSON with locally available model tags.

### Import verification

```bash
source .venv/bin/activate
python -c "from langchain_agent import agent; print('OK')"
```

### LangGraph agent creation

```bash
source .venv/bin/activate
python -c "from langchain_agent.agent import create_langgraph_agent; print('OK')"
```

## Tool Chaining

### Approving tools that require approval

When the agent runs a tool that requires approval:

```
[*] Running run_nuclei...
[✗] run_nuclei failed: approval required
[approval_required] Use /approve abc123 to execute this command.
```

Approve the single tool:

```bash
/approve abc123
```

After approval, the scan runs with live output streaming to the terminal.
Nuclei shows its banner, template loading progress, and findings as they
are discovered. Nmap shows port scan results line by line.

Note: After approval, only the approved tool runs. If the request was part
of a multi-tool chain, the chain does not resume automatically. Re-issue
the original prompt to continue.

### Checking pending approvals

Currently there is no CLI command to list pending approvals. The agent
displays the request ID when approval is needed. Use `/approve <id>` or
`/deny <id>` with the displayed ID.

### Auto-approve all requests

For testing, auto-approve a tool:

```bash
/approve-all run_nmap
/approve-all run_nuclei
```

This allows all requests of that type without manual approval.

## Live Tool Events

The agent streams tool lifecycle events:

```
[*] Running read_file...        # Tool started
[✓] read_file completed         # Success
[*] Running run_nmap...          # Next tool started
[✗] run_nmap failed: <error>    # Failure
```

For nmap and nuclei, scan output streams live during `/approve` execution.
Results are also saved to `sandbox/scans/`. Empty results are reported as
"No vulnerabilities found".

## Troubleshooting

### Connection refused to Ollama

- Confirm `ollama serve` is running
- Verify `langchain_agent/config.py` has `OLLAMA_HOST = "http://127.0.0.1:11434"`
- CLI prints `[OLLAMA ERROR]` on connection failure

### Agent doesn't use tools

- Verify tools are bound: `python -c "from langchain_agent.tools import tools; print([t.name for t in tools])"`
- Check model supports tool calling (llama3.1+ recommended)
- The 8B quantized model may hallucinate tool calls (wrong parameters, calling tools for conversational input) — a larger model (70B+) produces more reliable results

### LLM calls wrong tool or wrong parameters

- The agent uses a system prompt with exact parameter names to guide tool selection
- If the model calls `call_api` with `target` instead of `url`, or calls `call_api` instead of `run_nuclei` for vulnerability scanning, this is an LLM limitation
- Upgrading to a larger model (e.g. `llama3.1:70b`) improves tool selection accuracy
- The system prompt lists tool parameter names explicitly to minimize hallucination

### Scan shows no output during approval

- nmap and nuclei stream output live to the terminal during `/approve`
- If you see only `[*] Executing run_nuclei (this may take a while)...` with no further output, the scan is running but may take time to find results
- Nuclei output (banner, progress, findings) streams from both stdout and stderr
- If a scan finds no vulnerabilities, it reports "No vulnerabilities found"

### Empty file when reading scan results

- If nuclei finds zero vulnerabilities, the results file will be empty and `read_file` reports "(File is empty: ...)"
- This is correct behavior — the scan completed but found nothing

### Input rejected

- Check if input exceeds `guardrails.max_input_length` in config.yaml
- Check for blocked prompt injection phrases

### Tool blocked

- Target contains blocked address — guardrails resolve hostnames via DNS and check resolved IPs against blocked ranges (`127.0.0.0/8`, `::1`, `0.0.0.0`, `169.254.0.0/16`)
- Alternate IP representations (hex, octal, decimal, IPv6-mapped) are also blocked via DNS resolution
- Hostnames matching blocked targets use boundary matching (e.g., `not-localhost.com` is allowed, `localhost` is blocked)
- Options include flag outside `guardrails.nmap.allowed_flags`
- Check error message for specific reason

### Rate limited

- Exceeded `guardrails.rate_limit.max_per_minute` for that tool

### Chain too long

If a chain exceeds 5 tools, the chain ends after the 5th tool. Any
remaining tools are not executed. Re-issue the command to continue.

### Approval expired

Approval requests expire (default 5 minutes, configurable in `config.yaml`):

```
Request abc123 has expired. Please re-issue the command.
```

### Error during chain

On tool error, the chain terminates:

```
[error] Error: Disallowed switch '-T4'
```

Re-issue the command with corrected parameters.

## Logs

### Agent log

- path: `logs/agent.log`
- logs user messages with timestamp

### Scan outputs

- path: `sandbox/scans/nmap-*.txt`
- path: `sandbox/scans/nuclei-*.txt`

## Configuration

Configuration in `config.yaml`:

```yaml
model:
  name: "llama3.1"
  ollama_host: "http://127.0.0.1:11434"

agent:
  name: "electron-agent"
  log_file: "logs/agent.log"

sandbox:
  path: "./sandbox"
  directories: ["scans", "downloads", "temp"]

tools:
  auto: [read_file, call_api]
  approval_required: [run_nmap, run_nuclei]
  call_api:
    timeout: 20
  nmap:
    timeout: 600
  nuclei:
    timeout: 600

guardrails:
  max_input_length: 5000
  blocked_targets:
    - "127.0.0.1"
    - "localhost"
    - "localhost.localdomain"
    - "169.254.169.254"
  nmap:
    allowed_flags: ["-sV", "-sS", "-Pn", "-F", "-O"]
  rate_limit:
    enabled: true
    max_per_minute: 30

logging:
  rotation_days: 7
  backup_count: 7
```

## Chain State Debugging

To see chain state during execution:

```python
from langchain_agent.agent import stream_agent
from langchain_agent.tools import ToolEvent

def debug_cb(e: ToolEvent):
    print(f"EVENT: {e.format()}")

# Run with debug output
for chunk in stream_agent("your prompt", event_callback=debug_cb):
    print(chunk)
```

## Commands Summary

| Command | Description |
|---------|-------------|
| `python main.py` | Start agent |
| `exit` | Quit |
| `/approve <id>` | Approve pending request |
| `/deny <id>` | Deny pending request |
| `/approve-all <tool>` | Auto-approve all of tool type |