import pytest
import sys
import os
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_agent.approval_queue import (
    ApprovalQueue,
    ApprovalRequest,
    ApprovalStatus,
)


class TestApprovalRequest:
    def test_create_request(self):
        req = ApprovalRequest("run_nmap", {"target": "192.168.1.1"})
        assert req.tool == "run_nmap"
        assert req.args == {"target": "192.168.1.1"}
        assert req.status == ApprovalStatus.PENDING
        assert req.id is not None


class TestApprovalQueue:
    def setup_method(self):
        self.queue = ApprovalQueue()

    def test_add_request(self):
        request_id = self.queue.add_request("run_nmap", {"target": "192.168.1.1"})
        assert request_id is not None
        assert request_id != "auto_approved"

    def test_add_request_auto_approved(self):
        self.queue.approve_all("run_nmap")
        request_id = self.queue.add_request("run_nmap", {"target": "192.168.1.1"})
        assert request_id == "auto_approved"

    def test_approve_valid_request(self):
        request_id = self.queue.add_request("run_nmap", {"target": "192.168.1.1"})
        result = self.queue.approve(request_id)

        assert result["status"] == ApprovalStatus.APPROVED
        assert result["tool"] == "run_nmap"
        assert result["args"] == {"target": "192.168.1.1"}

    def test_approve_not_found(self):
        result = self.queue.approve("invalid-id")
        assert result["status"] == ApprovalStatus.PENDING

    def test_deny_valid_request(self):
        request_id = self.queue.add_request("run_nmap", {"target": "192.168.1.1"})
        result = self.queue.deny(request_id)

        assert result["status"] == ApprovalStatus.DENIED

    def test_deny_not_found(self):
        result = self.queue.deny("invalid-id")
        assert result["status"] == ApprovalStatus.PENDING

    def test_approve_all(self):
        self.queue.approve_all("run_nmap")
        assert self.queue.is_auto_approved("run_nmap") is True

    def test_revoke_approve_all(self):
        self.queue.approve_all("run_nmap")
        self.queue.revoke_approve_all("run_nmap")
        assert self.queue.is_auto_approved("run_nmap") is False

    def test_get_pending(self):
        request_id = self.queue.add_request("run_nmap", {"target": "192.168.1.1"})
        pending = self.queue.get_pending()

        assert request_id in pending
        assert pending[request_id]["tool"] == "run_nmap"

    def test_clear_session(self):
        self.queue.add_request("run_nmap", {"target": "192.168.1.1"})
        self.queue.approve_all("run_nmap")
        self.queue.clear_session()

        assert len(self.queue.get_pending()) == 0
        assert self.queue.is_auto_approved("run_nmap") is False
