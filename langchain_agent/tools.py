from langchain_core.tools import tool
from pathlib import Path
import subprocess
import shlex
import requests
from datetime import datetime
from typing import Union
from pydantic import BaseModel
import os

from langchain_agent.guardrails import validate_nmap_target, validate_nuclei_target
from langchain_agent.config import (
    get_sandbox_path,
    TOOL_CALL_API_TIMEOUT,
    TOOL_NMAP_TIMEOUT,
    TOOL_NUCLEI_TIMEOUT,
)
from langchain_agent.approval_queue import get_approval_queue
from langchain_agent.rate_limiter import get_rate_limiter


class ApprovalRequired(BaseModel):
    status: str = "approval_required"
    request_id: str
    tool: str
    message: str


class ToolOutput(BaseModel):
    status: str = "success"
    tool: str
    output: str
    saved_to: str | None = None


@tool
def read_file(file_path: str) -> ToolOutput:
    """Read file contents from disk within sandbox."""
    rate_limiter = get_rate_limiter()
    allowed, reason = rate_limiter.is_allowed("read_file")
    if not allowed:
        return ToolOutput(
            status="blocked",
            tool="read_file",
            output=reason,
            saved_to=None,
        )

    try:
        sandbox = get_sandbox_path()
        resolved = Path(file_path).resolve()

        if not str(resolved).startswith(str(sandbox)):
            return ToolOutput(
                status="blocked",
                tool="read_file",
                output=f"Access denied: path outside sandbox ({sandbox})",
                saved_to=None,
            )

        if not resolved.exists():
            return ToolOutput(
                status="error",
                tool="read_file",
                output=f"Error: file not found: {file_path}",
                saved_to=None,
            )

        content = resolved.read_text()
        return ToolOutput(
            status="success",
            tool="read_file",
            output=content,
            saved_to=None,
        )
    except Exception as e:
        return ToolOutput(
            status="error",
            tool="read_file",
            output=f"Error reading file: {str(e)}",
            saved_to=None,
        )


@tool
def call_api(url: str) -> ToolOutput:
    """Make HTTP GET request to a URL."""
    from langchain_agent.guardrails import validate_url

    rate_limiter = get_rate_limiter()
    allowed, reason = rate_limiter.is_allowed("call_api")
    if not allowed:
        return ToolOutput(
            status="blocked",
            tool="call_api",
            output=reason,
            saved_to=None,
        )

    allowed, reason = validate_url(url)
    if not allowed:
        return ToolOutput(
            status="blocked",
            tool="call_api",
            output=reason,
            saved_to=None,
        )

    try:
        r = requests.get(url, timeout=TOOL_CALL_API_TIMEOUT)
        content = r.text

        saved_path = None
        if url.startswith("http://") or url.startswith("https://"):
            sandbox = get_sandbox_path()
            downloads_dir = sandbox / "downloads"
            downloads_dir.mkdir(parents=True, exist_ok=True)

            filename = url.split("/")[-1] or "download"
            if len(filename) > 50:
                filename = f"download-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            file_path = downloads_dir / filename
            file_path.write_text(content)
            saved_path = str(file_path)

        return ToolOutput(
            status="success",
            tool="call_api",
            output=content,
            saved_to=saved_path,
        )
    except Exception as e:
        return ToolOutput(
            status="error",
            tool="call_api",
            output=f"Error fetching URL: {str(e)}",
            saved_to=None,
        )


@tool
def run_nmap(target: str, options: str = "-sV") -> Union[ApprovalRequired, ToolOutput]:
    """Run network scan to find open ports/services."""
    from langchain_agent.config import GUARDRAILS_NMAP_ALLOWED_FLAGS

    rate_limiter = get_rate_limiter()
    allowed, reason = rate_limiter.is_allowed("run_nmap")
    if not allowed:
        return ToolOutput(
            status="blocked",
            tool="run_nmap",
            output=reason,
            saved_to=None,
        )

    allowed, reason = validate_nmap_target(target)
    if not allowed:
        return ToolOutput(
            status="blocked",
            tool="run_nmap",
            output=reason,
            saved_to=None,
        )

    option_list = shlex.split(options)

    for opt in option_list:
        if opt not in GUARDRAILS_NMAP_ALLOWED_FLAGS:
            return ToolOutput(
                status="blocked",
                tool="run_nmap",
                output=f"Error: Disallowed switch '{opt}'",
                saved_to=None,
            )

    queue = get_approval_queue()
    if queue.is_auto_approved("run_nmap"):
        return _execute_nmap(target, options)

    request_id = queue.add_request(
        "run_nmap",
        {"target": target, "options": options},
    )

    if request_id == "auto_approved":
        return _execute_nmap(target, options)

    return ApprovalRequired(
        status="approval_required",
        request_id=request_id,
        tool="run_nmap",
        message=f"Use /approve {request_id} to execute this command.",
    )


def _execute_nmap(target: str, options: str) -> ToolOutput:
    """Execute nmap scan."""
    try:
        cmd = ["nmap"] + shlex.split(options) + [target]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=TOOL_NMAP_TIMEOUT
        )

        if result.returncode != 0:
            return ToolOutput(
                status="error",
                tool="run_nmap",
                output=f"Nmap error: {result.stderr}",
                saved_to=None,
            )

        output = result.stdout

        sandbox = get_sandbox_path()
        scans_dir = sandbox / "scans"
        scans_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_target = target.replace("://", "-").replace("/", "-").replace(":", "-")
        file_path = scans_dir / f"nmap-{safe_target}-{timestamp}.txt"
        file_path.write_text(output)

        return ToolOutput(
            status="success",
            tool="run_nmap",
            output=f"{output}\n\n[Saved to: {file_path}]",
            saved_to=str(file_path),
        )

    except subprocess.TimeoutExpired:
        return ToolOutput(
            status="error",
            tool="run_nmap",
            output="Error: Scan timed out",
            saved_to=None,
        )
    except Exception as e:
        return ToolOutput(
            status="error",
            tool="run_nmap",
            output=f"Error: {str(e)}",
            saved_to=None,
        )


@tool
def run_nuclei(
    target: str, options: str = "-severity critical,high,medium,low"
) -> Union[ApprovalRequired, ToolOutput]:
    """Run vulnerability scan using nuclei."""
    rate_limiter = get_rate_limiter()
    allowed, reason = rate_limiter.is_allowed("run_nuclei")
    if not allowed:
        return ToolOutput(
            status="blocked",
            tool="run_nuclei",
            output=reason,
            saved_to=None,
        )

    allowed, reason = validate_nuclei_target(target)
    if not allowed:
        return ToolOutput(
            status="blocked",
            tool="run_nuclei",
            output=f"Guard blocked: {reason}",
            saved_to=None,
        )

    queue = get_approval_queue()
    if queue.is_auto_approved("run_nuclei"):
        return _execute_nuclei(target, options)

    request_id = queue.add_request(
        "run_nuclei",
        {"target": target, "options": options},
    )

    if request_id == "auto_approved":
        return _execute_nuclei(target, options)

    return ApprovalRequired(
        status="approval_required",
        request_id=request_id,
        tool="run_nuclei",
        message=f"Use /approve {request_id} to execute this command.",
    )


def _execute_nuclei(target: str, options: str) -> ToolOutput:
    """Execute nuclei scan synchronously."""
    search_paths = os.environ.get("PATH", "").split(":") + [
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
    ]
    nuclei_bin = None
    for path in search_paths:
        candidate = os.path.join(path, "nuclei")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            nuclei_bin = candidate
            break

    if not nuclei_bin:
        return ToolOutput(
            status="error",
            tool="run_nuclei",
            output="Error: nuclei not found. Install from https://github.com/projectdiscovery/nuclei",
            saved_to=None,
        )

    templates_dir = os.path.expanduser("~/.local/nuclei-templates")
    if not os.path.isdir(templates_dir):
        return ToolOutput(
            status="error",
            tool="run_nuclei",
            output="Error: nuclei templates not found. Run: nuclei -update-templates",
            saved_to=None,
        )

    sandbox = get_sandbox_path()
    scans_dir = sandbox / "scans"
    scans_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_target = target.replace("://", "-").replace("/", "-").replace(":", "-")
    output_file = scans_dir / f"nuclei-{safe_target}-{timestamp}.txt"

    env = os.environ.copy()
    env["TEMPLATES_DIR"] = templates_dir

    try:
        cmd = [
            nuclei_bin,
            "-u",
            target,
            "-silent",
            "-nc",
            "-no-interactsh",
            "-o",
            str(output_file),
        ] + shlex.split(options)

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=TOOL_NUCLEI_TIMEOUT, env=env
        )

        if result.returncode != 0 and result.returncode != 1:
            return ToolOutput(
                status="error",
                tool="run_nuclei",
                output=f"Error: {result.stderr}",
                saved_to=None,
            )

        output = output_file.read_text() if output_file.exists() else result.stdout

        return ToolOutput(
            status="success",
            tool="run_nuclei",
            output=f"Nuclei scan complete. Results saved to: {output_file}\n\n{output}",
            saved_to=str(output_file),
        )

    except subprocess.TimeoutExpired:
        return ToolOutput(
            status="error",
            tool="run_nuclei",
            output="Error: Scan timed out",
            saved_to=None,
        )
    except Exception as e:
        return ToolOutput(
            status="error",
            tool="run_nuclei",
            output=f"Error: {str(e)}",
            saved_to=None,
        )


tools = [read_file, call_api, run_nmap, run_nuclei]


def get_tool_function(tool_name: str):
    tool_map = {
        "read_file": read_file,
        "call_api": call_api,
        "run_nmap": run_nmap,
        "run_nuclei": run_nuclei,
    }
    return tool_map.get(tool_name)
