"""MLflow Trace Insights - Tools Analytics Module

This module provides computational functions for tool discovery and performance analytics.
Tools are identified from trace names, span types, and other metadata.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, text, and_, or_, case, Integer
from sqlalchemy.orm import Session
from mlflow.store.tracking.sqlalchemy_store import SqlAlchemyStore
from mlflow.store.tracking.dbmodels.models import (
    SqlTraceInfo,
    SqlTraceTag,
    SqlExperiment,
    SqlSpan,
)
from pydantic import BaseModel
from typing import Union
from mlflow.server.trace_insights.time_bucketing import get_time_bucket_expression, validate_time_bucket


# ============= Data Models =============

class ToolDiscoveryInfo(BaseModel):
    """Information about a discovered tool for discovery response."""
    tool_name: str
    total_calls: int
    error_count: int
    success_count: int
    avg_latency_ms: float
    p50_latency_ms: float
    p90_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    first_seen: str
    last_seen: str


class ToolDiscoveryResponse(BaseModel):
    """Response for tool discovery endpoint."""
    tools: List[ToolDiscoveryInfo]
    total_tools: int


class ToolVolumePoint(BaseModel):
    """Single point for tool volume over time."""
    time_bucket: str
    tool_name: str
    call_count: int
    error_count: int
    success_count: int


class ToolVolumeOverTimeResponse(BaseModel):
    """Response for tool volume over time."""
    tool_volumes: List[ToolVolumePoint]


class ToolLatencyPoint(BaseModel):
    """Single point for tool latency metrics."""
    time_bucket: str
    tool_name: str
    p50_latency_ms: float
    p90_latency_ms: float
    p99_latency_ms: float
    avg_latency_ms: float


class ToolLatencyOverTimeResponse(BaseModel):
    """Response for tool latency over time."""
    tool_latencies: List[ToolLatencyPoint]


class ToolErrorRatePoint(BaseModel):
    """Single point for tool error rate."""
    time_bucket: str
    tool_name: str
    error_count: int
    total_count: int
    error_rate: float


class ToolErrorRateOverTimeResponse(BaseModel):
    """Response for tool error rate over time."""
    tool_error_rates: List[ToolErrorRatePoint]


# Legacy models for backward compatibility
PrecisionRecallOverTimeResponse = BaseModel
DocumentUsageOverTimeResponse = BaseModel
RetrievalLatencyOverTimeResponse = BaseModel
TopRetrievedDocumentsResponse = BaseModel


# ============= Tool Discovery Functions =============

def get_tool_discovery(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    limit: int = 50
) -> List[ToolDiscoveryInfo]:
    """
    Discover tools used in traces and compute their metrics.
    Tools are identified from spans with type='TOOL'.
    """
    def tool_discovery_query(session):
        # Import the Span model
        from mlflow.entities.span import Span
        # Use raw SQL query since we need to access spans table directly
        # which may not have a SQLAlchemy model
        
        # Build base SQL query for tools from spans table
        sql = """
        SELECT 
            s.name as tool_name,
            COUNT(DISTINCT s.trace_id) as trace_count,
            COUNT(*) as total_calls,
            SUM(CASE WHEN s.status = 'ERROR' THEN 1 ELSE 0 END) as error_count,
            SUM(CASE WHEN s.status = 'OK' THEN 1 ELSE 0 END) as success_count,
            AVG((s.end_time_unix_nano - s.start_time_unix_nano) / 1000000.0) as avg_latency_ms,
            MIN(s.start_time_unix_nano / 1000000) as first_seen,
            MAX(s.start_time_unix_nano / 1000000) as last_seen
        FROM spans s
        WHERE s.type = 'TOOL'
        """
        
        # Add experiment filter if provided
        if experiment_ids:
            exp_ids_str = ','.join([f"'{exp_id}'" for exp_id in experiment_ids])
            sql += f" AND s.experiment_id IN ({exp_ids_str})"
        
        # Add time range filters
        if start_time:
            sql += f" AND s.start_time_unix_nano >= {start_time * 1000000}"
        if end_time:
            sql += f" AND s.start_time_unix_nano <= {end_time * 1000000}"
        
        # Group by tool name and order by total calls
        sql += """
        GROUP BY s.name
        ORDER BY total_calls DESC
        """
        
        if limit:
            sql += f" LIMIT {limit}"
        
        # Execute the query
        result = session.execute(text(sql))
        rows = result.fetchall()
        
        tools = []
        for row in rows:
            # Get execution times for percentile calculation
            percentile_sql = f"""
            SELECT (end_time_unix_nano - start_time_unix_nano) / 1000000.0 as latency_ms
            FROM spans
            WHERE type = 'TOOL' AND name = :tool_name
            """
            
            if experiment_ids:
                exp_ids_str = ','.join([f"'{exp_id}'" for exp_id in experiment_ids])
                percentile_sql += f" AND experiment_id IN ({exp_ids_str})"
            
            if start_time:
                percentile_sql += f" AND start_time_unix_nano >= {start_time * 1000000}"
            if end_time:
                percentile_sql += f" AND start_time_unix_nano <= {end_time * 1000000}"
            
            percentile_sql += " ORDER BY latency_ms"
            
            latencies_result = session.execute(text(percentile_sql), {'tool_name': row.tool_name})
            latencies = [l[0] for l in latencies_result.fetchall() if l[0] is not None]
            
            # Calculate percentiles
            if latencies:
                n = len(latencies)
                p50 = latencies[int(n * 0.5)] if n > 0 else 0
                p90 = latencies[int(n * 0.9)] if n > 0 else 0
                p99 = latencies[min(int(n * 0.99), n-1)] if n > 0 else 0
            else:
                p50 = p90 = p99 = 0
            
            tools.append(ToolDiscoveryInfo(
                tool_name=row.tool_name,
                total_calls=row.total_calls or 0,
                error_count=row.error_count or 0,
                success_count=row.success_count or 0,
                avg_latency_ms=float(row.avg_latency_ms or 0),
                p50_latency_ms=float(p50),
                p90_latency_ms=float(p90),
                p99_latency_ms=float(p99),
                error_rate=float(row.error_count or 0) / float(row.total_calls) if row.total_calls else 0,
                first_seen=datetime.fromtimestamp(row.first_seen / 1000).isoformat() if row.first_seen else "",
                last_seen=datetime.fromtimestamp(row.last_seen / 1000).isoformat() if row.last_seen else "",
            ))
        
        return tools
    
    return store.execute_query(tool_discovery_query)


def get_tool_volume_over_time(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    tool_names: Optional[List[str]] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    time_bucket: str = "hour",
    timezone: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get tool call volume over time with time bucketing and zero-filling for missing periods using SQLAlchemy.
    """
    def volume_query(session):
        from sqlalchemy import func, text, and_, select, literal_column
        
        # Calculate timezone offset
        offset_ms = 0
        if timezone != 'UTC' and time_bucket in ["day", "week"]:
            try:
                import pytz
                from datetime import datetime
                tz = pytz.timezone(timezone)
                now = datetime.now(pytz.UTC)
                localized = now.astimezone(tz)
                offset_ms = int(localized.utcoffset().total_seconds() * 1000)
            except:
                offset_ms = 0
        
        # Build WHERE conditions using SQLAlchemy
        from mlflow.store.tracking.dbmodels.models import SqlTraceInfo, SqlSpan
        
        filters = [SqlSpan.type == 'TOOL']
        
        if experiment_ids:
            experiment_id = experiment_ids[0]
            filters.append(SqlTraceInfo.experiment_id == experiment_id)
            
        if tool_names:
            filters.append(SqlSpan.name.in_(tool_names))
            
        if start_time:
            filters.append(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            filters.append(SqlTraceInfo.timestamp_ms <= end_time)
        
        # Build time bucket expression
        if time_bucket == "hour":
            bucket_expr = func.cast((SqlTraceInfo.timestamp_ms / 3600000), Integer) * 3600000
            interval_ms = 3600000  # 1 hour in ms
        elif time_bucket == "day":
            bucket_expr = func.cast(((SqlTraceInfo.timestamp_ms + offset_ms) / 86400000), Integer) * 86400000 - offset_ms
            interval_ms = 86400000  # 1 day in ms
        elif time_bucket == "week":
            bucket_expr = func.cast(((SqlTraceInfo.timestamp_ms + offset_ms) / 604800000), Integer) * 604800000 - offset_ms
            interval_ms = 604800000  # 1 week in ms
        else:
            bucket_expr = func.cast((SqlTraceInfo.timestamp_ms / 3600000), Integer) * 3600000  # Default to hour
            interval_ms = 3600000
        
        # Get min and max timestamps for the time range to densify
        bounds_query = (
            session.query(
                func.min(bucket_expr).label('min_bucket'),
                func.max(bucket_expr).label('max_bucket')
            )
            .select_from(SqlSpan)
            .join(SqlTraceInfo, SqlSpan.trace_id == SqlTraceInfo.request_id)
            .filter(and_(*filters))
        )
        
        bounds_result = bounds_query.first()
        if not bounds_result or bounds_result.min_bucket is None:
            return []
        
        min_bucket = int(bounds_result.min_bucket)
        max_bucket = int(bounds_result.max_bucket)
        
        # Generate complete time series using Python instead of SQL CTE for better compatibility
        time_buckets = []
        current_bucket = min_bucket
        while current_bucket <= max_bucket:
            time_buckets.append(current_bucket)
            current_bucket += interval_ms
        
        # Get actual data grouped by tool and time bucket
        actual_data_query = (
            session.query(
                SqlSpan.name.label('tool_name'),
                bucket_expr.label('time_bucket'),
                func.count(SqlSpan.span_id).label('count')
            )
            .select_from(SqlSpan)
            .join(SqlTraceInfo, SqlSpan.trace_id == SqlTraceInfo.request_id)
            .filter(and_(*filters))
            .group_by(SqlSpan.name, bucket_expr)
            .order_by(SqlSpan.name, bucket_expr)
        )
        
        actual_results = actual_data_query.all()
        
        # Get distinct tool names
        tool_names_query = (
            session.query(SqlSpan.name.distinct().label('tool_name'))
            .select_from(SqlSpan)
            .join(SqlTraceInfo, SqlSpan.trace_id == SqlTraceInfo.request_id)
            .filter(and_(*filters))
        )
        
        distinct_tool_names = [row.tool_name for row in tool_names_query.all()]
        
        # Convert actual data to lookup dictionary
        actual_data_dict = {}
        for row in actual_results:
            key = (row.tool_name, int(row.time_bucket))
            actual_data_dict[key] = row.count
        
        # Generate complete results with zero-filling
        results = []
        for tool_name in distinct_tool_names:
            for bucket in time_buckets:
                count = actual_data_dict.get((tool_name, bucket), 0)
                results.append({
                    'tool_name': tool_name,
                    'time_bucket': bucket,
                    'count': count
                })
        
        return results
    
    return store.execute_query(volume_query)


def get_tool_latency_over_time(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    tool_names: Optional[List[str]] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    time_bucket: str = "hour",
    timezone: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get tool latency percentiles over time.
    Uses trace execution times with tool names from tags.
    """
    def latency_query(session):
        # Use timezone-aware time bucket expression
        validated_bucket = validate_time_bucket(time_bucket)
        time_bucket_expr = get_time_bucket_expression(validated_bucket, timezone=timezone)
        
        # Use spans table directly for tool latency data
        from sqlalchemy import text
        
        # Build WHERE conditions
        where_conditions = []
        params = {}
        
        if experiment_ids:
            experiment_id = experiment_ids[0]
            where_conditions.append("ti.experiment_id = :experiment_id")
            params["experiment_id"] = experiment_id
            
        if tool_names:
            tool_names_str = "', '".join(tool_names)
            where_conditions.append(f"s.name IN ('{tool_names_str}')")
            
        if start_time:
            where_conditions.append("ti.timestamp_ms >= :start_time")
            params["start_time"] = start_time
        if end_time:
            where_conditions.append("ti.timestamp_ms <= :end_time")
            params["end_time"] = end_time
        
        where_conditions.append("s.status = 'OK'")
        where_conditions.append("s.end_time_unix_nano IS NOT NULL")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Calculate timezone offset
        offset_ms = 0
        if timezone != 'UTC' and validated_bucket in ["day", "week"]:
            try:
                import pytz
                from datetime import datetime
                tz = pytz.timezone(timezone)
                now = datetime.now(pytz.UTC)
                localized = now.astimezone(tz)
                offset_ms = int(localized.utcoffset().total_seconds() * 1000)
            except:
                offset_ms = 0
        
        # Build time bucket expression
        if validated_bucket == "hour":
            bucket_expr = "(ti.timestamp_ms / 3600000) * 3600000"
        elif validated_bucket == "day":
            bucket_expr = f"((ti.timestamp_ms + {offset_ms}) / 86400000) * 86400000 - {offset_ms}"
        elif validated_bucket == "week":
            bucket_expr = f"((ti.timestamp_ms + {offset_ms}) / 604800000) * 604800000 - {offset_ms}"
        else:
            bucket_expr = "(ti.timestamp_ms / 3600000) * 3600000"
        
        # Query for spans latencies grouped by bucket
        query_sql = text(f"""
            SELECT 
                s.name as tool_name,
                {bucket_expr} as time_bucket,
                (s.end_time_unix_nano - s.start_time_unix_nano) / 1000000.0 as latency_ms
            FROM spans s
            JOIN trace_info ti ON s.trace_id = ti.request_id
            WHERE s.type = 'TOOL' AND {where_clause}
            ORDER BY s.name, time_bucket
        """)
        
        results = session.execute(query_sql, params).fetchall()
        
        # Group execution times by time bucket and tool
        bucket_tool_times = {}
        for row in results:
            bucket = int(row.time_bucket) if row.time_bucket else 0
            key = (bucket, row.tool_name)
            if key not in bucket_tool_times:
                bucket_tool_times[key] = []
            bucket_tool_times[key].append(row.latency_ms)
        
        # Calculate percentiles for each bucket and tool
        def get_percentile(data, p):
            if not data:
                return None
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = f + 1 if f < len(data) - 1 else f
            return data[f] if f == c else data[f] + (k - f) * (data[c] - data[f])
        
        latency_points = []
        for (bucket, tool_name), latencies in sorted(bucket_tool_times.items()):
            sorted_latencies = sorted(latencies)
            
            latency_points.append({
                'tool_name': tool_name,
                'time_bucket': bucket,
                'p50_latency': get_percentile(sorted_latencies, 50),
                'p90_latency': get_percentile(sorted_latencies, 90),
                'p99_latency': get_percentile(sorted_latencies, 99),
                'avg_latency': sum(sorted_latencies) / len(sorted_latencies) if sorted_latencies else None,
            })
        
        return latency_points
    
    return store.execute_query(latency_query)


def get_tool_error_rate_over_time(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    tool_names: Optional[List[str]] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    time_bucket: str = "hour",
    timezone: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get tool error rates over time.
    """
    def error_rate_query(session):
        from sqlalchemy import text
        
        # Calculate timezone offset
        offset_ms = 0
        if timezone != 'UTC' and time_bucket in ["day", "week"]:
            try:
                import pytz
                from datetime import datetime
                tz = pytz.timezone(timezone)
                now = datetime.now(pytz.UTC)
                localized = now.astimezone(tz)
                offset_ms = int(localized.utcoffset().total_seconds() * 1000)
            except:
                offset_ms = 0
        
        # Build WHERE conditions
        where_conditions = []
        params = {}
        
        if experiment_ids:
            experiment_id = experiment_ids[0]
            where_conditions.append("ti.experiment_id = :experiment_id")
            params["experiment_id"] = experiment_id
            
        if tool_names:
            tool_names_str = "', '".join(tool_names)
            where_conditions.append(f"s.name IN ('{tool_names_str}')")
            
        if start_time:
            where_conditions.append("ti.timestamp_ms >= :start_time")
            params["start_time"] = start_time
        if end_time:
            where_conditions.append("ti.timestamp_ms <= :end_time")
            params["end_time"] = end_time
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Build time bucket expression
        if time_bucket == "hour":
            bucket_expr = "(ti.timestamp_ms / 3600000) * 3600000"
        elif time_bucket == "day":
            bucket_expr = f"((ti.timestamp_ms + {offset_ms}) / 86400000) * 86400000 - {offset_ms}"
        elif time_bucket == "week":
            bucket_expr = f"((ti.timestamp_ms + {offset_ms}) / 604800000) * 604800000 - {offset_ms}"
        else:
            bucket_expr = "(ti.timestamp_ms / 3600000) * 3600000"
        
        # Query for tool error rates over time
        query = text(f"""
            SELECT 
                s.name as tool_name,
                {bucket_expr} as time_bucket,
                COUNT(s.span_id) as total_count,
                SUM(CASE WHEN s.status = 'ERROR' THEN 1 ELSE 0 END) as error_count
            FROM spans s
            JOIN trace_info ti ON s.trace_id = ti.request_id
            WHERE s.type = 'TOOL' AND {where_clause}
            GROUP BY s.name, {bucket_expr}
            ORDER BY s.name, time_bucket
        """)
        
        results = session.execute(query, params).fetchall()
        
        return [
            {
                'tool_name': row.tool_name,
                'time_bucket': int(row.time_bucket),
                'total_count': row.total_count,
                'error_count': row.error_count,
                'error_rate': (row.error_count / row.total_count * 100) if row.total_count else 0,
            }
            for row in results
        ]
    
    return store.execute_query(error_rate_query)


# ============= Overall Tools Functions =============

def get_overall_tool_metrics_data(store: SqlAlchemyStore, experiment_ids: List[str], start_time=None, end_time=None) -> Dict[str, Any]:
    """Get overall metrics across all tools.
    
    Args:
        store: SqlAlchemyStore instance
        experiment_ids: List of experiment IDs
        start_time: Start timestamp in ms (optional)
        end_time: End timestamp in ms (optional)
        
    Returns:
        Dict with overall tool metrics
    """
    def overall_metrics_query(session):
        
        # Build where clause for experiments - simplify to avoid parameter issues
        experiment_id = experiment_ids[0] if experiment_ids else "1"
        where_clause = f"ti.experiment_id = '{experiment_id}'"
        params = {}
        
        # Query for overall tool metrics (basic counts and averages)
        query = text(f"""
            SELECT 
                COUNT(DISTINCT ti.request_id) as trace_count,
                COUNT(s.span_id) as invocation_count,
                SUM(CASE WHEN s.status = 'ERROR' THEN 1 ELSE 0 END) as error_count,
                AVG(CASE WHEN s.end_time_unix_nano IS NOT NULL AND s.start_time_unix_nano IS NOT NULL 
                    THEN (s.end_time_unix_nano - s.start_time_unix_nano) / 1000000.0 ELSE NULL END) as avg_latency_ms
            FROM spans s
            JOIN trace_info ti ON s.trace_id = ti.request_id
            WHERE s.type = 'TOOL' AND {where_clause}
        """)
        
        result = session.execute(query).fetchone()
        
        if not result or result.trace_count == 0:
            return {
                'trace_count': 0,
                'invocation_count': 0,
                'error_count': 0,
                'error_rate': 0.0,
                'avg_latency_ms': None,
                'p50_latency': None,
                'p90_latency': None,
                'p99_latency': None
            }
        
        # Get all latencies for percentile calculation
        latency_query = text(f"""
            SELECT (s.end_time_unix_nano - s.start_time_unix_nano) / 1000000.0 as latency_ms
            FROM spans s
            JOIN trace_info ti ON s.trace_id = ti.request_id
            WHERE s.type = 'TOOL' AND s.end_time_unix_nano IS NOT NULL AND s.start_time_unix_nano IS NOT NULL AND {where_clause}
            ORDER BY latency_ms
        """)
        
        latency_results = session.execute(latency_query).fetchall()
        
        if latency_results:
            latencies = [row.latency_ms for row in latency_results]
            p50_latency = latencies[int(len(latencies) * 0.5)]
            p90_latency = latencies[int(len(latencies) * 0.9)]
            p99_latency = latencies[min(int(len(latencies) * 0.99), len(latencies) - 1)]
        else:
            p50_latency = p90_latency = p99_latency = None
        
        error_rate = (result.error_count / result.invocation_count * 100) if result.invocation_count else 0.0
        
        return {
            'trace_count': result.trace_count,
            'invocation_count': result.invocation_count,
            'error_count': result.error_count,
            'error_rate': error_rate,
            'avg_latency_ms': result.avg_latency_ms,
            'p50_latency': p50_latency,
            'p90_latency': p90_latency,
            'p99_latency': p99_latency
        }
    
    return store.execute_query(overall_metrics_query)


def get_overall_tool_volume_over_time(store: SqlAlchemyStore, experiment_ids: List[str], start_time=None, end_time=None, time_bucket="hour"):
    """Get overall tool volume over time across all tools with zero-filling for missing periods using SQLAlchemy."""
    def volume_query(session):
        from sqlalchemy import func, and_
        from mlflow.store.tracking.dbmodels.models import SqlTraceInfo, SqlSpan
        
        # Build WHERE conditions using SQLAlchemy
        filters = [SqlSpan.type == 'TOOL']
        
        if experiment_ids:
            filters.append(SqlTraceInfo.experiment_id.in_(experiment_ids))
            
        if start_time:
            filters.append(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            filters.append(SqlTraceInfo.timestamp_ms <= end_time)
        
        # Get bucket expression and interval based on time_bucket
        offset_ms = 0  # No timezone offset for now
        if time_bucket == "day":
            bucket_expr = func.cast(((SqlTraceInfo.timestamp_ms + offset_ms) / 86400000), Integer) * 86400000 - offset_ms
            interval_ms = 86400000  # 1 day in ms
        elif time_bucket == "week":
            bucket_expr = func.cast(((SqlTraceInfo.timestamp_ms + offset_ms) / 604800000), Integer) * 604800000 - offset_ms
            interval_ms = 604800000  # 1 week in ms
        else:
            bucket_expr = func.cast((SqlTraceInfo.timestamp_ms / 3600000), Integer) * 3600000
            interval_ms = 3600000  # 1 hour in ms
        
        # Get min and max timestamps for the time range to densify
        bounds_query = (
            session.query(
                func.min(bucket_expr).label('min_bucket'),
                func.max(bucket_expr).label('max_bucket')
            )
            .select_from(SqlSpan)
            .join(SqlTraceInfo, SqlSpan.trace_id == SqlTraceInfo.request_id)
            .filter(and_(*filters))
        )
        
        bounds_result = bounds_query.first()
        if not bounds_result or bounds_result.min_bucket is None:
            return []
        
        min_bucket = int(bounds_result.min_bucket)
        max_bucket = int(bounds_result.max_bucket)
        
        # Generate complete time series using Python
        time_buckets = []
        current_bucket = min_bucket
        while current_bucket <= max_bucket:
            time_buckets.append(current_bucket)
            current_bucket += interval_ms
        
        # Get actual data grouped by time bucket
        actual_data_query = (
            session.query(
                bucket_expr.label('time_bucket'),
                func.count(SqlSpan.span_id).label('count')
            )
            .select_from(SqlSpan)
            .join(SqlTraceInfo, SqlSpan.trace_id == SqlTraceInfo.request_id)
            .filter(and_(*filters))
            .group_by(bucket_expr)
            .order_by(bucket_expr)
        )
        
        actual_results = actual_data_query.all()
        
        # Convert actual data to lookup dictionary
        actual_data_dict = {int(row.time_bucket): row.count for row in actual_results}
        
        # Generate complete results with zero-filling
        results = []
        for bucket in time_buckets:
            count = actual_data_dict.get(bucket, 0)
            results.append({
                'time_bucket': bucket,
                'count': count
            })
        
        return results
    
    return store.execute_query(volume_query)


def get_overall_tool_latency_over_time(store: SqlAlchemyStore, experiment_ids: List[str], start_time=None, end_time=None, time_bucket="hour"):
    """Get overall tool latency percentiles over time across all tools."""
    def latency_query(session):
        
        # Build where clause for experiments
        exp_placeholders = ','.join(['?' for _ in experiment_ids])
        where_clause = f"ti.experiment_id IN ({exp_placeholders})"
        params = list(experiment_ids)
        
        # Add time filters
        if start_time:
            where_clause += " AND ti.timestamp_ms >= ?"
            params.append(start_time)
        if end_time:
            where_clause += " AND ti.timestamp_ms <= ?"
            params.append(end_time)
        
        # Get bucket expression based on time_bucket
        if time_bucket == "day":
            offset_ms = 0  # No timezone offset for now
            bucket_expr = f"((ti.timestamp_ms + {offset_ms}) / 86400000) * 86400000 - {offset_ms}"
        elif time_bucket == "week":
            offset_ms = 0  # No timezone offset for now
            bucket_expr = f"((ti.timestamp_ms + {offset_ms}) / 604800000) * 604800000 - {offset_ms}"
        else:
            bucket_expr = "(ti.timestamp_ms / 3600000) * 3600000"
        
        # For now, return empty latency data - we'll implement this later
        return []
    
    return store.execute_query(latency_query)


def get_overall_tool_error_rate_over_time(store: SqlAlchemyStore, experiment_ids: List[str], start_time=None, end_time=None, time_bucket="hour"):
    """Get overall tool error rate over time across all tools."""
    def error_rate_query(session):
        
        # Build where clause for experiments
        exp_placeholders = ','.join(['?' for _ in experiment_ids])
        where_clause = f"ti.experiment_id IN ({exp_placeholders})"
        params = list(experiment_ids)
        
        # Add time filters
        if start_time:
            where_clause += " AND ti.timestamp_ms >= ?"
            params.append(start_time)
        if end_time:
            where_clause += " AND ti.timestamp_ms <= ?"
            params.append(end_time)
        
        # Get bucket expression based on time_bucket
        if time_bucket == "day":
            offset_ms = 0  # No timezone offset for now
            bucket_expr = f"((ti.timestamp_ms + {offset_ms}) / 86400000) * 86400000 - {offset_ms}"
        elif time_bucket == "week":
            offset_ms = 0  # No timezone offset for now
            bucket_expr = f"((ti.timestamp_ms + {offset_ms}) / 604800000) * 604800000 - {offset_ms}"
        else:
            bucket_expr = "(ti.timestamp_ms / 3600000) * 3600000"
        
        # Query for overall tool error rates over time
        query = text(f"""
            SELECT 
                {bucket_expr} as time_bucket,
                COUNT(s.span_id) as total_count,
                SUM(CASE WHEN s.status = 'ERROR' THEN 1 ELSE 0 END) as error_count
            FROM spans s
            JOIN trace_info ti ON s.trace_id = ti.request_id
            WHERE s.type = 'TOOL' AND {where_clause}
            GROUP BY {bucket_expr}
            ORDER BY time_bucket
        """)
        
        results = session.execute(query, params).fetchall()
        
        return [
            {
                'time_bucket': int(row.time_bucket),
                'total_count': row.total_count,
                'error_count': row.error_count,
                'error_rate': (row.error_count / row.total_count * 100) if row.total_count else 0,
            }
            for row in results
        ]
    
    return store.execute_query(error_rate_query)


# ============= Legacy Functions (for backward compatibility) =============

def get_precision_recall_over_time(store, experiment_ids, start_time=None, end_time=None, time_bucket="hour"):
    """Legacy function - will be implemented when we have retrieval metrics."""
    return []

def get_document_usage_over_time(store, experiment_ids, start_time=None, end_time=None, time_bucket="hour"):
    """Legacy function - will be implemented when we have document usage data."""
    return []

def get_retrieval_latency_over_time(store, experiment_ids, start_time=None, end_time=None, time_bucket="hour"):
    """Legacy function - will be implemented when we have retrieval latency data."""
    return []

def get_top_retrieved_documents(store, experiment_ids, start_time=None, end_time=None, limit=10):
    """Legacy function - will be implemented when we have document retrieval data."""
    return []