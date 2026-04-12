import re
from urllib.parse import urlparse

from langchain_agent.config import (
    GUARDRAILS_MAX_INPUT_LENGTH,
    GUARDRAILS_BLOCKED_TARGETS,
)

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
    if len(user_input) > GUARDRAILS_MAX_INPUT_LENGTH:
        return False, f"Input exceeds {GUARDRAILS_MAX_INPUT_LENGTH} character limit"

    input_lower = user_input.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, input_lower, re.IGNORECASE):
            return False, "Blocked prompt injection pattern detected"

    return True, ""


def validate_nmap_target(target: str) -> tuple[bool, str]:
    """Validate nmap scan target.

    Args:
        target: The target IP/hostname

    Returns:
        Tuple of (is_valid, reason_if_invalid)
    """
    target_lower = target.lower()

    for blocked in GUARDRAILS_BLOCKED_TARGETS:
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

    for blocked in GUARDRAILS_BLOCKED_TARGETS:
        if blocked in target_lower:
            return False, f"Blocked target: '{blocked}' is not allowed"

    return True, ""


def validate_url(url: str) -> tuple[bool, str]:
    """Validate URL for HTTP requests.

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_valid, reason_if_invalid)
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    if parsed.scheme not in ("http", "https"):
        return (
            False,
            f"URL scheme '{parsed.scheme}' is not allowed. Use http:// or https://",
        )

    if parsed.scheme == "http":
        host = parsed.hostname or ""
        if (
            host.startswith("127.")
            or host == "localhost"
            or host.startswith("169.254.")
        ):
            return False, f"Internal URL target '{host}' is not allowed"

    if parsed.scheme == "https":
        host = parsed.hostname or ""
        if (
            host.startswith("127.")
            or host == "localhost"
            or host.startswith("169.254.")
        ):
            return False, f"Internal URL target '{host}' is not allowed"

    return True, ""
