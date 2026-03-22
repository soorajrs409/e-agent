import requests

MCP_SERVERS = ["http://127.0.0.1:8001"]

MCP_SERVER = MCP_SERVERS[0]

TOOLS_CACHE = None

def call_tool(tool_name: str, args: dict):
    for server in MCP_SERVERS:
        try:
            url = f"{server}/tools/{tool_name}"

            r = requests.post(url, json=args, timeout=600)

            # DEBUG
            print(f"[MCP] {url} -> {r.status_code}")

            # Check empty response
            if not r.text.strip():
                return {"error": "Empty response from tool server"}

            # Try safe JSON parse
            try:
                return r.json()
            except Exception:
                return {
                    "error": f"Invalid JSON response: {r.text[:200]}"
                }

        except Exception as e:
            print(f"[MCP] Failed {server}: {e}")

    return {"error": f"Tool {tool_name} failed on all servers"}



def discover_tools():

    global TOOLS_CACHE

    if TOOLS_CACHE is not None:
        return TOOLS_CACHE


    all_tools = []

    for server in MCP_SERVERS:
        try:
            r = requests.get(f"{server}/tools", timeout=5)
            data = r.json()

            for tool in data.get("tools", []):
                # print(f"[debug] {tool}")
                tool["server"] = server
                all_tools.append(tool)

        except Exception as e:
            print(f"[MCP] Failed to reach {server}: {e}")

    TOOLS_CACHE = all_tools
    return TOOLS_CACHE