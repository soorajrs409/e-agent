from ollama import Client
from agent.prompt import SYSTEM_PROMT
from agent.config import MODEL_NAME, OLLAMA_HOST
from agent.tools import read_file, call_api, run_nmap
import json
from agent.guardrails import (
    validate_user_input,
    validate_tool_call,
    filter_output
)


client = Client(host=OLLAMA_HOST)

def execute_tool(tool_name, args):
    if tool_name == "read_file":
        return read_file(**args)
    
    elif tool_name == "call_api":
        return call_api(**args)
    
    elif tool_name == "run_nmap":
        return run_nmap(**args)

    else:
        return "[-] Unknown Tool"

def agent_stream_chat(user_input: str) -> str:

    is_valid, reason = validate_user_input(user_input)

    if not is_valid:
        print(f"[-] [GUARD] {reason}")
        return
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMT},
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

            result = execute_tool(tool_call["tool"], tool_call.get("args", {}))
            print(f"[+] TOOL RESULT")

            safe_result = filter_output(result)
            print(safe_result)

    except:
        pass