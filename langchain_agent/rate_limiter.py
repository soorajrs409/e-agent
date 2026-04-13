from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock


class RateLimiter:
    def __init__(self):
        self._counters: dict[str, list[datetime]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, tool_name: str) -> tuple[bool, str]:
        from langchain_agent.config import (
            GUARDRAILS_RATE_LIMIT_ENABLED,
            GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE,
        )

        if not GUARDRAILS_RATE_LIMIT_ENABLED:
            return True, ""

        with self._lock:
            now = datetime.now()
            window_start = now - timedelta(minutes=1)

            self._counters[tool_name] = [
                ts for ts in self._counters[tool_name] if ts > window_start
            ]

            if len(self._counters[tool_name]) >= GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE:
                return (
                    False,
                    f"Rate limit exceeded for {tool_name}. Max {GUARDRAILS_RATE_LIMIT_MAX_PER_MINUTE} per minute.",
                )

            self._counters[tool_name].append(now)
            return True, ""

    def reset(self, tool_name: str = None):
        with self._lock:
            if tool_name:
                self._counters[tool_name].clear()
            else:
                self._counters.clear()


_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
