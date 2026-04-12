import re

BLOCKED_TARGETS = ["127.0.0.1", "localhost", "169.254.169.254"]
MAX_INPUT_LENGTH = 5000

INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"ignore all previous",
    r"disregard previous",
    r"forget previous",
    r"you are now",
    r"pretend you are",
    r"system prompt",
    r"reveal your",
    r"ignore your",
    r"disregard your",
    r"overwrite your",
]


def validate_input(user_input: str) -> tuple[bool, str]:
    """Validate user input before processing.

    Args:
        user_input: The raw user input string

    Returns:
        Tuple of (is_valid, reason_if_invalid)
    """
    if len(user_input) > MAX_INPUT_LENGTH:
        return False, f"Input exceeds {MAX_INPUT_LENGTH} character limit"

    input_lower = user_input.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, input_lower, re.IGNORECASE):
            return False, f"Blocked prompt injection pattern detected"

    return True, ""


def validate_nmap_target(target: str) -> tuple[bool, str]:
    """Validate nmap scan target.

    Args:
        target: The target IP/hostname

    Returns:
        Tuple of (is_valid, reason_if_invalid)
    """
    target_lower = target.lower()

    for blocked in BLOCKED_TARGETS:
        if blocked in target_lower:
            return False, f"Blocked target: '{blocked}' is not allowed"

    return True, ""


def validate_nuclei_target(target: str) -> tuple[bool, str]:
    """Validate nuclei scan target.

    Args:
        target: The target URL or hostname

    Returns:
        Tuple of (is_valid, reason_if_invalid)
    """
    target_lower = target.lower()

    for blocked in BLOCKED_TARGETS:
        if blocked in target_lower:
            return False, f"Blocked target: '{blocked}' is not allowed"

    return True, ""
