import yaml


def build_tools_section(tools: list[dict]) -> str:
    structured = {"tools": []}

    for tool in tools:
        structured["tools"].append({
            "name": tool["name"],
            "description": tool.get("description", "No description"),
            "arguments": {
                arg: "string" for arg in tool.get("args", [])
            }
        })

    yaml_output = yaml.dump(structured, sort_keys=False,default_flow_style=False)

    # return f"Available tools (YAML format):\n\n{yaml_output}"
    return f"""
            Available tools are defined below in YAML format.

            Use these tools exactly as specified when generating tool calls.

            {yaml_output}
            """