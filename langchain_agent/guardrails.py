import ipaddress
import re
import socket
from urllib.parse import urlparse

from langchain_agent.config import (
    GUARDRAILS_MAX_INPUT_LENGTH,
    GUARDRAILS_BLOCKED_TARGETS,
)

DNS_TIMEOUT = 5

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/32"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("::ffff:127.0.0.0/104"),
]

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


def resolve_host_to_ips(hostname: str) -> list[str] | None:
    """Resolve a hostname to a list of IP address strings.

    Returns None if resolution fails or times out.
    Uses a thread with timeout to prevent blocking DNS lookups.
    """
    import threading

    result: list[str] | None = None
    error: Exception | None = None

    def _resolve():
        nonlocal result, error
        try:
            addr_results = socket.getaddrinfo(
                hostname, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM
            )
            result = list({r[4][0] for r in addr_results})
        except Exception as e:
            error = e

    thread = threading.Thread(target=_resolve, daemon=True)
    thread.start()
    thread.join(timeout=DNS_TIMEOUT)

    if thread.is_alive():
        return None

    if error is not None:
        return None

    return result


def is_blocked_ip(ip_str: str) -> bool:
    """Check if an IP address string falls within any blocked network range."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False

    for network in BLOCKED_IP_NETWORKS:
        if addr in network:
            return True

    return False


def _is_hostname_blocked(hostname: str) -> tuple[bool, str]:
    """Check if a hostname resolves to a blocked IP, with string-based fallback."""
    hostname_lower = hostname.lower()

    for blocked in GUARDRAILS_BLOCKED_TARGETS:
        if re.search(rf"(?:^|\.){re.escape(blocked)}(?:$|\.)", hostname_lower):
            return True, f"Blocked target: '{blocked}' is not allowed"

    ips = resolve_host_to_ips(hostname)
    if ips is not None:
        for ip in ips:
            if is_blocked_ip(ip):
                return True, f"Internal URL target '{hostname}' is not allowed"
    else:
        if hostname_lower in ("127.0.0.1", "localhost"):
            return True, f"Blocked target: '{hostname_lower}' is not allowed"

    return False, ""


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
    hostname = target.lower().strip()

    for blocked in GUARDRAILS_BLOCKED_TARGETS:
        if re.search(rf"(?:^|\.){re.escape(blocked)}(?:$|\.)", hostname):
            return False, f"Blocked target: '{blocked}' is not allowed"

    try:
        addr = ipaddress.ip_address(hostname)
        if is_blocked_ip(str(addr)):
            return False, f"Blocked target: '{target}' is not allowed"
    except ValueError:
        pass

    ips = resolve_host_to_ips(hostname)
    if ips is not None:
        for ip in ips:
            if is_blocked_ip(ip):
                return False, f"Blocked target: '{target}' is not allowed"

    return True, ""


def validate_nuclei_target(target: str) -> tuple[bool, str]:
    """Validate nuclei scan target.

    Args:
        target: The target URL or hostname

    Returns:
        Tuple of (is_valid, reason_if_invalid)
    """
    parsed = urlparse(target)
    hostname = (parsed.hostname or target).lower().strip()

    for blocked in GUARDRAILS_BLOCKED_TARGETS:
        if re.search(rf"(?:^|\.){re.escape(blocked)}(?:$|\.)", hostname):
            return False, f"Blocked target: '{blocked}' is not allowed"

    try:
        addr = ipaddress.ip_address(hostname)
        if is_blocked_ip(str(addr)):
            return False, f"Blocked target: '{target}' is not allowed"
    except ValueError:
        pass

    if parsed.hostname:
        ips = resolve_host_to_ips(parsed.hostname)
        if ips is not None:
            for ip in ips:
                if is_blocked_ip(ip):
                    return False, f"Blocked target: '{target}' is not allowed"

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

    hostname = parsed.hostname
    if not hostname:
        return False, "URL hostname is required"

    blocked, reason = _is_hostname_blocked(hostname)
    if blocked:
        return False, reason

    return True, ""
