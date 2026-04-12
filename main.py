import os
import sys
from datetime import datetime

from langchain_agent.agent import stream_agent
from langchain_agent.guardrails import validate_input
from langchain_agent.config import LOG_FILE, AGENT_NAME

os.makedirs("logs", exist_ok=True)


def log_event(role: str, text: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()}[{role}] [{text}]\n")


def main():
    print(f"[*] {AGENT_NAME} started (type exit to quit)\n")

    while True:
        user_input = input("[+] you -> ")

        if user_input.lower() == "exit":
            break

        log_event("USER", user_input)

        is_valid, reason = validate_input(user_input)
        if not is_valid:
            print(f"[-] [GUARD] {reason}")
            continue

        print(f"[*] {AGENT_NAME} -> ", end="", flush=True)

        try:
            for chunk in stream_agent(user_input):
                print(chunk, end="", flush=True)
            print()
        except KeyboardInterrupt:
            print("\n[ interrupted ]")
        except Exception as e:
            print(f"\n[-] Runtime error: {e}")


if __name__ == "__main__":
    main()
