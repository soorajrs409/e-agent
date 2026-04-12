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

TOOLS_AUTO = _config.get("tools", {}).get("auto", ["read_file", "call_api", "run_nmap"])
TOOLS_APPROVAL_REQUIRED = _config.get("tools", {}).get(
    "approval_required", ["run_nuclei"]
)

APPROVAL_TIMEOUT_MINUTES = _config.get("approval", {}).get("timeout_minutes", 5)
APPROVAL_ALLOW_APPROVE_ALL = _config.get("approval", {}).get("allow_approve_all", True)

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
