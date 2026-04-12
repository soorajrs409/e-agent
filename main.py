import os
import logging
import logging.handlers

from langchain_agent.agent import stream_agent
from langchain_agent.guardrails import validate_input
from langchain_agent.config import (
    LOG_FILE,
    AGENT_NAME,
    get_sandbox_path,
    SANDBOX_DIRS,
    TOOLS_APPROVAL_REQUIRED,
)
from langchain_agent.approval_queue import get_approval_queue, ApprovalStatus


def setup_logging():
    os.makedirs(os.path.dirname(LOG_FILE) or "logs", exist_ok=True)

    handler = logging.handlers.TimedRotatingFileHandler(
        LOG_FILE, when="midnight", interval=7, backupCount=7, encoding="utf-8"
    )
    handler.suffix = "%Y-%m-%d"

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


logger = setup_logging()
approval_queue = get_approval_queue()


def setup_sandbox():
    sandbox = get_sandbox_path()
    sandbox.mkdir(parents=True, exist_ok=True)
    for subdir in SANDBOX_DIRS:
        (sandbox / subdir).mkdir(parents=True, exist_ok=True)


setup_sandbox()


def log_event(role: str, text: str):
    logger.info(f"[{role}] {text}")


def handle_approve(request_id: str) -> str:
    result = approval_queue.approve(request_id)
    if result["status"] == ApprovalStatus.APPROVED:
        logger.info(f"APPROVED: {request_id}")
        tool_name = result["tool"]
        args = result["args"]

        if tool_name == "run_nuclei":
            from langchain_agent.tools import _execute_nuclei

            output = _execute_nuclei(args.get("target", ""), args.get("options", ""))
            logger.info(
                f"TOOL_EXEC: {tool_name} output: {len(output.output) if hasattr(output, 'output') else 0} chars"
            )
            saved_info = f"\n[Saved to: {output.saved_to}]" if output.saved_to else ""
            return f"Executing {tool_name}...\n{output.output}{saved_info}"

        if tool_name == "run_nmap":
            from langchain_agent.tools import _execute_nmap

            output = _execute_nmap(args.get("target", ""), args.get("options", ""))
            logger.info(
                f"TOOL_EXEC: {tool_name} output: {len(output) if output else 0} chars"
            )
            return f"Executing {tool_name}...\n{output}"

        from langchain_agent.tools import get_tool_function

        tool_func = get_tool_function(tool_name)
        if tool_func:
            target = args.get("target", "")
            output = tool_func.invoke(
                {"target": target, "options": args.get("options", "")}
            )
            logger.info(f"TOOL_EXEC: {tool_name} output: {len(str(output))} chars")
            return f"Executing {tool_name}...\n{output}"
        return f"Tool {tool_name} not found"
    elif result["status"] == ApprovalStatus.EXPIRED:
        logger.info(f"EXPIRED: {request_id}")
        return f"Request {request_id} has expired. Please re-issue the command."
    return f"Request {request_id} not found"


def handle_deny(request_id: str) -> str:
    result = approval_queue.deny(request_id)
    if result["status"] == ApprovalStatus.DENIED:
        logger.info(f"DENIED: {request_id}")
        return f"Request {request_id} denied."
    elif result["status"] == ApprovalStatus.EXPIRED:
        logger.info(f"EXPIRED: {request_id}")
        return f"Request {request_id} has expired. Please re-issue the command."
    return f"Request {request_id} not found"


def handle_approve_all(tool_name: str) -> str:
    # Allow both "nuclei" and "run_nuclei" aliases
    if tool_name == "nuclei":
        tool_name = "run_nuclei"
    elif tool_name == "nmap":
        tool_name = "run_nmap"

    if tool_name not in TOOLS_APPROVAL_REQUIRED:
        return f"Tool {tool_name} does not require approval."
    approval_queue.approve_all(tool_name)
    logger.info(f"APPROVE_ALL: {tool_name}")
    return (
        f"All {tool_name} commands will now execute without approval for this session."
    )


def parse_command(user_input: str) -> tuple[str | None, str]:
    user_input = user_input.strip()

    if user_input.startswith("/approve "):
        request_id = user_input[9:].strip()
        return None, handle_approve(request_id)

    if user_input.startswith("/deny "):
        request_id = user_input[5:].strip()
        return None, handle_deny(request_id)

    if user_input.startswith("/approve-all "):
        tool_name = user_input[13:].strip()
        return None, handle_approve_all(tool_name)

    return user_input, None


def main():
    logger.info(f"Agent started: {AGENT_NAME}")

    print(f"[*] {AGENT_NAME} started (type exit to quit)")
    print(f"[*] Sandbox: {get_sandbox_path()}")
    print(f"[*] Approval-required tools: {', '.join(TOOLS_APPROVAL_REQUIRED)}\n")

    approval_queue.cleanup_expired()

    while True:
        user_input = input("[+] you -> ")

        if user_input.lower() == "exit":
            logger.info("Agent exited by user")
            break

        user_input, command_response = parse_command(user_input)

        if command_response:
            logger.info(f"USER: {user_input}")
            print(command_response)
            print()
            continue

        logger.info(f"USER: {user_input}")

        is_valid, reason = validate_input(user_input)
        if not is_valid:
            logger.warning(f"GUARD_REJECTED: {reason}")
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
            logger.error(f"RUNTIME_ERROR: {type(e).__name__}: {str(e)}")
            print(f"\n[-] Runtime error: {e}")


if __name__ == "__main__":
    main()
