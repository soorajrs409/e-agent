import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_agent.tools import ToolOutput


class TestToolOutput:
    def test_tool_output_model(self):
        output = ToolOutput(
            status="success",
            tool="test",
            output="test output",
            saved_to=None,
        )
        assert output.status == "success"
        assert output.tool == "test"
        assert output.output == "test output"

    def test_tool_output_with_save_path(self):
        output = ToolOutput(
            status="success",
            tool="read_file",
            output="content",
            saved_to="/path/to/file",
        )
        assert output.saved_to == "/path/to/file"

    def test_tool_output_error(self):
        output = ToolOutput(
            status="error",
            tool="run_nmap",
            output="Nmap error: Some error",
            saved_to=None,
        )
        assert output.status == "error"


class TestReadFile:
    @patch("langchain_agent.tools.get_sandbox_path")
    @patch("pathlib.Path.resolve")
    def test_read_file_success(self, mock_resolve, mock_sandbox):
        from langchain_agent.tools import read_file

        mock_sandbox.return_value = Path("/sandbox")
        mock_resolve.return_value = Path("/sandbox/test.txt")

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value="test content"):
                result = read_file.invoke({"file_path": "test.txt"})

        assert result.status == "success"
        assert result.tool == "read_file"

    @patch("langchain_agent.tools.get_sandbox_path")
    def test_read_file_outside_sandbox(self, mock_sandbox):
        from langchain_agent.tools import read_file

        mock_sandbox.return_value = Path("/sandbox")

        result = read_file.invoke({"file_path": "/etc/passwd"})

        assert result.status == "blocked"
        assert "Access denied" in result.output

    @patch("langchain_agent.tools.get_sandbox_path")
    @patch("pathlib.Path.resolve")
    def test_read_file_not_found(self, mock_resolve, mock_sandbox):
        from langchain_agent.tools import read_file

        mock_sandbox.return_value = Path("/sandbox")
        mock_resolve.return_value = Path("/sandbox/missing.txt")

        with patch("pathlib.Path.exists", return_value=False):
            result = read_file.invoke({"file_path": "missing.txt"})

        assert result.status == "error"
        assert "not found" in result.output


class TestCallApi:
    def test_call_api_invalid_scheme(self):
        from langchain_agent.tools import call_api

        result = call_api.invoke({"url": "ftp://example.com"})

        assert result.status == "blocked"
        assert "http" in result.output.lower()

    def test_call_api_blocked_internal(self):
        from langchain_agent.tools import call_api

        result = call_api.invoke({"url": "http://localhost/test"})

        assert result.status == "blocked"
        assert "not allowed" in result.output.lower()
