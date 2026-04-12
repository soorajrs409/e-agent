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
ollama pull llama3
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

- Check if input exceeds 5000 characters
- Check for blocked prompt injection phrases

### `run_nmap` blocked

Possible causes:

- target contains `127.0.0.1`, `localhost`, or `169.254.169.254`
- options include a flag outside allowlist: `-sV`, `-sS`, `-Pn`, `-F`, `-O`

## Logs

### Agent log

- path: `logs/agent.log`
- logs user messages with timestamp

## Configuration

Edit `langchain_agent/config.py`:

```python
MODEL_NAME = "llama3"
OLLAMA_HOST = "http://127.0.0.1:11434"
AGENT_NAME = "electron-agent"
LOG_FILE = "logs/agent.log"
```
