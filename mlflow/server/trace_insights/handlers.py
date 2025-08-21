"""MLflow Trace Insights - REST API Handlers

High-resolution handlers for trace insights endpoints.
These handlers are imported and registered in the main handlers.py file.
"""

from typing import List, Optional
from flask import jsonify, request
from mlflow.server.handlers import (
    _get_tracking_store,
    catch_mlflow_exception,
    _disable_if_artifacts_only,
)
from mlflow.server.trace_insights.traffic import (
    get_volume_over_time,
    get_latency_percentiles_over_time,
    get_error_rate_over_time,
    get_error_correlations_with_npmi,
)
from mlflow.server.trace_insights.quality import (
    get_token_usage_over_time,
    get_feedback_sentiment_over_time,
    get_quality_scores_over_time,
    get_model_performance_by_version,
)
from mlflow.server.trace_insights.tools import (
    get_precision_recall_over_time,
    get_document_usage_over_time,
    get_retrieval_latency_over_time,
    get_top_retrieved_documents,
    get_tool_discovery,
    get_tool_volume_over_time,
    get_tool_latency_over_time,
    get_tool_error_rate_over_time,
    ToolDiscoveryResponse,
    ToolVolumeOverTimeResponse,
    ToolLatencyOverTimeResponse,
    ToolErrorRateOverTimeResponse,
)
from mlflow.server.trace_insights.models import (
    VolumeOverTimeResponse,
    LatencyPercentilesOverTimeResponse,
    ErrorRateOverTimeResponse,
    ErrorCorrelationsNPMIResponse,
    TokenCostByModelResponse,
)
from mlflow.server.trace_insights.quality import (
    TokenUsageOverTimeResponse,
    FeedbackSentimentOverTimeResponse,
    QualityScoresOverTimeResponse,
    ModelPerformanceByVersionResponse,
)
from mlflow.server.trace_insights.tools import (
    PrecisionRecallOverTimeResponse,
    DocumentUsageOverTimeResponse,
    RetrievalLatencyOverTimeResponse,
    TopRetrievedDocumentsResponse,
)


# Traffic Analytics Handlers

@catch_mlflow_exception
@_disable_if_artifacts_only
def get_volume_over_time_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/volume-over-time`
    Returns trace volume over time with bucketing.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    time_bucket: str = data.get('time_bucket', 'hour')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    volume_points = get_volume_over_time(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time,
        time_bucket=time_bucket
    )
    
    response = VolumeOverTimeResponse(volume_over_time=volume_points)
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_latency_percentiles_over_time_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/latency-percentiles-over-time`
    Returns latency percentiles (P50, P90, P99) over time.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    time_bucket: str = data.get('time_bucket', 'hour')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    latency_points = get_latency_percentiles_over_time(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time,
        time_bucket=time_bucket
    )
    
    response = LatencyPercentilesOverTimeResponse(latency_percentiles_over_time=latency_points)
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_error_rate_over_time_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/error-rate-over-time`
    Returns error rate percentage over time.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    time_bucket: str = data.get('time_bucket', 'hour')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    error_points = get_error_rate_over_time(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time,
        time_bucket=time_bucket
    )
    
    response = ErrorRateOverTimeResponse(error_rate_over_time=error_points)
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_error_correlations_npmi_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/error-correlations-npmi`
    Returns NPMI correlations between errors and trace dimensions.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    min_occurrences: int = data.get('min_occurrences', 5)
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    correlation_points = get_error_correlations_with_npmi(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time,
        min_occurrences=min_occurrences
    )
    
    response = ErrorCorrelationsNPMIResponse(error_correlations=correlation_points)
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_token_cost_by_model_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/token-cost-by-model`
    Returns token usage and cost grouped by model.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    # Placeholder - will be implemented with actual cost calculation
    response = TokenCostByModelResponse(token_cost_by_model=[])
    return jsonify(response.model_dump())


# Quality Analytics Handlers

@catch_mlflow_exception
@_disable_if_artifacts_only
def get_token_usage_over_time_handler():
    """
    Handler for `POST /ajax-api/2.0/mlflow/traces/insights/token-usage-over-time`
    Returns token usage metrics over time with bucketing.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    time_bucket: str = data.get('time_bucket', 'hour')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    token_usage_points = get_token_usage_over_time(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time,
        time_bucket=time_bucket
    )
    
    response = TokenUsageOverTimeResponse(token_usage_over_time=token_usage_points)
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_feedback_sentiment_over_time_handler():
    """
    Handler for `POST /ajax-api/2.0/mlflow/traces/insights/feedback-sentiment-over-time`
    Returns feedback sentiment analysis over time with bucketing.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    time_bucket: str = data.get('time_bucket', 'hour')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    sentiment_points = get_feedback_sentiment_over_time(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time,
        time_bucket=time_bucket
    )
    
    response = FeedbackSentimentOverTimeResponse(feedback_sentiment_over_time=sentiment_points)
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_quality_scores_over_time_handler():
    """
    Handler for `POST /ajax-api/2.0/mlflow/traces/insights/quality-scores-over-time`
    Returns quality scores over time with bucketing.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    time_bucket: str = data.get('time_bucket', 'hour')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    quality_points = get_quality_scores_over_time(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time,
        time_bucket=time_bucket
    )
    
    response = QualityScoresOverTimeResponse(quality_scores_over_time=quality_points)
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_model_performance_by_version_handler():
    """
    Handler for `POST /ajax-api/2.0/mlflow/traces/insights/model-performance-by-version`
    Returns model performance metrics grouped by version.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    performance_points = get_model_performance_by_version(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time
    )
    
    response = ModelPerformanceByVersionResponse(model_performance_by_version=performance_points)
    return jsonify(response.model_dump())


# Retrieval Analytics Handlers

@catch_mlflow_exception
@_disable_if_artifacts_only
def get_precision_recall_over_time_handler():
    """
    Handler for `POST /ajax-api/2.0/mlflow/traces/insights/precision-recall-over-time`
    Returns precision/recall metrics over time with bucketing.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    time_bucket: str = data.get('time_bucket', 'hour')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    precision_recall_points = get_precision_recall_over_time(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time,
        time_bucket=time_bucket
    )
    
    response = PrecisionRecallOverTimeResponse(precision_recall_over_time=precision_recall_points)
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_document_usage_over_time_handler():
    """
    Handler for `POST /ajax-api/2.0/mlflow/traces/insights/document-usage-over-time`
    Returns document usage metrics over time with bucketing.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    time_bucket: str = data.get('time_bucket', 'hour')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    usage_points = get_document_usage_over_time(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time,
        time_bucket=time_bucket
    )
    
    response = DocumentUsageOverTimeResponse(document_usage_over_time=usage_points)
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_retrieval_latency_over_time_handler():
    """
    Handler for `POST /ajax-api/2.0/mlflow/traces/insights/retrieval-latency-over-time`
    Returns retrieval latency percentiles over time with bucketing.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    time_bucket: str = data.get('time_bucket', 'hour')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    latency_points = get_retrieval_latency_over_time(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time,
        time_bucket=time_bucket
    )
    
    response = RetrievalLatencyOverTimeResponse(retrieval_latency_over_time=latency_points)
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_top_retrieved_documents_handler():
    """
    Handler for `POST /ajax-api/2.0/mlflow/traces/insights/top-retrieved-documents`
    Returns most frequently retrieved documents with analytics.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    limit: int = data.get('limit', 20)
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    document_points = get_top_retrieved_documents(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    response = TopRetrievedDocumentsResponse(top_retrieved_documents=document_points)
    return jsonify(response.model_dump())


# Tools Analytics Handlers

@catch_mlflow_exception
@_disable_if_artifacts_only
def get_tool_discovery_handler():
    """
    Handler for `POST /ajax-api/2.0/mlflow/traces/insights/tool-discovery`
    Returns discovered tools with performance metrics.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    limit: int = data.get('limit', 50)
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    tools = get_tool_discovery(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    response = ToolDiscoveryResponse(tools=tools, total_tools=len(tools))
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_tool_volume_over_time_handler():
    """
    Handler for `POST /ajax-api/2.0/mlflow/traces/insights/tool-volume-over-time`
    Returns tool call volume over time with bucketing.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    tool_names: Optional[List[str]] = data.get('tool_names')
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    time_bucket: str = data.get('time_bucket', 'hour')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    tool_volumes = get_tool_volume_over_time(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        tool_names=tool_names,
        start_time=start_time,
        end_time=end_time,
        time_bucket=time_bucket
    )
    
    response = ToolVolumeOverTimeResponse(tool_volumes=tool_volumes)
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_tool_latency_over_time_handler():
    """
    Handler for `POST /ajax-api/2.0/mlflow/traces/insights/tool-latency-over-time`
    Returns tool latency percentiles over time with bucketing.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    tool_names: Optional[List[str]] = data.get('tool_names')
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    time_bucket: str = data.get('time_bucket', 'hour')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    tool_latencies = get_tool_latency_over_time(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        tool_names=tool_names,
        start_time=start_time,
        end_time=end_time,
        time_bucket=time_bucket
    )
    
    response = ToolLatencyOverTimeResponse(tool_latencies=tool_latencies)
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def get_tool_error_rate_over_time_handler():
    """
    Handler for `POST /ajax-api/2.0/mlflow/traces/insights/tool-error-rate-over-time`
    Returns tool error rates over time with bucketing.
    """
    # Get JSON data from request
    data = request.get_json() or {}
    
    # Extract parameters with type hints
    experiment_ids: List[str] = data.get('experiment_ids', [])
    tool_names: Optional[List[str]] = data.get('tool_names')
    start_time: Optional[int] = data.get('start_time')
    end_time: Optional[int] = data.get('end_time')
    time_bucket: str = data.get('time_bucket', 'hour')
    
    # Validate required fields
    if not experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    tool_error_rates = get_tool_error_rate_over_time(
        store=_get_tracking_store(),
        experiment_ids=experiment_ids,
        tool_names=tool_names,
        start_time=start_time,
        end_time=end_time,
        time_bucket=time_bucket
    )
    
    response = ToolErrorRateOverTimeResponse(tool_error_rates=tool_error_rates)
    return jsonify(response.model_dump())