import uuid
from datetime import datetime, timedelta
from enum import Enum


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class ApprovalRequest:
    def __init__(self, tool: str, args: dict, chain_state: dict = None):
        self.id = str(uuid.uuid4())[:8]
        self.tool = tool
        self.args = args
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(minutes=5)
        self.status = ApprovalStatus.PENDING
        self.chain_state = chain_state or {}

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


_global_queue = None


def get_approval_queue() -> "ApprovalQueue":
    global _global_queue
    if _global_queue is None:
        _global_queue = ApprovalQueue()
    return _global_queue


class ApprovalQueue:
    def __init__(self):
        self._queue: dict[str, ApprovalRequest] = {}
        self._auto_approved_tools: set[str] = set()

    def add_request(self, tool: str, args: dict, chain_state: dict = None) -> str:
        if tool in self._auto_approved_tools:
            return "auto_approved"

        request = ApprovalRequest(tool, args, chain_state)
        self._queue[request.id] = request
        return request.id

    def approve(self, request_id: str) -> dict:
        request = self._queue.get(request_id)

        if not request:
            return {"status": ApprovalStatus.PENDING, "reason": "not_found"}

        if request.is_expired():
            del self._queue[request_id]
            return {"status": ApprovalStatus.EXPIRED, "reason": "expired"}

        tool = request.tool
        args = request.args
        chain_state = request.chain_state

        del self._queue[request_id]

        return {
            "status": ApprovalStatus.APPROVED,
            "tool": tool,
            "args": args,
            "chain_state": chain_state,
        }

    def get_request(self, request_id: str) -> dict | None:
        request = self._queue.get(request_id)
        if not request:
            return None

        return {
            "id": request.id,
            "tool": request.tool,
            "args": request.args,
            "chain_state": request.chain_state,
            "created_at": request.created_at.isoformat(),
            "expires_at": request.expires_at.isoformat(),
            "status": request.status.value,
        }

    def deny(self, request_id: str) -> dict:
        request = self._queue.get(request_id)

        if not request:
            return {"status": ApprovalStatus.PENDING, "reason": "not_found"}

        if request.is_expired():
            del self._queue[request_id]
            return {"status": ApprovalStatus.EXPIRED, "reason": "expired"}

        del self._queue[request_id]

        return {"status": ApprovalStatus.DENIED}

    def approve_all(self, tool: str):
        self._auto_approved_tools.add(tool)

    def revoke_approve_all(self, tool: str):
        self._auto_approved_tools.discard(tool)

    def is_auto_approved(self, tool: str) -> bool:
        return tool in self._auto_approved_tools

    def cleanup_expired(self):
        expired_ids = [
            req_id for req_id, req in self._queue.items() if req.is_expired()
        ]
        for req_id in expired_ids:
            del self._queue[req_id]

    def get_pending(self) -> dict:
        self.cleanup_expired()
        return {
            req_id: {
                "tool": req.tool,
                "created_at": req.created_at.isoformat(),
                "expires_at": req.expires_at.isoformat(),
            }
            for req_id, req in self._queue.items()
        }

    def clear_session(self):
        self._queue.clear()
        self._auto_approved_tools.clear()
