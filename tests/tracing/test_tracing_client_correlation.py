import pytest

import mlflow
from mlflow.store.tracking.dbmodels.models import SqlSpan, SqlTraceInfo, SqlTraceTag
from mlflow.tracing.analysis import TraceFilterCorrelationResult
from mlflow.tracing.client import TracingClient


def test_tracing_client_calculate_trace_filter_correlation(tmp_path):
    """Test TracingClient.calculate_trace_filter_correlation method."""
    # Create a client with a test database
    db_uri = f"sqlite:///{tmp_path}/test.db"
    mlflow.set_tracking_uri(db_uri)
    client = TracingClient(tracking_uri=db_uri)
    store = client.store

    # Create experiment
    exp_id = store.create_experiment("test_correlation")

    # Create traces with patterns directly in the store
    with store.ManagedSessionMaker() as session:
        for i in range(10):
            trace_id = f"tr-test-{i}"

            # Create trace info
            trace_info = SqlTraceInfo(
                request_id=trace_id,
                experiment_id=exp_id,
                timestamp_ms=i * 1000,
                execution_time_ms=100,
                status="OK",
            )
            session.add(trace_info)

            # Add tag
            tag = SqlTraceTag(
                request_id=trace_id,
                key="env",
                value="prod" if i < 6 else "dev",
            )
            session.add(tag)

            # Add span
            span = SqlSpan(
                trace_id=trace_id,
                experiment_id=exp_id,
                span_id=f"sp-{i}",
                parent_span_id=None,
                name="process",
                type="TOOL" if i < 7 else "LLM",
                status="OK",
                start_time_unix_nano=i * 1000000000,
                end_time_unix_nano=(i + 1) * 1000000000,
                content="{}",
            )
            session.add(span)

    # Test correlation between env=prod and TOOL spans
    result = client.calculate_trace_filter_correlation(
        experiment_ids=[exp_id],
        filter_string1="tags.env = 'prod'",
        filter_string2="span.type = 'TOOL'",
    )

    assert isinstance(result, TraceFilterCorrelationResult)
    assert result.total_count == 10
    assert result.filter_string1_count == 6  # prod traces
    assert result.filter_string2_count == 7  # TOOL traces
    assert result.joint_count == 6  # All prod traces have TOOL spans

    # NPMI calculation:
    # P(prod) = 6/10 = 0.6
    # P(TOOL) = 7/10 = 0.7
    # P(prod & TOOL) = 6/10 = 0.6
    # PMI = log2(0.6 / (0.6 * 0.7)) = log2(1.429) ≈ 0.515
    # NPMI = PMI / (-log2(0.6)) ≈ 0.515 / 0.737 ≈ 0.699
    assert 0.6 < result.npmi < 0.8

    # Test with count expression
    result2 = client.calculate_trace_filter_correlation(
        experiment_ids=[exp_id],
        filter_string1="tags.env = 'dev'",
        filter_string2="count(span.type = 'LLM') > 0",
    )

    assert result2.total_count == 10
    assert result2.filter_string1_count == 4  # dev traces (6-9)
    assert result2.filter_string2_count == 3  # traces with LLM spans (7-9)
    assert result2.joint_count == 3  # All LLM traces are in dev

    # Test with invalid filter
    from mlflow.exceptions import MlflowException

    with pytest.raises(MlflowException, match="Invalid"):
        client.calculate_trace_filter_correlation(
            experiment_ids=[exp_id],
            filter_string1="invalid.filter = 'test'",
            filter_string2="span.type = 'TOOL'",
        )
