import re

INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"disregard rules",
    r"you are now",
    r"reveal system prompt",
    r"bypass security",
    r"act as root"
]


BLOCKED_TARGETS = [
    "127.0.0.1",
    "localhost",
    "169.254.169.254"  # cloud metadata
]


SENSITIVE_PATTERNS = [
    r"system prompt",
    r"internal policy",
    r"hidden instructions"
]


def validate_user_input(user_input: str) -> tuple[bool, str]:
    text = user_input.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return False, "[-] Blocked: Prompt injection attempt detected."
        
    if len(user_input) > 5000:
        return False, "[-] Blocked: Input too long"
    

    return True, ""


def validate_tool_call(tool: str, args: dict) -> tuple[bool, str]:

    if tool == "run_nmap":
        target = args.get("target", "")

        for blocked in BLOCKED_TARGETS:
            if blocked in target:
                return False, f"[-] Blocked: Scanning {blocked} is not allowed"
            
    return True, ""


def filter_output(text: str) -> str:
    lowered = text.lower()

    for pattern in SENSITIVE_PATTERNS:
        if pattern in lowered:
            return "[Filtered sensitive content]"
    
    return text