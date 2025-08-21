"""MLflow Trace Insights Backend Module

This module provides REST API endpoints for trace insights analytics.
All endpoints follow the specification in insights_rest_api.md.
"""


def register_trace_insights_routes(app):
    """
    Register all trace insights routes with the Flask app.
    Routes follow the REST API specification in insights_rest_api.md.
    """
    from mlflow.server.handlers import _get_ajax_path
    from mlflow.server.trace_insights.rest_handlers import (
        # Traffic & Cost handlers
        traffic_volume_handler,
        traffic_latency_handler,
        traffic_errors_handler,
        # Assessment handlers
        assessment_discovery_handler,
        assessment_metrics_handler,
        # Tool handlers
        tool_discovery_handler,
        tool_metrics_handler,
        # Tag handlers
        tag_discovery_handler,
        tag_metrics_handler,
        # Dimension handlers
        dimension_discovery_handler,
        calculate_npmi_handler,
        # Correlation handler
        correlations_handler,
    )
    
    # ============================================================================
    # Traffic & Cost Analytics Endpoints
    # ============================================================================
    
    app.add_url_rule(
        _get_ajax_path("/mlflow/traces/insights/traffic-cost/volume"),
        endpoint="trace_traffic_volume",
        view_func=traffic_volume_handler,
        methods=["POST"]
    )
    
    app.add_url_rule(
        _get_ajax_path("/mlflow/traces/insights/traffic-cost/latency"),
        endpoint="trace_traffic_latency",
        view_func=traffic_latency_handler,
        methods=["POST"]
    )
    
    app.add_url_rule(
        _get_ajax_path("/mlflow/traces/insights/traffic-cost/errors"),
        endpoint="trace_traffic_errors",
        view_func=traffic_errors_handler,
        methods=["POST"]
    )
    
    # ============================================================================
    # Assessment Analytics Endpoints
    # ============================================================================
    
    app.add_url_rule(
        _get_ajax_path("/mlflow/traces/insights/assessments/discovery"),
        endpoint="trace_assessment_discovery",
        view_func=assessment_discovery_handler,
        methods=["POST"]
    )
    
    app.add_url_rule(
        _get_ajax_path("/mlflow/traces/insights/assessments/metrics"),
        endpoint="trace_assessment_metrics",
        view_func=assessment_metrics_handler,
        methods=["POST"]
    )
    
    # ============================================================================
    # Tool Analytics Endpoints
    # ============================================================================
    
    app.add_url_rule(
        _get_ajax_path("/mlflow/traces/insights/tools/discovery"),
        endpoint="trace_tool_discovery",
        view_func=tool_discovery_handler,
        methods=["POST"]
    )
    
    app.add_url_rule(
        _get_ajax_path("/mlflow/traces/insights/tools/metrics"),
        endpoint="trace_tool_metrics",
        view_func=tool_metrics_handler,
        methods=["POST"]
    )
    
    # ============================================================================
    # Tag Analytics Endpoints
    # ============================================================================
    
    app.add_url_rule(
        _get_ajax_path("/mlflow/traces/insights/tags/discovery"),
        endpoint="trace_tag_discovery",
        view_func=tag_discovery_handler,
        methods=["POST"]
    )
    
    app.add_url_rule(
        _get_ajax_path("/mlflow/traces/insights/tags/metrics"),
        endpoint="trace_tag_metrics",
        view_func=tag_metrics_handler,
        methods=["POST"]
    )
    
    # ============================================================================
    # Dimension Endpoints
    # ============================================================================
    
    app.add_url_rule(
        _get_ajax_path("/mlflow/traces/insights/dimensions/discovery"),
        endpoint="trace_dimension_discovery",
        view_func=dimension_discovery_handler,
        methods=["POST"]
    )
    
    app.add_url_rule(
        _get_ajax_path("/mlflow/traces/insights/dimensions/calculate-npmi"),
        endpoint="trace_calculate_npmi",
        view_func=calculate_npmi_handler,
        methods=["POST"]
    )
    
    # ============================================================================
    # Correlation Endpoint
    # ============================================================================
    
    app.add_url_rule(
        _get_ajax_path("/mlflow/traces/insights/correlations"),
        endpoint="trace_correlations",
        view_func=correlations_handler,
        methods=["POST"]
    )


__all__ = [
    "register_trace_insights_routes",
]