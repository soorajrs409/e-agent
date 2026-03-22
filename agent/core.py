from ollama import Client
from agent.prompt import SYSTEM_PROMPT
from agent.config import MODEL_NAME, OLLAMA_HOST
import json

from agent.guardrails import (
    validate_user_input,
    validate_tool_call,
    filter_output
)

from agent.mcp_client import call_tool, discover_tools
from agent.prompt_builder import build_tools_section
from agent.base_prompt import BASE_SYSTEM_PROMPT
import re


client = Client(host=OLLAMA_HOST)


def build_system_prompt():
    tools = discover_tools()
    tools_section = build_tools_section(tools)
    return BASE_SYSTEM_PROMPT + "\n\n" + tools_section


system_prompt = build_system_prompt()


def agent_stream_chat(user_input: str):
    # 🔹 Step 0: Input Guard
    is_valid, reason = validate_user_input(user_input)
    if not is_valid:
        print(f"[-] [GUARD] {reason}")
        return

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    stream = client.chat(
        model=MODEL_NAME,
        messages=messages,
        stream=True
    )

    full_response = ""

    # 🔹 Step 1: Capture response ONLY (no printing yet)
    for chunk in stream:
        content = chunk["message"]["content"]
        full_response += content

    clean = full_response.strip()

    # 🔹 Step 2: Detect tool call safely
    tool_call = None
    is_tool = False

    match = re.search(r"\{.*\}", clean, re.DOTALL)

    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, dict) and "tool" in parsed:
                tool_call = parsed
                is_tool = True
        except Exception:
            is_tool = False

    # 🔹 Step 3: Handle Tool Execution
    if is_tool:
        tool_name = tool_call["tool"]
        args = tool_call.get("args", {})

        print("\n[+] Executing tool...\n")

        # 🛡️ Tool Guard
        allowed, reason = validate_tool_call(tool_name, args)
        if not allowed:
            print(f"[-] [GUARD BLOCKED] {reason}")
            return

        # 🔌 MCP Tool Call
        resp = call_tool(tool_name, args)

        if not isinstance(resp, dict):
            print("[-] Invalid response from tool")
            return

        if "error" in resp:
            print(f"[-] TOOL ERROR: {resp['error']}")
            return

        if "output" not in resp:
            print("[-] Tool returned unexpected format")
            print(resp)
            return

        print("[+] TOOL RESULT")
        safe_result = filter_output(resp["output"])
        print(safe_result)

    # 🔹 Step 4: Normal Chat Response
    else:
        print(clean)