import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig:
    def test_get_guardrails_config(self):
        from langchain_agent.config import get_guardrails_config

        config = get_guardrails_config()

        assert "max_input_length" in config
        assert "blocked_targets" in config
        assert "nmap_allowed_flags" in config
        assert "rate_limit_enabled" in config

    def test_guardrails_defaults(self):
        from langchain_agent.config import (
            GUARDRAILS_MAX_INPUT_LENGTH,
            GUARDRAILS_BLOCKED_TARGETS,
            GUARDRAILS_NMAP_ALLOWED_FLAGS,
            GUARDRAILS_RATE_LIMIT_ENABLED,
        )

        assert GUARDRAILS_MAX_INPUT_LENGTH == 5000
        assert "127.0.0.1" in GUARDRAILS_BLOCKED_TARGETS
        assert "localhost" in GUARDRAILS_BLOCKED_TARGETS
        assert "-sV" in GUARDRAILS_NMAP_ALLOWED_FLAGS
        assert GUARDRAILS_RATE_LIMIT_ENABLED is True

    def test_get_sandbox_path(self):
        from langchain_agent.config import get_sandbox_path

        path = get_sandbox_path()
        assert isinstance(path, Path)

    def test_tool_category(self):
        from langchain_agent.config import get_tool_category

        assert get_tool_category("read_file") == "auto"
        assert get_tool_category("run_nuclei") == "approval_required"

    def test_is_tool_auto(self):
        from langchain_agent.config import is_tool_auto

        assert is_tool_auto("read_file") is True
        assert is_tool_auto("run_nuclei") is False
