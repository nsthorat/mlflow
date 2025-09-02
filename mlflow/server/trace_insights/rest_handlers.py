"""MLflow Trace Insights - REST API Handlers

REST API handlers that use the appropriate insights store implementation
based on the tracking backend configuration.
These handlers follow the REST API specification in insights_rest_api.md.
"""

import os
import logging
from datetime import datetime
from flask import jsonify, request
from mlflow.server.handlers import (
    _get_tracking_store,
    catch_mlflow_exception,
    _disable_if_artifacts_only,
)

# Set up logging
logger = logging.getLogger(__name__)
from mlflow.server.trace_insights.models import (
    # Traffic models
    VolumeRequest, LatencyRequest, ErrorRequest, 
    VolumeResponse, LatencyResponse, ErrorResponse,
    # Assessment models
    AssessmentDiscoveryRequest, AssessmentMetricsRequest,
    AssessmentDiscoveryResponse, AssessmentMetricsResponse,
    # Tool models
    ToolDiscoveryRequest, ToolMetricsRequest,
    ToolDiscoveryResponse, ToolMetricsResponse,
    # Tag models
    TagDiscoveryRequest, TagMetricsRequest,
    TagDiscoveryResponse, TagMetricsResponse,
    # Dimension models
    DimensionDiscoveryRequest, NPMIRequest,
    DimensionDiscoveryResponse, NPMIResponse,
    # Correlation models
    CorrelationsRequest, CorrelationsResponse
)


def _get_insights_store():
    """Get the appropriate insights store based on tracking URI.
    
    Returns:
        InsightsAbstractStore implementation based on backend configuration
    """
    # Get tracking URI from the server environment (set by _run_server)
    tracking_uri = os.environ.get('_MLFLOW_SERVER_FILE_STORE', '') or os.environ.get('MLFLOW_TRACKING_URI', '')
    databricks_host = os.environ.get('DATABRICKS_HOST', '')
    databricks_token = os.environ.get('DATABRICKS_TOKEN', '')
    
    # Also check for DATABRICKS_CONFIG_PROFILE which indicates Databricks mode
    databricks_profile = os.environ.get('DATABRICKS_CONFIG_PROFILE', '')
    
    logger.info(f"Getting insights store for tracking_uri: {tracking_uri}")
    logger.info(f"DATABRICKS_HOST: {databricks_host if databricks_host else 'NOT SET'}")
    logger.info(f"DATABRICKS_TOKEN: {'SET' if databricks_token else 'NOT SET'}")
    logger.info(f"DATABRICKS_CONFIG_PROFILE: {databricks_profile if databricks_profile else 'NOT SET'}")
    
    # Note: Experiment IDs should come from the request, not from environment
    # The handlers will set MLFLOW_EXPERIMENT_IDS when processing requests
    
    # Check if we should use Databricks - either by tracking URI or by presence of Databricks credentials
    if tracking_uri == 'databricks' or databricks_profile:
        # Use Databricks SQL insights store for Databricks backend
        logger.info("Using Databricks SQL insights store")
        from mlflow.store.tracking.insights_databricks_sql_store import InsightsDatabricksSqlStore
        return InsightsDatabricksSqlStore('databricks')
    else:
        # Use SQLAlchemy insights store for local database backends
        logger.info(f"Using SQLAlchemy insights store for URI: {tracking_uri}")
        from mlflow.store.tracking.insights_sqlalchemy_store import InsightsSqlAlchemyStore
        # Default artifact root for local store
        default_artifact_root = os.environ.get('MLFLOW_DEFAULT_ARTIFACT_ROOT', 'mlruns')
        return InsightsSqlAlchemyStore(tracking_uri, default_artifact_root)


def _convert_iso_to_ms(iso_timestamp):
    """Convert ISO timestamp string to milliseconds since epoch.
    
    Args:
        iso_timestamp: ISO timestamp string (e.g., '2024-08-25T15:30:00.000Z') or None
        
    Returns:
        int: Milliseconds since epoch, or None if input is None
    """
    if iso_timestamp is None:
        return None
    if isinstance(iso_timestamp, int):
        return iso_timestamp  # Already in milliseconds
    try:
        # Parse ISO timestamp and convert to milliseconds
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return int(dt.timestamp() * 1000)
    except (ValueError, AttributeError):
        # If parsing fails, assume it's already an integer or return None
        return None


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
    try:
        data = request.get_json() or {}
        
        # Get experiment IDs and set in environment
        experiment_ids = data.get('experiment_ids', [])
        if not experiment_ids:
            return jsonify({"error": "experiment_ids is required"}), 400
        
        # Set experiment IDs in environment for store to use
        os.environ['MLFLOW_EXPERIMENT_IDS'] = ','.join(str(eid) for eid in experiment_ids)
        
        # Get insights store and compute response
        store = _get_insights_store()
        
        # Call store method with well-typed arguments
        result = store.get_traffic_volume(
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            time_bucket=data.get('time_bucket', 'hour'),
            timezone=data.get('timezone')
        )
        
        # Log the raw result to understand the structure
        logger.info(f"Raw volume result: {result}")
        
        # Fix field name mapping if needed
        if 'summary' in result and result['summary']:
            summary = result['summary']
            # Map any field name differences here if needed
            if 'total_traces' not in summary and 'trace_count' in summary:
                summary['total_traces'] = summary.pop('trace_count')
            if 'total_cost' not in summary and 'cost' in summary:
                summary['total_cost'] = summary.pop('cost')
        
        # Convert result to response model
        response = VolumeResponse(**result)
        
        return jsonify(response.model_dump())
    except Exception as e:
        logger.error(f"Error in traffic_volume_handler: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@catch_mlflow_exception
@_disable_if_artifacts_only
def traffic_latency_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/traffic-cost/latency`
    Returns latency percentile statistics with summary and time series.
    """
    try:
        data = request.get_json() or {}
        
        # Get experiment IDs and set in environment
        experiment_ids = data.get('experiment_ids', [])
        if not experiment_ids:
            return jsonify({"error": "experiment_ids is required"}), 400
        
        # Set experiment IDs in environment for store to use
        os.environ['MLFLOW_EXPERIMENT_IDS'] = ','.join(str(eid) for eid in experiment_ids)
        
        # Get insights store and compute response
        store = _get_insights_store()
        
        # Call store method with well-typed arguments
        result = store.get_traffic_latency(
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            time_bucket=data.get('time_bucket', 'hour'),
            timezone=data.get('timezone')
        )
        
        # Log the raw result to understand the structure
        logger.info(f"Raw latency result: {result}")
        
        # Fix field name mapping - the store returns different names
        if 'summary' in result and result['summary']:
            summary = result['summary']
            # Map the field names from store format to API format
            if 'p50' in summary:
                summary['p50_latency'] = summary.pop('p50')
            if 'p90' in summary:
                summary['p90_latency'] = summary.pop('p90')
            elif 'p90_latency' not in summary:
                # Add missing p90 field with default value
                summary['p90_latency'] = None
            if 'p95' in summary:
                summary['p95_latency'] = summary.pop('p95')
            if 'p99' in summary:
                summary['p99_latency'] = summary.pop('p99')
            if 'avg_latency_ms' in summary:
                summary['avg_latency'] = summary.pop('avg_latency_ms')
            if 'min_latency_ms' in summary:
                summary['min_latency'] = summary.pop('min_latency_ms')
            elif 'min_latency' not in summary:
                # Add missing min field with default value
                summary['min_latency'] = None
            if 'max_latency_ms' in summary:
                summary['max_latency'] = summary.pop('max_latency_ms')
            elif 'max_latency' not in summary:
                # Add missing max field with default value
                summary['max_latency'] = None
        
        # Convert result to response model
        response = LatencyResponse(**result)
        
        return jsonify(response.model_dump())
    except Exception as e:
        logger.error(f"Error in traffic_latency_handler: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@catch_mlflow_exception
@_disable_if_artifacts_only
def traffic_errors_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/traffic-cost/errors`
    Returns error rate statistics with summary and time series.
    """
    try:
        data = request.get_json() or {}
        
        # Get experiment IDs and set in environment
        experiment_ids = data.get('experiment_ids', [])
        if not experiment_ids:
            return jsonify({"error": "experiment_ids is required"}), 400
        
        # Set experiment IDs in environment for store to use
        os.environ['MLFLOW_EXPERIMENT_IDS'] = ','.join(str(eid) for eid in experiment_ids)
        
        # Get insights store and compute response
        store = _get_insights_store()
        
        # Call store method with well-typed arguments
        result = store.get_traffic_errors(
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            time_bucket=data.get('time_bucket', 'hour'),
            timezone=data.get('timezone')
        )
        
        # Log the raw result to understand the structure
        logger.info(f"Raw errors result: {result}")
        
        # Fix field name mapping if needed
        if 'summary' in result and result['summary']:
            summary = result['summary']
            # Map any field name differences here if needed
            if 'error_rate' not in summary and 'error_percentage' in summary:
                summary['error_rate'] = summary.pop('error_percentage')
            if 'total_errors' not in summary and 'error_count' in summary:
                summary['total_errors'] = summary.pop('error_count')
            # Ensure error_count field exists (required by API)
            if 'error_count' not in summary:
                summary['error_count'] = summary.get('total_errors', 0)
        
        # Convert result to response model
        response = ErrorResponse(**result)
        
        return jsonify(response.model_dump())
    except Exception as e:
        logger.error(f"Error in traffic_errors_handler: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


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
    
    # Create request object with timestamp conversion
    req = AssessmentDiscoveryRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=_convert_iso_to_ms(data.get('start_time')),
        end_time=_convert_iso_to_ms(data.get('end_time'))
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    # Get the insights store and fetch assessment info
    store = _get_insights_store()
    
    try:
        logger.info(f"Calling store.get_assessments with experiment_id: {req.experiment_ids[0]}")
        assessments = store.get_assessments(req.experiment_ids[0])
        logger.info(f"Got {len(assessments)} assessments from store")
        
        # Transform to proper AssessmentInfo format
        assessment_infos = []
        for assessment in assessments:
            # Debug logging
            assessment_type = assessment.get('data_type', 'boolean')
            logger.info(f"Assessment {assessment.get('name')}: raw data_type={assessment_type}")
            
            # Map field names from store format to API format
            assessment_info = {
                'assessment_name': assessment.get('name', 'unknown'),
                'assessment_type': assessment_type,  # boolean, numeric, string, pass/fail
                'sources': [assessment.get('source', 'databricks').upper()],  # Convert to list and uppercase
                'trace_count': assessment.get('count', 0)
            }
            assessment_infos.append(assessment_info)
        
        # Return proper AssessmentDiscoveryResponse format
        response = AssessmentDiscoveryResponse(data=assessment_infos)
        return jsonify(response.model_dump())
    except Exception as e:
        logger.error(f"Error getting assessments: {e}")
        # Return empty response in proper format
        response = AssessmentDiscoveryResponse(data=[])
        return jsonify(response.model_dump())


@catch_mlflow_exception
@_disable_if_artifacts_only
def assessment_metrics_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/assessments/metrics`
    Returns detailed metrics for a specific assessment.
    """
    data = request.get_json() or {}
    
    # Debug: Log received parameters
    import logging
    logging.info(f"Assessment data request: {data}")
    
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
    
    # Set experiment IDs in environment for store to use
    os.environ['MLFLOW_EXPERIMENT_IDS'] = ','.join(str(eid) for eid in req.experiment_ids)
    
    # Get insights store
    store = _get_insights_store()
    
    # Get REAL assessment metrics data from the store
    result = store.get_assessment_metrics(
        assessment_name=req.assessment_name,
        start_time=req.start_time,
        end_time=req.end_time,
        time_bucket=req.time_bucket,
        timezone=data.get('timezone')
    )
    
    # Determine assessment type based on the assessment name
    # These are common assessment types - adjust as needed
    assessment_type = 'boolean'  # Default type
    if req.assessment_name in ['relevance_to_query', 'groundedness', 'answer_correctness']:
        assessment_type = 'boolean'
    elif req.assessment_name in ['latency', 'token_count', 'cost']:
        assessment_type = 'numeric'
    elif req.assessment_name in ['feedback', 'error_message']:
        assessment_type = 'string'
    
    # Construct proper response with required fields
    response_data = {
        'assessment_name': req.assessment_name,
        'assessment_type': assessment_type,
        'sources': [],  # TODO: Populate with actual sources if available
        'summary': result.get('summary', {}),
        'time_series': result.get('time_series', [])
    }
    
    # Convert to proper response model
    response = AssessmentMetricsResponse(**response_data)
    
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
    
    # Get the insights store and fetch tool info
    store = _get_insights_store()
    
    try:
        tools = store.discover_tools(
            experiment_ids=req.experiment_ids,
            start_time=req.start_time,
            end_time=req.end_time
        )
        return jsonify({'tools': tools})
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        return jsonify({'tools': []})


@catch_mlflow_exception
@_disable_if_artifacts_only
def tool_metrics_handler():
    """
    Handler for `POST /api/3.0/mlflow/traces/insights/tools/metrics`
    Returns detailed metrics for a specific tool OR overall metrics across all tools.
    """
    data = request.get_json() or {}
    
    # Get tool_name and normalize empty string to None
    tool_name = data.get('tool_name')
    if tool_name == '':
        tool_name = None
    
    # Create request object
    req = ToolMetricsRequest(
        experiment_ids=data.get('experiment_ids', []),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        time_bucket=data.get('time_bucket', 'hour'),
        tool_name=tool_name
    )
    
    # Validate required fields
    if not req.experiment_ids:
        return jsonify({"error": "experiment_ids is required"}), 400
    
    # Get the insights store using the same pattern as other working handlers
    store = _get_insights_store()
    
    # Call the store method
    try:
        result = store.get_tool_metrics(
            experiment_ids=req.experiment_ids,
            tool_name=req.tool_name,  # Use the tool_name from the request, not from tools array
            start_time=req.start_time,
            end_time=req.end_time,
            time_bucket=req.time_bucket,
            timezone=data.get('timezone')
        )
        
        # Return the result directly as it should already have the correct format
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting tool metrics: {e}", exc_info=True)
        return jsonify({'summary': {'avg_latency': None, 'p50_latency': None, 'p90_latency': None, 'usage_count': 0}, 'time_series': []})


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
    
    # TODO: Implement tag discovery
    # For now, return empty response
    return jsonify({'tags': []})


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
    
    # TODO: Implement tag metrics
    # For now, return empty response
    return jsonify({'tag_values': [], 'time_series': []})


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
    
    # TODO: Implement dimension discovery
    # For now, return empty response
    return jsonify({'dimensions': []})


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
    
    # TODO: Implement NPMI calculation
    # For now, return empty response
    return jsonify({'npmi': 0.0, 'confidence_lower': None, 'confidence_upper': None})


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
    
    # TODO: Implement correlations
    # For now, return empty response with correct structure
    return jsonify({'data': []})