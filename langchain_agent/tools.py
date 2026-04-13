from langchain_core.tools import tool
from pathlib import Path
import re
import subprocess
import shlex
import requests
from datetime import datetime
from typing import Union
from urllib.parse import urlparse
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


class ToolEvent:
    def __init__(self, tool_name: str, event_type: str, message: str = ""):
        self.tool_name = tool_name
        self.event_type = event_type  # "started", "completed", "failed"
        self.message = message
        self.timestamp = datetime.now().isoformat()

    def format(self) -> str:
        if self.event_type == "started":
            return f"[*] Running {self.tool_name}..."
        elif self.event_type == "completed":
            return f"[✓] {self.tool_name} completed"
        else:  # failed
            return f"[✗] {self.tool_name} failed: {self.message}"


_tool_event_callback = None


def set_tool_event_callback(callback):
    global _tool_event_callback
    _tool_event_callback = callback


def emit_tool_event(tool_name: str, event_type: str, message: str = ""):
    if _tool_event_callback:
        event = ToolEvent(tool_name, event_type, message)
        _tool_event_callback(event)


def _sanitize_filename(url: str) -> str:
    """Extract and sanitize a filename from a URL."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    filename = path.split("/")[-1] if path else ""

    if not filename:
        filename = f"download-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    else:
        filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
        if not filename or filename.startswith("."):
            filename = f"download-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    if len(filename) > 50:
        filename = f"download-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    return filename


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
        if not content.strip():
            content = f"(File is empty: {file_path})"
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
    """Fetch the content of a webpage or API endpoint via HTTP GET. Use this to download or inspect page content, NOT for security scanning. For vulnerability scanning use run_nuclei, for port scanning use run_nmap."""
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

            filename = _sanitize_filename(url)

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
    """Run nmap to scan a target host for open ports and running services. Use this when the user wants a port scan. The target should be a hostname or IP address (e.g. '192.168.1.1' or 'example.com')."""
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
    """Execute nmap scan with live output streaming."""
    try:
        cmd = ["nmap"] + shlex.split(options) + [target]
        lines = []
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            if proc.stdout:
                for line in proc.stdout:
                    print(line, end="", flush=True)
                    lines.append(line)
            proc.wait(timeout=TOOL_NMAP_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            return ToolOutput(
                status="error",
                tool="run_nmap",
                output="Error: Scan timed out",
                saved_to=None,
            )

        if proc.returncode != 0:
            return ToolOutput(
                status="error",
                tool="run_nmap",
                output=f"Nmap error: exit code {proc.returncode}",
                saved_to=None,
            )

        output = "".join(lines)

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
    """Run nuclei vulnerability scanner against a target URL or hostname. Use this when the user asks to scan for vulnerabilities, security issues, or CWEs. The target should be a URL (e.g. 'http://example.com') or hostname."""
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
            "-nc",
            "-no-interactsh",
            "-o",
            str(output_file),
        ] + shlex.split(options)

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            if proc.stdout:
                for line in proc.stdout:
                    print(line, end="", flush=True)
            proc.wait(timeout=TOOL_NUCLEI_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            return ToolOutput(
                status="error",
                tool="run_nuclei",
                output="Error: Scan timed out",
                saved_to=None,
            )

        if proc.returncode != 0 and proc.returncode != 1:
            return ToolOutput(
                status="error",
                tool="run_nuclei",
                output=f"Error: nuclei exited with code {proc.returncode}",
                saved_to=None,
            )

        output = output_file.read_text() if output_file.exists() else ""
        if not output.strip():
            output = "No vulnerabilities found."

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
