import requests

MCP_SERVER = "http://127.0.0.1:8001"


def call_tool(tool_name: str, args:dict):
    r = requests.post(
        f"{MCP_SERVER}/tools/{tool_name}",
        json=args,
        timeout=600
    )

    return r.json()