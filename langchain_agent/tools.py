from langchain_core.tools import tool
from pathlib import Path
import subprocess
import shlex
import requests
from langchain_agent.guardrails import validate_nmap_target


@tool
def read_file(file_path: str) -> str:
    """Read file contents from disk.

    Args:
        file_path: Path to the file to read

    Returns:
        File contents as string
    """
    try:
        content = Path(file_path).read_text()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def call_api(url: str) -> str:
    """Make HTTP GET request to a URL.

    Args:
        url: The URL to fetch

    Returns:
        HTTP response body as string
    """
    try:
        r = requests.get(url, timeout=20)
        return r.text
    except Exception as e:
        return f"Error fetching URL: {str(e)}"


@tool
def run_nmap(target: str, options: str = "-sV") -> str:
    """Run network scan to find open ports/services.

    Args:
        target: Target IP address or hostname to scan
        options: Nmap command line options (default: -sV)

    Returns:
        Nmap scan output as string
    """
    allowed, reason = validate_nmap_target(target)
    if not allowed:
        return f"Guard blocked: {reason}"

    allowed_flags = ["-sV", "-sS", "-Pn", "-F", "-O"]

    option_list = shlex.split(options)

    for opt in option_list:
        if opt not in allowed_flags:
            return f"Error: Disallowed switch '{opt}'"

    try:
        cmd = ["nmap"] + option_list + [target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            return f"Nmap error: {result.stderr}"

        return result.stdout

    except subprocess.TimeoutExpired:
        return "Error: Scan timed out"
    except Exception as e:
        return f"Error: {str(e)}"


tools = [read_file, call_api, run_nmap]
