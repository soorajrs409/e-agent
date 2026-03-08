from ollama import Client
from agent.prompt import SYSTEM_PROMPT
from agent.config import MODEL_NAME, OLLAMA_HOST
import json
from agent.guardrails import (
    validate_user_input,
    validate_tool_call,
    filter_output
)

from agent.mcp_client import call_tool


client = Client(host=OLLAMA_HOST)


def agent_stream_chat(user_input: str) -> str:

    is_valid, reason = validate_user_input(user_input)

    if not is_valid:
        print(f"[-] [GUARD] {reason}")
        return
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    stream = client.chat(
        model=MODEL_NAME,
        messages=messages,
        stream=True
    )

    full_response = ""

    for chunk in stream:
        content = chunk["message"]["content"]
        full_response += content
        print(content, end="", flush=True)

    print()

    try:

        tool_call = json.loads(full_response)

        if "tool" in tool_call:
            print("\n[+] Executing tool...\n")

            allowed, reason = validate_tool_call(tool_call["tool"], tool_call.get("args", {}))

            if not allowed:
                print(f"[-] [GUARD] {reason}")
                return

            resp = call_tool(tool_call["tool"], tool_call.get("args", {}))

            if "error" in resp:
                print(f"[-] Tool error: {resp['error']}")

            else:

                print(f"[+] TOOL RESULT")

                safe_result = filter_output(resp["output"])
                print(safe_result)

    except:
        pass