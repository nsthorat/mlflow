import json
from unittest import mock

from click.testing import CliRunner

from mlflow.traces_cli import commands
from mlflow.entities import AssessmentSourceType

# Table cell formatting tests are in tests/utils/test_string_utils.py


class TestTracesCommands:
    """Test suite for mlflow traces CLI commands."""

    def test_commands_group_exists(self):
        """Test that the traces command group is properly defined."""
        assert commands.name == "traces"
        assert commands.help is not None

    def test_search_command_params(self):
        """Test that search command has all required parameters."""
        search_cmd = None
        for cmd in commands.commands.values():
            if cmd.name == "search":
                search_cmd = cmd
                break

        assert search_cmd is not None
        param_names = [p.name for p in search_cmd.params]

        # Check for required parameters
        assert "experiment_id" in param_names
        assert "extract_fields" in param_names
        assert "output" in param_names
        assert "max_results" in param_names

    def test_get_command_params(self):
        """Test that get command has all required parameters."""
        get_cmd = None
        for cmd in commands.commands.values():
            if cmd.name == "get":
                get_cmd = cmd
                break

        assert get_cmd is not None
        param_names = [p.name for p in get_cmd.params]

        # Check for required parameters
        assert "trace_id" in param_names
        assert "extract_fields" in param_names

    def test_assessment_source_type_choices(self):
        """Test that assessment commands use dynamic enum values."""
        feedback_cmd = None
        expectation_cmd = None

        for cmd in commands.commands.values():
            if cmd.name == "log-feedback":
                feedback_cmd = cmd
            elif cmd.name == "log-expectation":
                expectation_cmd = cmd

        assert feedback_cmd is not None
        assert expectation_cmd is not None

        # Find source-type parameter
        feedback_source_param = None
        expectation_source_param = None

        for param in feedback_cmd.params:
            if param.name == "source_type":
                feedback_source_param = param
                break

        for param in expectation_cmd.params:
            if param.name == "source_type":
                expectation_source_param = param
                break

        assert feedback_source_param is not None
        assert expectation_source_param is not None

        # Check that choices include the enum values
        expected_choices = (
            AssessmentSourceType.HUMAN,
            AssessmentSourceType.LLM_JUDGE,
            AssessmentSourceType.CODE,
        )

        assert feedback_source_param.type.choices == expected_choices
        assert expectation_source_param.type.choices == expected_choices

    @mock.patch("mlflow.cli.traces.validate_field_paths")
    @mock.patch("mlflow.cli.traces.TracingClient")
    def test_search_command_with_fields(self, mock_client, mock_validate):
        """Test search command with field selection."""
        # Mock the client and response
        mock_trace = mock.MagicMock()
        mock_trace.to_dict.return_value = {
            "info": {"trace_id": "tr-123", "state": "OK", "execution_duration_ms": 1500}
        }
        mock_traces = mock.MagicMock()
        mock_traces.__iter__.return_value = [mock_trace]
        mock_traces.token = None
        mock_client.return_value.search_traces.return_value = mock_traces

        # Mock field validation to pass
        mock_validate.return_value = None

        runner = CliRunner()
        result = runner.invoke(
            commands,
            [
                "search",
                "--experiment-id",
                "1",
                "--extract-fields",
                "info.trace_id,info.state",
                "--max-results",
                "1",
            ],
        )

        assert result.exit_code == 0
        assert "tr-123" in result.output
        assert "OK" in result.output

    @mock.patch("mlflow.cli.traces.validate_field_paths")
    @mock.patch("mlflow.cli.traces.TracingClient")
    def test_get_command_with_fields(self, mock_client, mock_validate):
        """Test get command with field selection."""
        # Mock the client and response
        mock_trace = mock.MagicMock()
        mock_trace.to_dict.return_value = {
            "info": {"trace_id": "tr-123", "state": "OK"},
            "data": {"spans": [{"name": "test_span"}]},
        }
        mock_client.return_value.get_trace.return_value = mock_trace

        # Mock field validation to pass
        mock_validate.return_value = None

        runner = CliRunner()
        result = runner.invoke(
            commands,
            [
                "get",
                "--trace-id",
                "tr-123",
                "--extract-fields",
                "info.trace_id,data.spans.*.name",
            ],
        )

        assert result.exit_code == 0
        output_json = json.loads(result.output)
        assert "info" in output_json
        assert output_json["info"]["trace_id"] == "tr-123"
        assert "data" in output_json
        assert len(output_json["data"]["spans"]) == 1
        assert output_json["data"]["spans"][0]["name"] == "test_span"

    @mock.patch("mlflow.cli.traces.TracingClient")
    def test_delete_command(self, mock_client):
        """Test delete command."""
        mock_client.return_value.delete_traces.return_value = 5

        runner = CliRunner()
        result = runner.invoke(
            commands, ["delete", "--experiment-id", "1", "--trace-ids", "tr-123,tr-456"]
        )

        assert result.exit_code == 0
        assert "Deleted 5 trace(s)" in result.output
        mock_client.return_value.delete_traces.assert_called_once()

    def test_field_validation_error(self):
        """Test that invalid fields produce helpful error messages."""
        runner = CliRunner()

        with mock.patch("mlflow.cli.traces.TracingClient") as mock_client:
            mock_trace = mock.MagicMock()
            mock_trace.to_dict.return_value = {"info": {"trace_id": "tr-123"}}
            mock_traces = mock.MagicMock()
            mock_traces.__iter__.return_value = [mock_trace]
            mock_client.return_value.search_traces.return_value = mock_traces

            # Mock validate_field_paths to raise an exception
            with mock.patch("mlflow.cli.traces.validate_field_paths") as mock_validate:
                from click import UsageError

                mock_validate.side_effect = UsageError("Invalid field: info.nonexistent")

                result = runner.invoke(
                    commands,
                    [
                        "search",
                        "--experiment-id",
                        "1",
                        "--extract-fields",
                        "info.nonexistent",
                    ],
                )

                assert result.exit_code != 0
                assert "Invalid field: info.nonexistent" in result.output
