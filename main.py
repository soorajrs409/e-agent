import os 
from datetime import datetime
from agent.core import agent_stream_chat
from agent.config import LOG_FILE, AGENT_NAME

os.makedirs("logs", exist_ok=True)

def log_event(role: str, text: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()}[{role}] [{text}]\n")


def main():
    print(f"[*] {AGENT_NAME} stated (type exit to quit)\n")

    while True:
        user_input = input("[+] you -> ")

        if user_input.lower() == "exit":
            break

        log_event("USER", user_input)

        print(f"[*] {AGENT_NAME} -> ", end="", flush=True)

        try:
            agent_stream_chat(user_input)
        except Exception as e:
            print(f"\n[-] Runtime error: {e}")

         # Optional: log response later (we’ll improve this in v2)

if __name__ == "__main__":
    main()
