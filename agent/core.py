from ollama import Client
from agent.config import MODEL_NAME, OLLAMA_HOST
import json
from json import JSONDecodeError

from agent.guardrails import (
    validate_user_input,
    validate_tool_call,
    filter_output
)

from agent.mcp_client import call_tool, discover_tools
from agent.prompt_builder import build_tools_section
from agent.base_prompt import BASE_SYSTEM_PROMPT


client = Client(host=OLLAMA_HOST)


system_prompt = None


def build_system_prompt(force_refresh: bool = False):
    tools = discover_tools(force_refresh=force_refresh)
    tools_section = build_tools_section(tools)
    return BASE_SYSTEM_PROMPT + "\n\n" + tools_section


def get_system_prompt():
    global system_prompt

    if system_prompt is None:
        system_prompt = build_system_prompt(force_refresh=True)
        return system_prompt

    tools = discover_tools()
    if not tools:
        system_prompt = build_system_prompt(force_refresh=True)

    return system_prompt


def extract_tool_call(text: str):
    decoder = json.JSONDecoder()

    for start in (i for i, char in enumerate(text) if char == "{"):
        try:
            parsed, end = decoder.raw_decode(text[start:])
        except JSONDecodeError:
            continue

        trailing_text = text[start + end:].strip()
        if trailing_text and not trailing_text.startswith("```"):
            continue

        if isinstance(parsed, dict) and "tool" in parsed:
            return parsed

    return None


def agent_stream_chat(user_input: str):
    # 🔹 Step 0: Input Guard
    is_valid, reason = validate_user_input(user_input)
    if not is_valid:
        print(f"[-] [GUARD] {reason}")
        return

    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": user_input}
    ]

    try:
        stream = client.chat(
            model=MODEL_NAME,
            messages=messages,
            stream=True
        )
    except Exception as e:
        print(f"[-] [OLLAMA ERROR] {e}")
        return

    full_response = ""

    # 🔹 Step 1: Capture response ONLY (no printing yet)
    for chunk in stream:
        content = chunk["message"]["content"]
        full_response += content

    clean = full_response.strip()

    # 🔹 Step 2: Detect tool call safely
    tool_call = extract_tool_call(clean)
    is_tool = tool_call is not None

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
