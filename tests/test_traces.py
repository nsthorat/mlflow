"""Tests for mlflow.traces CLI module."""

import json
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from mlflow.traces import commands


@pytest.fixture
def runner():
    """Provide a CLI runner for tests."""
    return CliRunner()


@pytest.fixture
def mock_trace():
    """Create a mock trace object."""
    trace = Mock()
    trace.info.request_id = "test-request-123"
    trace.info.experiment_id = "1"
    trace.info.timestamp_ms = 1609459200000
    trace.info.status = "OK"
    trace.info.execution_time_ms = 1500
    trace.data = Mock()
    trace.data.request = {"name": "test_request", "input": "test"}
    trace.data.response = {"output": "result"}
    trace.to_dict = Mock(return_value={
        "info": {
            "request_id": "test-request-123",
            "experiment_id": "1",
            "timestamp_ms": 1609459200000
        },
        "data": {
            "request": {"name": "test_request", "input": "test"},
            "response": {"output": "result"}
        }
    })
    return trace


def test_traces_help_command(runner):
    """Test that the main traces command shows help."""
    result = runner.invoke(commands, ["--help"])
    assert result.exit_code == 0
    assert "Manage traces" in result.output
    assert "search" in result.output
    assert "get" in result.output
    assert "delete" in result.output
    assert "log-feedback" in result.output


def test_search_traces_help(runner):
    """Test that the search subcommand shows help."""
    result = runner.invoke(commands, ["search", "--help"])
    assert result.exit_code == 0
    assert "Search for traces" in result.output
    assert "--experiment-id" in result.output
    assert "--limit" in result.output
    assert "--filter" in result.output


@patch("mlflow.traces.MlflowClient")
def test_search_traces_basic(mock_client_class, runner, mock_trace):
    """Test basic trace search."""
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.search_traces.return_value = [mock_trace]
    
    result = runner.invoke(commands, ["search", "--experiment-id", "1"])
    assert result.exit_code == 0
    assert "test-request-123" in result.output
    mock_client.search_traces.assert_called_once()


@patch("mlflow.traces.MlflowClient")
def test_search_traces_json_format(mock_client_class, runner, mock_trace):
    """Test trace search with JSON output."""
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.search_traces.return_value = [mock_trace]
    
    result = runner.invoke(commands, ["search", "--experiment-id", "1", "--json"])
    assert result.exit_code == 0
    # Should contain valid JSON
    output_data = json.loads(result.output)
    assert len(output_data) == 1
    assert output_data[0]["info"]["request_id"] == "test-request-123"


@patch("mlflow.traces.MlflowClient")
def test_get_trace(mock_client_class, runner, mock_trace):
    """Test getting a specific trace."""
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.get_trace.return_value = mock_trace
    
    result = runner.invoke(commands, ["get", "test-request-123"])
    assert result.exit_code == 0
    assert "Request ID: test-request-123" in result.output
    assert "Experiment ID: 1" in result.output
    mock_client.get_trace.assert_called_once_with("test-request-123")


@patch("mlflow.traces.MlflowClient")
def test_get_trace_json_format(mock_client_class, runner, mock_trace):
    """Test getting a trace with JSON output."""
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.get_trace.return_value = mock_trace
    
    result = runner.invoke(commands, ["get", "test-request-123", "--json"])
    assert result.exit_code == 0
    output_data = json.loads(result.output)
    assert output_data["info"]["request_id"] == "test-request-123"


@patch("mlflow.traces.MlflowClient")
def test_delete_trace(mock_client_class, runner):
    """Test deleting a trace."""
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    
    result = runner.invoke(commands, ["delete", "test-request-123"])
    assert result.exit_code == 0
    assert "Trace test-request-123 has been deleted" in result.output
    mock_client.delete_trace.assert_called_once_with("test-request-123")


@patch("mlflow.traces.MlflowClient")
def test_log_feedback(mock_client_class, runner):
    """Test logging feedback for a trace."""
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    
    result = runner.invoke(commands, [
        "log-feedback", "test-request-123", 
        "--score", "0.8", 
        "--comment", "Good result"
    ])
    assert result.exit_code == 0
    assert "Feedback logged for trace test-request-123" in result.output
    # Should have called set_trace_tag for both score and comment
    assert mock_client.set_trace_tag.call_count == 2


def test_log_feedback_no_args(runner):
    """Test that log-feedback requires at least one argument."""
    result = runner.invoke(commands, ["log-feedback", "test-request-123"])
    assert result.exit_code == 1
    assert "At least one of --score, --comment, or --tags must be provided" in result.output