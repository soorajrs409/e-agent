import requests

MCP_SERVERS = ["http://127.0.0.1:8001"]

MCP_SERVER = MCP_SERVERS[0]

TOOLS_CACHE = None


def call_tool(tool_name: str, args: dict):
    last_error = None

    for server in MCP_SERVERS:
        try:
            url = f"{server}/tools/{tool_name}"

            r = requests.post(url, json=args, timeout=600)

            # DEBUG
            print(f"[MCP] {url} -> {r.status_code}")

            if r.status_code >= 400:
                last_error = f"HTTP {r.status_code} from {server}"
                print(f"[MCP] Server returned HTTP {r.status_code}")
                continue

            # Check empty response
            if not r.text.strip():
                last_error = f"Empty response from {server}"
                print("[MCP] Empty response from tool server")
                continue

            # Try safe JSON parse
            try:
                payload = r.json()
            except ValueError:
                last_error = f"Invalid JSON response from {server}: {r.text[:200]}"
                print(f"[MCP] Invalid JSON response: {r.text[:200]}")
                continue

            if not isinstance(payload, dict):
                last_error = f"Unexpected response shape from {server}"
                print(f"[MCP] Unexpected response shape from {server}: {type(payload).__name__}")
                continue

            if "error" in payload:
                last_error = payload["error"]
                print(f"[MCP] Tool error from {server}: {payload['error']}")
                continue

            return payload

        except Exception as e:
            last_error = str(e)
            print(f"[MCP] Failed {server}: {e}")

    return {"error": last_error or f"Tool {tool_name} failed on all servers"}



def discover_tools(force_refresh: bool = False):

    global TOOLS_CACHE

    if TOOLS_CACHE is not None and not force_refresh:
        return TOOLS_CACHE


    all_tools = []

    for server in MCP_SERVERS:
        try:
            r = requests.get(f"{server}/tools", timeout=5)
            r.raise_for_status()
            data = r.json()

            for tool in data.get("tools", []):
                tool_with_server = dict(tool)
                tool_with_server["server"] = server
                all_tools.append(tool_with_server)

        except Exception as e:
            print(f"[MCP] Failed to reach {server}: {e}")

    TOOLS_CACHE = all_tools
    return TOOLS_CACHE
