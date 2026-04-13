import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_agent.rate_limiter import RateLimiter, get_rate_limiter


class TestRateLimiter:
    def test_rate_limiter_allows_under_limit(self):
        limiter = RateLimiter()

        for i in range(5):
            allowed, reason = limiter.is_allowed("test_tool")
            assert allowed is True
            assert reason == ""

    def test_rate_limiter_blocks_over_limit(self):
        limiter = RateLimiter()

        import langchain_agent.config as config

        original_limit = config.GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE

        config.GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE = 2

        try:
            limiter.is_allowed("test_tool")
            limiter.is_allowed("test_tool")
            allowed, reason = limiter.is_allowed("test_tool")

            assert allowed is False
            assert "exceeded" in reason.lower()
        finally:
            config.GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE = original_limit

    def test_rate_limiter_per_tool(self):
        import langchain_agent.config as config

        limiter = RateLimiter()
        original_limit = config.GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE

        config.GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE = 2

        try:
            limiter.is_allowed("tool_a")
            limiter.is_allowed("tool_a")

            allowed_a, _ = limiter.is_allowed("tool_a")
            allowed_b, _ = limiter.is_allowed("tool_b")

            assert allowed_a is False
            assert allowed_b is True
        finally:
            config.GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE = original_limit

    def test_rate_limiter_reset(self):
        limiter = RateLimiter()

        import langchain_agent.config as config

        original_limit = config.GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE

        config.GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE = 2

        try:
            limiter.is_allowed("test_tool")
            limiter.is_allowed("test_tool")

            limiter.reset("test_tool")

            allowed, reason = limiter.is_allowed("test_tool")
            assert allowed is True
        finally:
            config.GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE = original_limit

    def test_get_rate_limiter_singleton(self):
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2

    def test_rate_limiter_disabled(self):
        limiter = RateLimiter()

        import langchain_agent.config as config

        original_enabled = config.GUARDRAILS_RATE_LIMIT_ENABLED

        config.GUARDRAILS_RATE_LIMIT_ENABLED = False

        try:
            allowed, reason = limiter.is_allowed("test_tool")
            assert allowed is True
        finally:
            config.GUARDRAILS_RATE_LIMIT_ENABLED = original_enabled
