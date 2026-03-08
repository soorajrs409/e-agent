# Runbook

Operational guide for running and debugging the current AI agent + tool-server stack.

## Services

You need both services running:

1. Ollama model API
2. FastAPI tool server (`tool-servers/core_server/server.py`)

Then run the CLI agent (`main.py`).

## Startup Order

## 1) Python environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Start Ollama

```bash
ollama serve
ollama pull llama3
```

## 3) Start tool server

```bash
uvicorn server:app --app-dir tool-servers/core_server --host 127.0.0.1 --port 8001 --reload
```

## 4) Run CLI agent

```bash
python main.py
```

## Quick Health Checks

### Ollama health

```bash
curl -s http://127.0.0.1:11434/api/tags
```

Expected: JSON containing local model tags.

### Tool server health

```bash
curl -s http://127.0.0.1:8001/tools
```

Expected shape:

```json
{
  "tools": [
    {"name": "read_file", "args": ["file_path"]},
    {"name": "call_api", "args": ["url"]},
    {"name": "run_nmap", "args": ["target", "options"]}
  ]
}
```

## Manual Endpoint Checks

### `read_file`

```bash
curl -s -X POST http://127.0.0.1:8001/tools/read_file \
  -H 'Content-Type: application/json' \
  -d '{"file_path":"README.md"}'
```

### `call_api`

```bash
curl -s -X POST http://127.0.0.1:8001/tools/call_api \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}'
```

### `run_nmap`

Current code caveat: route is not decorated as `POST /tools/run_nmap`, so direct calls may return 404 until route registration is added.

## Common Failures

### `Connection refused` to Ollama from agent

- confirm `ollama serve` is running
- verify `agent/config.py` uses `OLLAMA_HOST = http://127.0.0.1:11434`

### `Connection refused` to tool server

- confirm `uvicorn ... --port 8001` is running
- verify `agent/mcp_client.py` points to `http://127.0.0.1:8001`

### Tool response error in CLI

- the CLI prints `[-] Tool error: ...` when server returns `{ "error": ... }`
- check tool-server console logs for traceback/details

### Tool invocation never happens

- model output must be valid JSON as full response
- mixed prose + JSON will fail parsing silently in current `agent/core.py`

## Logs

### Agent logs

- file: `logs/agent.log`
- currently logs user messages only

### Server logs

- emitted in the uvicorn process stdout/stderr

## Operational Notes

- This is currently a dev prototype.
- Use localhost/network restrictions when testing `call_api` and scanning features.
- Treat tool server as a privileged surface; avoid exposing it publicly without auth and policy controls.
