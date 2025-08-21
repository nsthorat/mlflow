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
)
from pydantic import BaseModel
from typing import Union


# ============= Data Models =============

class ToolInfo(BaseModel):
    """Information about a discovered tool."""
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
    tools: List[ToolInfo]
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
) -> List[ToolInfo]:
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
            
            tools.append(ToolInfo(
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
    time_bucket: str = "hour"
) -> List[ToolVolumePoint]:
    """
    Get tool call volume over time with time bucketing.
    """
    def volume_query(session):
        # Time bucket expression
        if time_bucket == "hour":
            time_bucket_expr = func.strftime(
                '%Y-%m-%d %H:00:00',
                func.datetime(
                    func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                    'unixepoch'
                )
            ).label('time_bucket')
        elif time_bucket == "day":
            time_bucket_expr = func.strftime(
                '%Y-%m-%d',
                func.datetime(
                    func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                    'unixepoch'
                )
            ).label('time_bucket')
        else:
            time_bucket_expr = func.strftime(
                '%Y-%m-%d %H:00:00',
                func.datetime(
                    func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                    'unixepoch'
                )
            ).label('time_bucket')
        
        query = session.query(
            time_bucket_expr,
            SqlTraceTag.value.label('tool_name'),
            func.count(SqlTraceInfo.request_id).label('call_count'),
            func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0)).label('error_count'),
            func.sum(case((SqlTraceInfo.status == 'OK', 1), else_=0)).label('success_count'),
        ).join(
            SqlTraceInfo,
            SqlTraceTag.request_id == SqlTraceInfo.request_id
        ).filter(
            SqlTraceTag.key == 'mlflow.traceName'
        )
        
        # Filters
        if experiment_ids:
            query = query.filter(SqlTraceInfo.experiment_id.in_(experiment_ids))
        if tool_names:
            query = query.filter(SqlTraceTag.value.in_(tool_names))
        if start_time:
            query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)
        
        query = query.group_by('time_bucket', SqlTraceTag.value)
        query = query.order_by('time_bucket', SqlTraceTag.value)
        
        results = query.all()
        
        return [
            ToolVolumePoint(
                time_bucket=row.time_bucket,
                tool_name=row.tool_name,
                call_count=row.call_count or 0,
                error_count=row.error_count or 0,
                success_count=row.success_count or 0,
            )
            for row in results
        ]
    
    return store.execute_query(volume_query)


def get_tool_latency_over_time(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    tool_names: Optional[List[str]] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    time_bucket: str = "hour"
) -> List[ToolLatencyPoint]:
    """
    Get tool latency percentiles over time.
    Uses SQLite-compatible percentile calculation.
    """
    def latency_query(session):
        # Build the SQL query for time-bucketed latency data
        sql = """
        SELECT
            CASE
                WHEN :time_bucket = 'hour' THEN
                    strftime('%Y-%m-%d %H:00:00', datetime(s.start_time_unix_nano / 1000000000, 'unixepoch'))
                ELSE
                    strftime('%Y-%m-%d', datetime(s.start_time_unix_nano / 1000000000, 'unixepoch'))
            END as time_bucket,
            s.name as tool_name,
            AVG((s.end_time_unix_nano - s.start_time_unix_nano) / 1000000.0) as avg_latency_ms
        FROM spans s
        WHERE s.type = 'TOOL'
        """
        
        # Add filters
        if experiment_ids:
            exp_ids_str = ','.join([f"'{exp_id}'" for exp_id in experiment_ids])
            sql += f" AND s.experiment_id IN ({exp_ids_str})"
        
        if tool_names:
            tool_names_str = ','.join([f"'{name}'" for name in tool_names])
            sql += f" AND s.name IN ({tool_names_str})"
        
        if start_time:
            sql += f" AND s.start_time_unix_nano >= {start_time * 1000000}"
        if end_time:
            sql += f" AND s.start_time_unix_nano <= {end_time * 1000000}"
        
        sql += """
        GROUP BY time_bucket, s.name
        ORDER BY time_bucket, s.name
        """
        
        # Execute the aggregation query
        result = session.execute(text(sql), {'time_bucket': time_bucket})
        rows = result.fetchall()
        
        # For each time bucket and tool, calculate percentiles
        latency_points = []
        for row in rows:
            # Get all latencies for this time bucket and tool
            percentile_sql = """
            SELECT (end_time_unix_nano - start_time_unix_nano) / 1000000.0 as latency_ms
            FROM spans
            WHERE type = 'TOOL' AND name = :tool_name
            """
            
            # Add time bucket filter
            if time_bucket == 'hour':
                percentile_sql += """
                AND strftime('%Y-%m-%d %H:00:00', datetime(start_time_unix_nano / 1000000000, 'unixepoch')) = :time_bucket
                """
            else:
                percentile_sql += """
                AND strftime('%Y-%m-%d', datetime(start_time_unix_nano / 1000000000, 'unixepoch')) = :time_bucket
                """
            
            if experiment_ids:
                exp_ids_str = ','.join([f"'{exp_id}'" for exp_id in experiment_ids])
                percentile_sql += f" AND experiment_id IN ({exp_ids_str})"
            
            if start_time:
                percentile_sql += f" AND start_time_unix_nano >= {start_time * 1000000}"
            if end_time:
                percentile_sql += f" AND start_time_unix_nano <= {end_time * 1000000}"
            
            percentile_sql += " ORDER BY latency_ms"
            
            latencies_result = session.execute(
                text(percentile_sql), 
                {'tool_name': row.tool_name, 'time_bucket': row.time_bucket}
            )
            latencies = [l[0] for l in latencies_result.fetchall() if l[0] is not None]
            
            # Calculate percentiles
            if latencies:
                n = len(latencies)
                p50 = latencies[int(n * 0.5)] if n > 0 else 0
                p90 = latencies[int(n * 0.9)] if n > 0 else 0
                p99 = latencies[min(int(n * 0.99), n-1)] if n > 0 else 0
            else:
                p50 = p90 = p99 = 0
            
            latency_points.append(ToolLatencyPoint(
                time_bucket=row.time_bucket,
                tool_name=row.tool_name,
                p50_latency_ms=float(p50),
                p90_latency_ms=float(p90),
                p99_latency_ms=float(p99),
                avg_latency_ms=float(row.avg_latency_ms or 0),
            ))
        
        return latency_points
    
    return store.execute_query(latency_query)


def get_tool_error_rate_over_time(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    tool_names: Optional[List[str]] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    time_bucket: str = "hour"
) -> List[ToolErrorRatePoint]:
    """
    Get tool error rates over time.
    """
    def error_rate_query(session):
        # Time bucket expression
        if time_bucket == "hour":
            time_bucket_expr = func.strftime(
                '%Y-%m-%d %H:00:00',
                func.datetime(
                    func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                    'unixepoch'
                )
            ).label('time_bucket')
        else:
            time_bucket_expr = func.strftime(
                '%Y-%m-%d',
                func.datetime(
                    func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                    'unixepoch'
                )
            ).label('time_bucket')
        
        query = session.query(
            time_bucket_expr,
            SqlTraceTag.value.label('tool_name'),
            func.count(SqlTraceInfo.request_id).label('total_count'),
            func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0)).label('error_count'),
        ).join(
            SqlTraceInfo,
            SqlTraceTag.request_id == SqlTraceInfo.request_id
        ).filter(
            SqlTraceTag.key == 'mlflow.traceName'
        )
        
        # Filters
        if experiment_ids:
            query = query.filter(SqlTraceInfo.experiment_id.in_(experiment_ids))
        if tool_names:
            query = query.filter(SqlTraceTag.value.in_(tool_names))
        if start_time:
            query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)
        
        query = query.group_by('time_bucket', SqlTraceTag.value)
        query = query.order_by('time_bucket', SqlTraceTag.value)
        
        results = query.all()
        
        return [
            ToolErrorRatePoint(
                time_bucket=row.time_bucket,
                tool_name=row.tool_name,
                error_count=row.error_count or 0,
                total_count=row.total_count or 0,
                error_rate=float(row.error_count or 0) / float(row.total_count) if row.total_count else 0,
            )
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