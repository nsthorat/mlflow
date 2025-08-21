"""MLflow Trace Insights - Dimension Discovery and NPMI Calculations

This module provides dimension discovery and NPMI (Normalized Pointwise Mutual Information)
correlation calculations for trace insights.
"""

import math
from typing import List, Dict, Any, Optional
from sqlalchemy import func, case, and_, or_, distinct, desc
from mlflow.store.tracking.sqlalchemy_store import SqlAlchemyStore
from mlflow.store.tracking.dbmodels.models import (
    SqlTraceInfo,
    SqlTraceTag,
    SqlSpan
)
from mlflow.server.trace_insights.models import (
    Dimension,
    DimensionParameter,
    CorrelationItem
)
from mlflow.server.trace_insights.tag_utils import should_filter_tag


def discover_dimensions(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    start_time: Optional[int] = None,
    end_time: Optional[int] = None
) -> List[Dimension]:
    """
    Discover all available dimensions for correlation analysis.
    
    Args:
        store: SQLAlchemy tracking store
        experiment_ids: List of experiment IDs to analyze
        start_time: Optional start timestamp in milliseconds
        end_time: Optional end timestamp in milliseconds
        
    Returns:
        List of discovered dimensions
    """
    dimensions = []
    
    def query_func(session):
        # Build base query
        base_query = session.query(SqlTraceInfo).filter(
            SqlTraceInfo.experiment_id.in_(experiment_ids)
        )
        
        # Add time filters
        if start_time:
            base_query = base_query.filter(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            base_query = base_query.filter(SqlTraceInfo.timestamp_ms <= end_time)
        
        # Get trace IDs for filtering
        trace_ids = [t.request_id for t in base_query.with_entities(SqlTraceInfo.request_id).all()]
        
        if not trace_ids:
            return []
        
        # Discover tag dimensions
        tag_query = session.query(
            SqlTraceTag.key,
            func.count(distinct(SqlTraceTag.value)).label('unique_values')
        ).filter(
            SqlTraceTag.request_id.in_(trace_ids)
        ).group_by(SqlTraceTag.key).all()
        
        tag_dimensions = []
        for row in tag_query:
            # Filter out built-in MLflow tags using shared utility
            if should_filter_tag(row.key):
                continue
                
            # Determine data type based on values
            sample_values = session.query(SqlTraceTag.value).filter(
                and_(
                    SqlTraceTag.request_id.in_(trace_ids),
                    SqlTraceTag.key == row.key
                )
            ).limit(10).all()
            
            data_type = infer_data_type([v[0] for v in sample_values])
            
            tag_dimensions.append(Dimension(
                name=f"tag.{row.key}",
                type="tag",
                data_type=data_type,
                parameters=[
                    DimensionParameter(name="key", type="string", required=True),
                    DimensionParameter(name="value", type=data_type, required=True)
                ]
            ))
        
        # TODO: Discover span attribute dimensions when SqlSpanAttribute is available
        span_dimensions = []
        
        # Add built-in dimensions
        builtin_dimensions = [
            Dimension(
                name="trace.status",
                type="builtin",
                data_type="string",
                parameters=[
                    DimensionParameter(name="value", type="string", required=True)
                ]
            ),
            Dimension(
                name="trace.has_error",
                type="builtin",
                data_type="boolean",
                parameters=[]
            ),
            Dimension(
                name="trace.latency_bucket",
                type="builtin",
                data_type="string",
                parameters=[
                    DimensionParameter(name="buckets", type="array", required=False)
                ]
            )
        ]
        
        return tag_dimensions + span_dimensions + builtin_dimensions
    
    dimensions = store.execute_query(query_func)
    return dimensions if dimensions else []


def infer_data_type(values: List[Any]) -> str:
    """
    Infer the data type from a list of sample values.
    
    Args:
        values: List of sample values
        
    Returns:
        Data type: "boolean", "numeric", or "string"
    """
    if not values:
        return "string"
    
    # Check if all values are boolean-like
    boolean_values = {"true", "false", "yes", "no", "1", "0", "t", "f"}
    if all(str(v).lower() in boolean_values for v in values if v is not None):
        return "boolean"
    
    # Check if all values are numeric
    try:
        for v in values:
            if v is not None and v != "":
                float(v)
        return "numeric"
    except (ValueError, TypeError):
        pass
    
    return "string"


def calculate_npmi_score(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    dimension1: Dict[str, Any],
    dimension2: Dict[str, Any],
    start_time: Optional[int] = None,
    end_time: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate NPMI correlation score between two dimensions.
    
    Args:
        store: SQLAlchemy tracking store
        experiment_ids: List of experiment IDs to analyze
        dimension1: First dimension specification
        dimension2: Second dimension specification
        start_time: Optional start timestamp in milliseconds
        end_time: Optional end timestamp in milliseconds
        
    Returns:
        Dictionary with dimension counts, intersection, and NPMI score
    """
    def query_func(session):
        # Build base query
        base_query = session.query(SqlTraceInfo).filter(
            SqlTraceInfo.experiment_id.in_(experiment_ids)
        )
        
        # Add time filters
        if start_time:
            base_query = base_query.filter(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            base_query = base_query.filter(SqlTraceInfo.timestamp_ms <= end_time)
        
        # Get total trace count
        total_count = base_query.count()
        
        if total_count == 0:
            return {
                'dimension1': {'name': dimension1.get('name', ''), 'value': dimension1.get('value', ''), 'count': 0},
                'dimension2': {'name': dimension2.get('name', ''), 'value': dimension2.get('value', ''), 'count': 0},
                'intersection': {'count': 0},
                'correlation': {'npmi_score': 0.0, 'strength': 'None'}
            }
        
        # Get traces matching dimension1
        dim1_traces = get_traces_for_dimension(session, base_query, dimension1)
        dim1_count = len(dim1_traces)
        
        # Get traces matching dimension2
        dim2_traces = get_traces_for_dimension(session, base_query, dimension2)
        dim2_count = len(dim2_traces)
        
        # Calculate intersection
        intersection_count = len(dim1_traces.intersection(dim2_traces))
        
        # Calculate NPMI
        if dim1_count == 0 or dim2_count == 0 or intersection_count == 0:
            npmi_score = 0.0
        else:
            # P(dim1)
            p_dim1 = dim1_count / total_count
            # P(dim2)
            p_dim2 = dim2_count / total_count
            # P(dim1, dim2)
            p_intersection = intersection_count / total_count
            
            # PMI = log(P(dim1, dim2) / (P(dim1) * P(dim2)))
            pmi = math.log(p_intersection / (p_dim1 * p_dim2))
            
            # NPMI = PMI / -log(P(dim1, dim2))
            # Avoid division by zero
            if p_intersection == 1.0:
                npmi_score = 1.0
            else:
                npmi_score = pmi / -math.log(p_intersection)
        
        # Determine correlation strength
        strength = get_correlation_strength(npmi_score)
        
        return {
            'dimension1': {
                'name': dimension1.get('name', ''),
                'value': dimension1.get('value', ''),
                'count': dim1_count
            },
            'dimension2': {
                'name': dimension2.get('name', ''),
                'value': dimension2.get('value', ''),
                'count': dim2_count
            },
            'intersection': {
                'count': intersection_count
            },
            'correlation': {
                'npmi_score': npmi_score,
                'strength': strength
            }
        }
    
    return store.execute_query(query_func)


def get_traces_for_dimension(session, base_query, dimension: Dict[str, Any]) -> set:
    """
    Get trace IDs matching a dimension specification.
    
    Args:
        session: SQLAlchemy session
        base_query: Base query for traces
        dimension: Dimension specification
        
    Returns:
        Set of trace IDs matching the dimension
    """
    dim_type = dimension.get('type', '')
    dim_name = dimension.get('name', '')
    dim_value = dimension.get('value')
    
    if dim_type == 'tag' or dim_name.startswith('tag.'):
        # Extract tag key from dimension name
        tag_key = dim_name.replace('tag.', '') if dim_name.startswith('tag.') else dimension.get('key', '')
        
        tag_query = base_query.join(
            SqlTraceTag, SqlTraceInfo.request_id == SqlTraceTag.request_id
        ).filter(
            SqlTraceTag.key == tag_key
        )
        
        if dim_value is not None:
            tag_query = tag_query.filter(SqlTraceTag.value == str(dim_value))
        
        return set(t.request_id for t in tag_query.with_entities(SqlTraceInfo.request_id).all())
    
    elif dim_type == 'span_attribute' or dim_name.startswith('span_attribute.'):
        # TODO: Implement when SqlSpanAttribute is available
        return set()
    
    elif dim_name == 'trace.status':
        status_query = base_query.filter(SqlTraceInfo.status == dim_value)
        return set(t.request_id for t in status_query.with_entities(SqlTraceInfo.request_id).all())
    
    elif dim_name == 'trace.has_error':
        if dim_value or dim_value == 'true':
            error_query = base_query.filter(SqlTraceInfo.status == 'ERROR')
        else:
            error_query = base_query.filter(SqlTraceInfo.status != 'ERROR')
        return set(t.request_id for t in error_query.with_entities(SqlTraceInfo.request_id).all())
    
    else:
        # Unknown dimension type
        return set()


def get_correlation_strength(npmi_score: float) -> str:
    """
    Classify correlation strength based on NPMI score.
    
    Args:
        npmi_score: NPMI score between -1 and 1
        
    Returns:
        Strength classification: "Strong", "Moderate", "Weak", or "None"
    """
    abs_score = abs(npmi_score)
    
    if abs_score >= 0.7:
        return "Strong"
    elif abs_score >= 0.4:
        return "Moderate"
    elif abs_score >= 0.1:
        return "Weak"
    else:
        return "None"


def get_correlations_for_filter(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    filter_string: str,
    correlation_dimensions: List[str],
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get top NPMI correlations for a given filter.
    
    Args:
        store: SQLAlchemy tracking store
        experiment_ids: List of experiment IDs to analyze
        filter_string: Filter to correlate against (e.g., "status:ERROR")
        correlation_dimensions: List of dimension types to check
        start_time: Optional start timestamp in milliseconds
        end_time: Optional end timestamp in milliseconds
        limit: Maximum number of correlations to return
        
    Returns:
        List of top correlations with NPMI scores
    """
    # Parse filter string to get base dimension
    base_dimension = parse_filter_string(filter_string)
    
    # Discover available dimensions
    all_dimensions = discover_dimensions(store, experiment_ids, start_time, end_time)
    
    # Filter dimensions based on requested types
    relevant_dimensions = [
        d for d in all_dimensions
        if any(d.type == dim_type for dim_type in correlation_dimensions)
    ]
    
    correlations = []
    
    def query_func(session):
        # Build base query
        base_query = session.query(SqlTraceInfo).filter(
            SqlTraceInfo.experiment_id.in_(experiment_ids)
        )
        
        # Add time filters
        if start_time:
            base_query = base_query.filter(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            base_query = base_query.filter(SqlTraceInfo.timestamp_ms <= end_time)
        
        # Get total trace count
        total_count = base_query.count()
        
        # Get traces matching the filter
        filter_traces = get_traces_for_dimension(session, base_query, base_dimension)
        filter_count = len(filter_traces)
        
        if filter_count == 0:
            return []
        
        # Calculate correlations for each dimension
        for dimension in relevant_dimensions:
            # Get unique values for this dimension
            if dimension.type == 'tag':
                tag_key = dimension.name.replace('tag.', '')
                values_query = session.query(
                    SqlTraceTag.value,
                    func.count(SqlTraceTag.request_id).label('count')
                ).filter(
                    and_(
                        SqlTraceTag.request_id.in_(filter_traces),
                        SqlTraceTag.key == tag_key
                    )
                ).group_by(SqlTraceTag.value).order_by(desc('count')).limit(20).all()
                
                for value_row in values_query:
                    if value_row.value:
                        # Calculate NPMI for this value
                        dim_spec = {
                            'type': 'tag',
                            'name': dimension.name,
                            'key': tag_key,
                            'value': value_row.value
                        }
                        
                        # Get traces for this dimension value
                        dim_traces = get_traces_for_dimension(session, base_query, dim_spec)
                        dim_count = len(dim_traces)
                        
                        # Calculate intersection
                        intersection_count = len(filter_traces.intersection(dim_traces))
                        
                        if intersection_count > 0:
                            # Calculate NPMI
                            p_filter = filter_count / total_count
                            p_dim = dim_count / total_count
                            p_intersection = intersection_count / total_count
                            
                            if p_filter > 0 and p_dim > 0 and p_intersection > 0:
                                pmi = math.log(p_intersection / (p_filter * p_dim))
                                npmi_score = pmi / -math.log(p_intersection) if p_intersection < 1.0 else 1.0
                                
                                correlations.append({
                                    'dimension': dimension.name,
                                    'value': value_row.value,
                                    'npmi_score': npmi_score,
                                    'trace_count': intersection_count,
                                    'percentage_of_slice': (intersection_count / filter_count * 100),
                                    'percentage_of_total': (intersection_count / total_count * 100),
                                    'strength': get_correlation_strength(npmi_score)
                                })
        
        # Sort by NPMI score (absolute value)
        correlations.sort(key=lambda x: abs(x['npmi_score']), reverse=True)
        
        return correlations[:limit]
    
    return store.execute_query(query_func)


def parse_filter_string(filter_string: str) -> Dict[str, Any]:
    """
    Parse a filter string into a dimension specification.
    
    Args:
        filter_string: Filter string (e.g., "status:ERROR", "tag.tool_name:AgentExecutor")
        
    Returns:
        Dimension specification dictionary
    """
    if ':' in filter_string:
        key, value = filter_string.split(':', 1)
        
        if key == 'status':
            return {
                'type': 'builtin',
                'name': 'trace.status',
                'value': value
            }
        elif key == 'has_error':
            return {
                'type': 'builtin',
                'name': 'trace.has_error',
                'value': value.lower() == 'true'
            }
        elif key.startswith('tag.'):
            tag_key = key.replace('tag.', '')
            return {
                'type': 'tag',
                'name': key,
                'key': tag_key,
                'value': value
            }
        elif key.startswith('span_attribute.'):
            attr_key = key.replace('span_attribute.', '')
            return {
                'type': 'span_attribute',
                'name': key,
                'key': attr_key,
                'value': value
            }
    
    # Default to error status if no valid filter
    return {
        'type': 'builtin',
        'name': 'trace.status',
        'value': 'ERROR'
    }