"""MLflow Trace Insights - REST API Handlers with InsightsStore

REST API handlers that use the centralized InsightsStore for all computations.
These handlers follow the REST API specification in insights_rest_api.md.
"""

from flask import jsonify, request
from mlflow.server.handlers import (
    _get_tracking_store,
    catch_mlflow_exception,
    _disable_if_artifacts_only,
)
from mlflow.server.trace_insights.insights_store import InsightsStore
from mlflow.server.trace_insights.models import (
    # Traffic models
    VolumeRequest, LatencyRequest, ErrorRequest,
    # Assessment models
    AssessmentDiscoveryRequest, AssessmentMetricsRequest,
    # Tool models
    ToolDiscoveryRequest, ToolMetricsRequest,
    # Tag models
    TagDiscoveryRequest, TagMetricsRequest,
    # Dimension models
    DimensionDiscoveryRequest, NPMIRequest,
    # Correlation models
    CorrelationsRequest
)


# ============================================================================
# Traffic & Cost Handlers
# ============================================================================

@catch_mlflow_exception
@_disable_if_artifacts_only
def traffic_volume_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/traffic-cost/volume`
    Returns trace volume statistics with summary and time series.
    """
    data = request.get_json() or {}
    
    # Create request object
    req = VolumeRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        time_bucket=data.get('time_bucket', 'hour')
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    # Get insights store and compute response
    store = InsightsStore(_get_tracking_store())
    response = store.get_traffic_volume(req)
    
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def traffic_latency_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/traffic-cost/latency`
    Returns latency percentile statistics with summary and time series.
    """
    data = request.get_json() or {}
    
    # Create request object
    req = LatencyRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        time_bucket=data.get('time_bucket', 'hour')
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    # Get insights store and compute response
    store = InsightsStore(_get_tracking_store())
    response = store.get_traffic_latency(req)
    
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def traffic_errors_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/traffic-cost/errors`
    Returns error rate statistics with summary and time series.
    """
    data = request.get_json() or {}
    
    # Create request object
    req = ErrorRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        time_bucket=data.get('time_bucket', 'hour')
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    # Get insights store and compute response
    store = InsightsStore(_get_tracking_store())
    response = store.get_traffic_errors(req)
    
    return jsonify(response.model_dump())


# ============================================================================
# Assessment Handlers
# ============================================================================

@catch_mlflow_exception
@_disable_if_artifacts_only
def assessment_discovery_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/assessments/discovery`
    Returns all discovered assessments with their types and statistics.
    """
    data = request.get_json() or {}
    
    # Create request object
    req = AssessmentDiscoveryRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time')
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    # Get insights store and compute response
    store = InsightsStore(_get_tracking_store())
    response = store.get_assessment_discovery(req)
    
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def assessment_metrics_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/assessments/metrics`
    Returns detailed metrics for a specific assessment.
    """
    data = request.get_json() or {}
    
    # Create request object
    req = AssessmentMetricsRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        time_bucket=data.get('time_bucket', 'hour'),
        assessment_name=data.get('assessment_name', '')
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    if not req.assessment_name:
        return jsonify({"error": "assessment_name is required"}), 400
    
    # Get insights store and compute response
    store = InsightsStore(_get_tracking_store())
    response = store.get_assessment_metrics(req)
    
    return jsonify(response.model_dump())


# ============================================================================
# Tool Handlers
# ============================================================================

@catch_mlflow_exception
@_disable_if_artifacts_only
def tool_discovery_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/tools/discovery`
    Returns all discovered tools with their performance metrics.
    """
    data = request.get_json() or {}
    
    # Create request object
    req = ToolDiscoveryRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        limit=data.get('limit', 50)
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    # Get insights store and compute response
    store = InsightsStore(_get_tracking_store())
    response = store.get_tool_discovery(req)
    
    # Transform response to match UI expectations
    # The model has 'data' field but UI expects 'tools' field
    response_dict = response.model_dump()
    if 'data' in response_dict:
        # Transform each tool in the data array to match UI expectations
        tools = []
        for tool in response_dict['data']:
            tools.append({
                'name': tool.get('tool_name', ''),
                'trace_count': tool.get('trace_count', 0),
                'invocation_count': tool.get('invocation_count', 0),
                'error_count': tool.get('error_count', 0),
                'avg_latency_ms': tool.get('avg_latency_ms', None),
                'p50_latency': tool.get('p50_latency', None),
                'p90_latency': tool.get('p90_latency', None),
                'p99_latency': tool.get('p99_latency', None)
            })
        return jsonify({'tools': tools})
    
    return jsonify(response_dict)


@catch_mlflow_exception
@_disable_if_artifacts_only
def tool_metrics_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/tools/metrics`
    Returns detailed metrics for a specific tool.
    """
    data = request.get_json() or {}
    
    # Create request object
    req = ToolMetricsRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        time_bucket=data.get('time_bucket', 'hour'),
        tool_name=data.get('tool_name', '')
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    if not req.tool_name:
        return jsonify({"error": "tool_name is required"}), 400
    
    # Get insights store and compute response
    store = InsightsStore(_get_tracking_store())
    response = store.get_tool_metrics(req)
    
    # Transform response to match UI expectations
    response_dict = response.model_dump()
    if 'data' in response_dict and 'time_series' in response_dict['data']:
        # Extract the time_series from nested structure
        ts_data = response_dict['data']['time_series']
        
        # Combine volume, latency, and errors into unified time series
        time_buckets = set()
        if 'volume' in ts_data:
            for point in ts_data['volume']:
                time_buckets.add(point['time_bucket'])
        if 'errors' in ts_data:
            for point in ts_data['errors']:
                time_buckets.add(point['time_bucket'])
        if 'latency' in ts_data:
            for point in ts_data['latency']:
                time_buckets.add(point['time_bucket'])
        
        # Build unified time series array
        time_series = []
        for bucket in sorted(time_buckets):
            point = {
                'time_bucket': bucket,
                'count': 0,
                'error_count': 0,
                'p50_latency': None,
                'p90_latency': None,
                'p99_latency': None
            }
            
            # Add volume data
            for vol in ts_data.get('volume', []):
                if vol['time_bucket'] == bucket:
                    point['count'] = vol.get('count', 0)
                    break
            
            # Add error data
            for err in ts_data.get('errors', []):
                if err['time_bucket'] == bucket:
                    point['error_count'] = err.get('error_count', 0)
                    break
            
            # Add latency data
            for lat in ts_data.get('latency', []):
                if lat['time_bucket'] == bucket:
                    point['p50_latency'] = lat.get('p50_latency')
                    point['p90_latency'] = lat.get('p90_latency')
                    point['p99_latency'] = lat.get('p99_latency')
                    break
            
            time_series.append(point)
        
        # If no time series data, return empty array
        return jsonify({'time_series': time_series})
    
    return jsonify(response_dict)


# ============================================================================
# Tag Handlers
# ============================================================================

@catch_mlflow_exception
@_disable_if_artifacts_only
def tag_discovery_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/tags/discovery`
    Returns all discovered tag keys with their statistics.
    """
    data = request.get_json() or {}
    
    # Create request object
    req = TagDiscoveryRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        limit=data.get('limit', 100)
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    # Get insights store and compute response
    store = InsightsStore(_get_tracking_store())
    response = store.get_tag_discovery(req)
    
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def tag_metrics_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/tags/metrics`
    Returns detailed metrics for a specific tag key.
    """
    data = request.get_json() or {}
    
    # Create request object
    req = TagMetricsRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        tag_key=data.get('tag_key', ''),
        limit=data.get('limit', 10)
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    if not req.tag_key:
        return jsonify({"error": "tag_key is required"}), 400
    
    # Get insights store and compute response
    store = InsightsStore(_get_tracking_store())
    response = store.get_tag_metrics(req)
    
    return jsonify(response.model_dump())


# ============================================================================
# Dimension Handlers
# ============================================================================

@catch_mlflow_exception
@_disable_if_artifacts_only
def dimension_discovery_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/dimensions/discovery`
    Returns all available dimensions for correlation analysis.
    """
    data = request.get_json() or {}
    
    # Create request object
    req = DimensionDiscoveryRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time')
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    # Get insights store and compute response
    store = InsightsStore(_get_tracking_store())
    response = store.get_dimension_discovery(req)
    
    return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def calculate_npmi_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/dimensions/calculate-npmi`
    Calculates NPMI correlation between two dimensions.
    """
    data = request.get_json() or {}
    
    # Create request object
    req = NPMIRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        dimension1=data.get('dimension1', {}),
        dimension2=data.get('dimension2', {})
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    if not req.dimension1:
        return jsonify({"error": "dimension1 is required"}), 400
    if not req.dimension2:
        return jsonify({"error": "dimension2 is required"}), 400
    
    # Get insights store and compute response
    store = InsightsStore(_get_tracking_store())
    response = store.calculate_npmi(req)
    
    return jsonify(response.model_dump())


# ============================================================================
# Correlation Handler
# ============================================================================

@catch_mlflow_exception
@_disable_if_artifacts_only
def correlations_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/correlations`
    Returns top NPMI correlations for a given filter.
    """
    data = request.get_json() or {}
    
    # Create request object
    req = CorrelationsRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        filter_string=data.get('filter_string', ''),
        correlation_dimensions=data.get('correlation_dimensions', ['tag', 'assessment', 'span_attribute']),
        limit=data.get('limit', 10)
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    if not req.filter_string:
        return jsonify({"error": "filter_string is required"}), 400
    
    # Get insights store and compute response
    store = InsightsStore(_get_tracking_store())
    response = store.get_correlations(req)
    
    return jsonify(response.model_dump())