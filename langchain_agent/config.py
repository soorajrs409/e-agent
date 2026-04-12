import yaml
from pathlib import Path

CONFIG_FILE = "config.yaml"


def load_config():
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}


_config = load_config()

MODEL_NAME = _config.get("model", {}).get("name", "llama3.1")
OLLAMA_HOST = _config.get("model", {}).get("ollama_host", "http://127.0.0.1:11434")
AGENT_NAME = _config.get("agent", {}).get("name", "electron-agent")
LOG_FILE = _config.get("agent", {}).get("log_file", "logs/agent.log")

SANDBOX_PATH = _config.get("sandbox", {}).get("path", "./sandbox")
SANDBOX_DIRS = _config.get("sandbox", {}).get(
    "directories", ["scans", "downloads", "temp"]
)

TOOLS_AUTO = _config.get("tools", {}).get("auto", ["read_file", "call_api"])
TOOLS_APPROVAL_REQUIRED = _config.get("tools", {}).get(
    "approval_required", ["run_nuclei"]
)

APPROVAL_TIMEOUT_MINUTES = _config.get("approval", {}).get("timeout_minutes", 5)
APPROVAL_ALLOW_APPROVE_ALL = _config.get("approval", {}).get("allow_approve_all", True)

TOOL_CALL_API_TIMEOUT = _config.get("tools", {}).get("call_api", {}).get("timeout", 20)
TOOL_NMAP_TIMEOUT = _config.get("tools", {}).get("nmap", {}).get("timeout", 600)
TOOL_NUCLEI_TIMEOUT = _config.get("tools", {}).get("nuclei", {}).get("timeout", 600)

LOG_ROTATION_DAYS = _config.get("logging", {}).get("rotation_days", 7)
LOG_BACKUP_COUNT = _config.get("logging", {}).get("backup_count", 7)

GUARDRAILS_MAX_INPUT_LENGTH = _config.get("guardrails", {}).get(
    "max_input_length", 5000
)
GUARDRAILS_BLOCKED_TARGETS = _config.get("guardrails", {}).get(
    "blocked_targets", ["127.0.0.1", "localhost", "169.254.169.254"]
)
GUARDRAILS_NMAP_ALLOWED_FLAGS = (
    _config.get("guardrails", {})
    .get("nmap", {})
    .get("allowed_flags", ["-sV", "-sS", "-Pn", "-F", "-O"])
)
GUARDRAILS_RATE_LIMIT_ENABLED = (
    _config.get("guardrails", {}).get("rate_limit", {}).get("enabled", True)
)
GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE = (
    _config.get("guardrails", {}).get("rate_limit", {}).get("max_per_minute", 30)
)


def get_sandbox_path():
    return Path(SANDBOX_PATH).resolve()


def get_tool_category(tool_name: str) -> str:
    if tool_name in TOOLS_AUTO:
        return "auto"
    if tool_name in TOOLS_APPROVAL_REQUIRED:
        return "approval_required"
    return "auto"


def is_tool_auto(tool_name: str) -> bool:
    return get_tool_category(tool_name) == "auto"


def get_guardrails_config() -> dict:
    return {
        "max_input_length": GUARDRAILS_MAX_INPUT_LENGTH,
        "blocked_targets": GUARDRAILS_BLOCKED_TARGETS,
        "nmap_allowed_flags": GUARDRAILS_NMAP_ALLOWED_FLAGS,
        "rate_limit_enabled": GUARDRAILS_RATE_LIMIT_ENABLED,
        "rate_limit_max_per_minute": GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE,
    }


def get_tool_timeouts() -> dict:
    return {
        "call_api": TOOL_CALL_API_TIMEOUT,
        "nmap": TOOL_NMAP_TIMEOUT,
        "nuclei": TOOL_NUCLEI_TIMEOUT,
    }


def get_logging_config() -> dict:
    return {
        "rotation_days": LOG_ROTATION_DAYS,
        "backup_count": LOG_BACKUP_COUNT,
    }
