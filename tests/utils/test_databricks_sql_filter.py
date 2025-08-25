"""
Unit tests for Databricks SQL filter DSL parser.
"""

import pytest

from mlflow.exceptions import MlflowException
from mlflow.utils.databricks_sql_filter import FilterOperator, TraceFilterParser


class TestTraceFilterParser:
    """Test the TraceFilterParser for converting MLflow filter DSL to SQL."""

    def test_parse_empty_filter(self):
        """Test parsing empty or None filter string."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse(None)
        assert conditions == []
        assert params == {}
        
        conditions, params = parser.parse("")
        assert conditions == []
        assert params == {}
        
        conditions, params = parser.parse("  ")
        assert conditions == []
        assert params == {}

    def test_parse_simple_status_filter(self):
        """Test parsing simple status equality filter."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("status = 'OK'")
        assert len(conditions) == 1
        assert "state" in conditions[0]  # status maps to state column
        assert "param_0" in params
        assert params["param_0"] == "OK"

    def test_parse_numeric_comparison_filters(self):
        """Test parsing numeric comparison operators."""
        parser = TraceFilterParser("test_table")
        
        # Greater than
        conditions, params = parser.parse("execution_time > 1000")
        assert len(conditions) == 1
        assert "execution_duration_ms >" in conditions[0]
        assert any(params[k] == 1000 for k in params)
        
        # Less than or equal
        parser = TraceFilterParser("test_table")
        conditions, params = parser.parse("timestamp_ms <= 1640995200000")
        assert len(conditions) == 1
        assert "request_time <=" in conditions[0]
        assert any(params[k] == 1640995200000 for k in params)

    def test_parse_string_like_filter(self):
        """Test parsing LIKE operator for strings."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("name LIKE '%test%'")
        assert len(conditions) == 1
        assert "mlflow.traceName" in conditions[0]  # name maps to tag
        assert any(params[k] == "%test%" for k in params)

    def test_parse_in_operator(self):
        """Test parsing IN operator with multiple values."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("status IN ('OK', 'ERROR')")
        assert len(conditions) == 1
        assert "state IN" in conditions[0]
        # Should have two parameters for the two values
        assert len([v for v in params.values() if v in ["OK", "ERROR"]]) == 2

    def test_parse_not_in_operator(self):
        """Test parsing NOT IN operator."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("status NOT IN ('PENDING')")
        assert len(conditions) == 1
        assert "state NOT IN" in conditions[0]
        assert any(params[k] == "PENDING" for k in params)

    def test_parse_compound_filter_with_and(self):
        """Test parsing compound filter with AND."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("status = 'OK' AND execution_time > 1000")
        assert len(conditions) == 2
        # Check both conditions are present
        status_condition = [c for c in conditions if "state" in c][0]
        time_condition = [c for c in conditions if "execution_duration_ms" in c][0]
        assert status_condition
        assert time_condition
        # Check parameters
        assert any(params[k] == "OK" for k in params)
        assert any(params[k] == 1000 for k in params)

    def test_parse_tag_filter(self):
        """Test parsing tag filters with tags. prefix."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("tags.environment = 'production'")
        assert len(conditions) == 1
        assert "tags['environment']" in conditions[0]
        assert any(params[k] == "production" for k in params)

    def test_parse_metadata_filter(self):
        """Test parsing metadata filters."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("metadata.source = 'api'")
        assert len(conditions) == 1
        assert "trace_metadata['source']" in conditions[0]
        assert any(params[k] == "api" for k in params)

    def test_parse_run_id_filter(self):
        """Test parsing run_id which maps to metadata."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("run_id = 'abc123'")
        assert len(conditions) == 1
        assert "mlflow.sourceRun" in conditions[0]
        assert any(params[k] == "abc123" for k in params)

    def test_parse_feedback_filter(self):
        """Test parsing feedback filters."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("feedback.score > 0.8")
        assert len(conditions) == 1
        assert "feedback.score" in conditions[0]
        assert any(params[k] == 0.8 for k in params)

    def test_parse_span_filter(self):
        """Test parsing span filters."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("span.type = 'LLM'")
        assert len(conditions) == 1
        assert "span_type" in conditions[0]
        assert any(params[k] == "LLM" for k in params)

    def test_parse_span_content_like(self):
        """Test parsing span.content with LIKE (only supported operator)."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("span.content LIKE '%error%'")
        assert len(conditions) == 1
        assert "span_content" in conditions[0]
        assert "LIKE" in conditions[0]
        assert any(params[k] == "%error%" for k in params)

    def test_parse_count_expression(self):
        """Test parsing count expressions."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("count(span.type = 'LLM') > 2")
        assert len(conditions) == 1
        assert "COUNT" in conditions[0]
        # Should have parameters for both inner condition and count value
        assert any(params[k] == "LLM" for k in params)
        assert any(params[k] == 2 for k in params)

    def test_parse_boolean_values(self):
        """Test parsing boolean values in filters."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("feedback.is_correct = true")
        assert len(conditions) == 1
        assert any(params[k] is True for k in params)
        
        parser = TraceFilterParser("test_table")
        conditions, params = parser.parse("feedback.is_correct = false")
        assert len(conditions) == 1
        assert any(params[k] is False for k in params)

    def test_parse_quoted_field_names(self):
        """Test parsing field names with backticks."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("`status` = 'OK'")
        assert len(conditions) == 1
        assert "state" in conditions[0]
        assert any(params[k] == "OK" for k in params)

    def test_parse_case_insensitive_operators(self):
        """Test that operators are case-insensitive."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse("name like '%test%'")
        assert len(conditions) == 1
        assert "LIKE" in conditions[0] or "like" in conditions[0].lower()
        
        parser = TraceFilterParser("test_table")
        conditions, params = parser.parse("status in ('OK', 'ERROR')")
        assert len(conditions) == 1
        assert "IN" in conditions[0] or "in" in conditions[0].lower()

    def test_parse_complex_compound_filter(self):
        """Test parsing complex filter with multiple conditions."""
        parser = TraceFilterParser("test_table")
        
        filter_str = "status = 'OK' AND name LIKE '%test%' AND execution_time > 1000 AND tags.env = 'prod'"
        conditions, params = parser.parse(filter_str)
        
        assert len(conditions) == 4
        # Verify all condition types are present
        assert any("state" in c for c in conditions)
        assert any("mlflow.traceName" in c for c in conditions)
        assert any("execution_duration_ms" in c for c in conditions)
        assert any("tags['env']" in c for c in conditions)

    def test_invalid_filter_raises_exception(self):
        """Test that invalid filter syntax raises MlflowException."""
        parser = TraceFilterParser("test_table")
        
        # Invalid operator for field
        with pytest.raises(MlflowException) as exc_info:
            parser.parse("invalid syntax here")
        assert "Invalid filter condition" in str(exc_info.value)
        
        # Invalid span field
        with pytest.raises(MlflowException) as exc_info:
            parser.parse("span.invalid_field = 'value'")
        assert "Invalid span field" in str(exc_info.value)
        
        # Invalid operator for span.content
        with pytest.raises(MlflowException) as exc_info:
            parser.parse("span.content = 'exact'")
        assert "span.content only supports LIKE/ILIKE" in str(exc_info.value)

    def test_numeric_operator_validation(self):
        """Test that numeric fields only accept numeric operators."""
        parser = TraceFilterParser("test_table")
        
        # Valid numeric operator
        conditions, params = parser.parse("timestamp_ms >= 1000")
        assert len(conditions) == 1
        
        # Invalid string operator for numeric field
        with pytest.raises(MlflowException) as exc_info:
            parser.parse("timestamp_ms LIKE '1000'")
        assert "Invalid operator" in str(exc_info.value)

    def test_tag_operator_validation(self):
        """Test that tag fields only accept limited operators."""
        parser = TraceFilterParser("test_table")
        
        # Valid tag operator
        conditions, params = parser.parse("tags.env = 'prod'")
        assert len(conditions) == 1
        
        # Invalid LIKE operator for tags (not supported for performance)
        with pytest.raises(MlflowException) as exc_info:
            parser.parse("tags.env LIKE '%prod%'")
        assert "not supported for tags" in str(exc_info.value)

    def test_parameter_name_uniqueness(self):
        """Test that parameter names are unique across conditions."""
        parser = TraceFilterParser("test_table")
        
        conditions, params = parser.parse(
            "status = 'OK' AND status != 'ERROR' AND execution_time > 1000"
        )
        
        # All parameter names should be unique
        param_names = list(params.keys())
        assert len(param_names) == len(set(param_names))
        
        # Should have correct number of parameters
        assert len(params) == 3

    def test_value_type_inference(self):
        """Test correct type inference for values."""
        parser = TraceFilterParser("test_table")
        
        # Integer
        conditions, params = parser.parse("execution_time = 42")
        assert any(isinstance(params[k], int) and params[k] == 42 for k in params)
        
        # Float
        conditions, params = parser.parse("feedback.score = 3.14")
        assert any(isinstance(params[k], float) and params[k] == 3.14 for k in params)
        
        # String with quotes
        conditions, params = parser.parse("name = 'test'")
        assert any(isinstance(params[k], str) and params[k] == "test" for k in params)
        
        # Boolean
        conditions, params = parser.parse("feedback.enabled = true")
        assert any(isinstance(params[k], bool) and params[k] is True for k in params)

    def test_field_alias_mapping(self):
        """Test that field aliases are correctly mapped."""
        parser = TraceFilterParser("test_table")
        
        # timestamp -> timestamp_ms
        conditions, params = parser.parse("timestamp > 1000")
        assert "request_time" in conditions[0]
        
        # execution_time -> execution_time_ms
        conditions, params = parser.parse("execution_time < 5000")
        assert "execution_duration_ms" in conditions[0]

    def test_split_by_and_respects_quotes(self):
        """Test that AND splitting respects quoted strings."""
        parser = TraceFilterParser("test_table")
        
        # AND inside quotes should not split
        conditions, params = parser.parse("name = 'test AND more' AND status = 'OK'")
        assert len(conditions) == 2
        assert any(params[k] == "test AND more" for k in params)
        assert any(params[k] == "OK" for k in params)

    def test_split_by_and_respects_parentheses(self):
        """Test that AND splitting respects parentheses."""
        parser = TraceFilterParser("test_table")
        
        # This is a simplified test - full implementation would need proper grouping
        conditions, params = parser.parse("status IN ('OK', 'ERROR') AND name = 'test'")
        assert len(conditions) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])