# Runbook

Operational guide for running and troubleshooting the local CLI agent.

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
python -c "from langchain_agent import agent_executor; print('OK')"
```

## Common Failures

### `Connection refused` to Ollama

- confirm `ollama serve` is running
- verify `langchain_agent/config.py` has `OLLAMA_HOST = "http://127.0.0.1:11434"`
- CLI prints `[OLLAMA ERROR]` on connection failure

### Agent doesn't use tools

- Verify tools are bound: `python -c "from langchain_agent.tools import tools; print([t.name for t in tools])"`
- Check model supports tool calling (llama3.1+ recommended)

### Input rejected

- Check if input exceeds `guardrails.max_input_length` in config.yaml
- Check for blocked prompt injection phrases

### `run_nmap` blocked

- Target contains blocked address from `guardrails.blocked_targets`
- Options include flag outside `guardrails.nmap.allowed_flags`

### `call_api` blocked

Possible causes:
- URL scheme not http/https
- URL targets internal address (localhost, 127.x.x.x)

### Rate limited

Possible causes:
- Exceeded `guardrails.rate_limit.max_per_minute` for that tool

## Logs

### Agent log

- path: `logs/agent.log`
- logs user messages with timestamp

## Configuration
Configuration is in `config.yaml`:

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

guardrails:
  max_input_length: 5000
  blocked_targets:
    - "127.0.0.1"
    - "localhost"
    - "169.254.169.254"
  nmap:
    allowed_flags: ["-sV", "-sS", "-Pn", "-F", "-O"]
  rate_limit:
    enabled: true
    max_per_minute: 30
```

## Troubleshooting

### Input rejected
- Check if input exceeds `guardrails.max_input_length` in config.yaml
- Check for blocked prompt injection phrases

### `run_nmap` blocked
- Target contains blocked address from `guardrails.blocked_targets`
- Options include flag outside `guardrails.nmap.allowed_flags`

### `call_api` blocked
- URL scheme not http/https
- URL targets internal address (localhost, 127.x.x.x)

### Rate limited
- Exceeded `guardrails.rate_limit.max_per_minute` for tool
