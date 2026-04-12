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
from langchain_agent.config import get_sandbox_path, TOOLS_APPROVAL_REQUIRED
from langchain_agent.approval_queue import get_approval_queue


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
def read_file(file_path: str) -> Union[str, ToolOutput]:
    """Read file contents from disk within sandbox."""
    try:
        sandbox = get_sandbox_path()
        resolved = Path(file_path).resolve()

        if not str(resolved).startswith(str(sandbox)):
            return f"Access denied: path outside sandbox ({sandbox})"

        if not resolved.exists():
            return f"Error: file not found: {file_path}"

        return resolved.read_text()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def call_api(url: str) -> Union[str, ToolOutput]:
    """Make HTTP GET request to a URL."""
    try:
        r = requests.get(url, timeout=20)
        content = r.text

        if url.startswith("http://") or url.startswith("https://"):
            sandbox = get_sandbox_path()
            downloads_dir = sandbox / "downloads"
            downloads_dir.mkdir(parents=True, exist_ok=True)

            filename = url.split("/")[-1] or "download"
            if len(filename) > 50:
                filename = f"download-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            file_path = downloads_dir / filename
            file_path.write_text(content)

        return content
    except Exception as e:
        return f"Error fetching URL: {str(e)}"


@tool
def run_nmap(target: str, options: str = "-sV") -> Union[str, ToolOutput]:
    """Run network scan to find open ports/services."""
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

        output = result.stdout

        sandbox = get_sandbox_path()
        scans_dir = sandbox / "scans"
        scans_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        file_path = scans_dir / f"nmap-{target}-{timestamp}.txt"
        file_path.write_text(output)

        return f"{output}\n\n[Saved to: {file_path}]"

    except subprocess.TimeoutExpired:
        return "Error: Scan timed out"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def run_nuclei(
    target: str, options: str = "-severity critical,high,medium,low"
) -> Union[ApprovalRequired, ToolOutput]:
    """Run vulnerability scan using nuclei."""
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
        lambda: _execute_nuclei(target, options),
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
    """Execute nuclei scan (runs in background)."""
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

        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
        )

        return ToolOutput(
            status="success",
            tool="run_nuclei",
            output=f"Nuclei scan started (PID: {proc.pid}). Check results in a few minutes at: {output_file}",
            saved_to=str(output_file),
        )

    except Exception as e:
        return ToolOutput(
            status="error", tool="run_nuclei", output=f"Error: {str(e)}", saved_to=None
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
