# Runbook

Operational guide for running and troubleshooting the local CLI agent and tool server.

## Services

You need these processes:

1. Ollama API
2. FastAPI tool server
3. CLI agent

Start them in that order.

## Startup Order

### 1. Create the environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Ollama

```bash
ollama serve
ollama pull llama3
```

### 3. Start the tool server

```bash
uvicorn server:app --app-dir tool-servers/core_server --host 127.0.0.1 --port 8001 --reload
```

### 4. Start the CLI agent

```bash
python main.py
```

## Important Startup Note

The agent discovers tools and builds its system prompt when `agent/core.py` is imported. Because of that:

- start the tool server before `python main.py`
- if the tool server was down when the CLI started, restart the CLI after the tool server is healthy

Without that restart, the process can continue using an empty or stale tool list from cache.

## Quick Health Checks

### Ollama

```bash
curl -s http://127.0.0.1:11434/api/tags
```

Expected: JSON with locally available model tags.

### Tool server

```bash
curl -s http://127.0.0.1:8001/tools
```

Expected shape:

```json
{
  "tools": [
    {
      "name": "read_file",
      "description": "Read file contents from disk",
      "args": ["file_path"]
    },
    {
      "name": "call_api",
      "description": "Make HTTP GET request to a URL",
      "args": ["url"]
    },
    {
      "name": "run_nmap",
      "description": "Run network scan to find open ports/services",
      "args": ["target", "options"]
    }
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

```bash
curl -s -X POST http://127.0.0.1:8001/tools/run_nmap \
  -H 'Content-Type: application/json' \
  -d '{"target":"scanme.nmap.org","options":"-F"}'
```

Notes:

- the route is currently exposed and should not return `404`
- only these options are accepted: `-sV`, `-sS`, `-Pn`, `-F`, `-O`
- agent-side guardrails still block scan targets like `localhost` and `169.254.169.254`

## Common Failures

### The agent answers normally but never uses tools

Check these first:

- the tool server was running before the CLI started
- `http://127.0.0.1:8001/tools` returns a valid tool list
- restart the CLI if the tool server came up after the CLI

Why this happens:

- tool discovery happens at import time
- discovered tools are cached in `TOOLS_CACHE`
- the system prompt is built once per process

### `Connection refused` to Ollama

- confirm `ollama serve` is running
- verify `agent/config.py` points to `http://127.0.0.1:11434`

### `Connection refused` to the tool server

- confirm the uvicorn process is running on port `8001`
- verify `agent/mcp_client.py` includes `http://127.0.0.1:8001` in `MCP_SERVERS`

### Tool execution prints `TOOL ERROR`

- inspect the tool server console for request failures
- verify the endpoint returns JSON and not an HTML error page
- confirm local dependencies like `nmap` are installed if using `run_nmap`

### Tool invocation does not trigger even though the model tried

- the agent looks for a JSON object in the full model response
- mixed prose plus malformed JSON may fail parsing and fall back to normal text output
- the current parse path swallows JSON parse errors

### `run_nmap` is rejected

Possible causes:

- the target contains `127.0.0.1`
- the target contains `localhost`
- the target contains `169.254.169.254`
- the options include a flag outside the allowlist

## Logs

### Agent log

- path: `logs/agent.log`
- current behavior: logs user messages only

### Server logs

- emitted by the uvicorn process to stdout/stderr

## Operational Notes

- `call_tool()` tries each configured MCP server in sequence.
- `discover_tools()` caches tool metadata for the duration of the process.
- `call_api` performs a simple HTTP GET and returns raw text.
- Tool output is filtered for selected sensitive phrases before display.
- This stack is a local development prototype and should not be exposed publicly without authentication and tighter policy controls.
