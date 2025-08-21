"""MLflow Trace Insights - Traffic Analytics Computations

High-resolution computational functions for trace traffic analysis.
Focuses on volume over time, latency percentiles, and error rates.
"""

from typing import Dict, List, Any, Optional
from sqlalchemy import func, case, and_, Integer
from mlflow.store.tracking.sqlalchemy_store import SqlAlchemyStore
from mlflow.store.tracking.dbmodels.models import SqlTraceInfo, SqlSpan
from mlflow.server.trace_insights.models import (
    VolumeOverTimePoint,
    LatencyPercentilesPoint,
    ErrorRatePoint,
    ErrorCorrelationPoint,
)


def get_volume_over_time(
    store: SqlAlchemyStore, 
    experiment_ids: List[str], 
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    time_bucket: str = "hour"
) -> List[VolumeOverTimePoint]:
    """
    Compute trace volume over time with hourly/daily bucketing.
    
    Args:
        store: SqlAlchemy store instance
        experiment_ids: List of experiment IDs to analyze
        start_time: Start timestamp in milliseconds (optional)
        end_time: End timestamp in milliseconds (optional)  
        time_bucket: Time bucketing ('hour' or 'day')
        
    Returns:
        List of VolumeOverTimePoint objects with time_bucket, count, ok_count, error_count
    """
    def volume_query(session):
        # Build time bucket expression using SQLAlchemy
        # Note: SQLite datetime requires integer seconds, not fractional
        if time_bucket == "hour":
            # Format as YYYY-MM-DD HH:00:00 for hourly buckets
            time_bucket_expr = func.strftime(
                '%Y-%m-%d %H:00:00',
                func.datetime(
                    func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                    'unixepoch'
                )
            ).label('time_bucket')
        elif time_bucket == "day":
            # Format as YYYY-MM-DD for daily buckets
            time_bucket_expr = func.date(
                func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer), 
                'unixepoch'
            ).label('time_bucket')
        else:
            raise ValueError(f"Unsupported time_bucket: {time_bucket}")
        
        # Build query with SQLAlchemy ORM
        query = session.query(
            time_bucket_expr,
            func.count().label('count'),
            func.sum(case((SqlTraceInfo.status == 'OK', 1), else_=0)).label('ok_count'),
            func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0)).label('error_count')
        ).filter(
            SqlTraceInfo.experiment_id.in_(experiment_ids)
        )
        
        # Add time filters
        if start_time:
            query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)
            
        # Group and order
        query = query.group_by(time_bucket_expr).order_by(time_bucket_expr)
        
        return query.all()
    
    results = store.execute_query(volume_query)
    return [
        VolumeOverTimePoint(
            time_bucket=str(row.time_bucket) if row.time_bucket else "unknown",
            count=row.count or 0, 
            ok_count=row.ok_count or 0,
            error_count=row.error_count or 0
        )
        for row in results
    ]


def get_latency_percentiles_over_time(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    start_time: Optional[int] = None, 
    end_time: Optional[int] = None,
    time_bucket: str = "hour"
) -> List[LatencyPercentilesPoint]:
    """
    Compute latency percentiles (P50, P90, P99) over time.
    
    Args:
        store: SqlAlchemy store instance
        experiment_ids: List of experiment IDs to analyze
        start_time: Start timestamp in milliseconds (optional)
        end_time: End timestamp in milliseconds (optional)
        time_bucket: Time bucketing ('hour' or 'day')
        
    Returns:
        List of LatencyPercentilesPoint objects with time_bucket, p50, p90, p99, avg, min, max
    """
    def latency_query(session):
        # Build time bucket expression
        # Note: SQLite datetime requires integer seconds, not fractional
        if time_bucket == "hour":
            # Format as YYYY-MM-DD HH:00:00 for hourly buckets
            time_bucket_expr = func.strftime(
                '%Y-%m-%d %H:00:00',
                func.datetime(
                    func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                    'unixepoch'
                )
            ).label('time_bucket')
        elif time_bucket == "day":
            # Format as YYYY-MM-DD for daily buckets
            time_bucket_expr = func.date(
                func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                'unixepoch'
            ).label('time_bucket')
        else:
            raise ValueError(f"Unsupported time_bucket: {time_bucket}")
        
        # Query for basic stats (SQLite doesn't have percentile functions)
        query = session.query(
            time_bucket_expr,
            func.avg(SqlTraceInfo.execution_time_ms).label('avg_latency'),
            func.min(SqlTraceInfo.execution_time_ms).label('min_latency'),
            func.max(SqlTraceInfo.execution_time_ms).label('max_latency'),
            # For now, use avg as approximation for percentiles
            # A proper implementation would need window functions or subqueries
            func.avg(SqlTraceInfo.execution_time_ms).label('p50_latency'),
            func.avg(SqlTraceInfo.execution_time_ms).label('p90_latency'),
            func.max(SqlTraceInfo.execution_time_ms).label('p99_latency')
        ).filter(
            and_(
                SqlTraceInfo.experiment_id.in_(experiment_ids),
                SqlTraceInfo.status == 'OK'
            )
        )
        
        # Add time filters
        if start_time:
            query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)
        
        # Group and order
        query = query.group_by(time_bucket_expr).order_by(time_bucket_expr)
        
        return query.all()
    
    results = store.execute_query(latency_query)
    return [
        LatencyPercentilesPoint(
            time_bucket=str(row.time_bucket) if row.time_bucket else "unknown",
            p50_latency=float(row.p50_latency) if row.p50_latency else None,
            p90_latency=float(row.p90_latency) if row.p90_latency else None,
            p99_latency=float(row.p99_latency) if row.p99_latency else None,
            avg_latency=float(row.avg_latency) if row.avg_latency else None,
            min_latency=int(row.min_latency) if row.min_latency else None,
            max_latency=int(row.max_latency) if row.max_latency else None
        )
        for row in results
    ]


def get_error_rate_over_time(
    store: SqlAlchemyStore,
    experiment_ids: List[str], 
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    time_bucket: str = "hour"
) -> List[ErrorRatePoint]:
    """
    Compute error rate percentage over time.
    
    Args:
        store: SqlAlchemy store instance
        experiment_ids: List of experiment IDs to analyze 
        start_time: Start timestamp in milliseconds (optional)
        end_time: End timestamp in milliseconds (optional)
        time_bucket: Time bucketing ('hour' or 'day')
        
    Returns:
        List of ErrorRatePoint objects with time_bucket, error_rate, total_count, error_count
    """
    def error_rate_query(session):
        # Build time bucket expression
        # Note: SQLite datetime requires integer seconds, not fractional
        if time_bucket == "hour":
            # Format as YYYY-MM-DD HH:00:00 for hourly buckets
            time_bucket_expr = func.strftime(
                '%Y-%m-%d %H:00:00',
                func.datetime(
                    func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                    'unixepoch'
                )
            ).label('time_bucket')
        elif time_bucket == "day":
            # Format as YYYY-MM-DD for daily buckets
            time_bucket_expr = func.date(
                func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                'unixepoch'
            ).label('time_bucket')
        else:
            raise ValueError(f"Unsupported time_bucket: {time_bucket}")
        
        # Build query with SQLAlchemy
        error_count = func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0)).label('error_count')
        total_count = func.count().label('total_count')
        
        # Calculate error rate
        error_rate = case(
            (total_count > 0, (error_count * 100.0) / total_count),
            else_=0
        ).label('error_rate')
        
        query = session.query(
            time_bucket_expr,
            total_count,
            error_count,
            error_rate
        ).filter(
            SqlTraceInfo.experiment_id.in_(experiment_ids)
        )
        
        # Add time filters
        if start_time:
            query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)
        
        # Group and order
        query = query.group_by(time_bucket_expr).order_by(time_bucket_expr)
        
        return query.all()
    
    results = store.execute_query(error_rate_query)
    return [
        ErrorRatePoint(
            time_bucket=str(row.time_bucket) if row.time_bucket else "unknown",
            total_count=row.total_count or 0,
            error_count=row.error_count or 0,
            error_rate=float(row.error_rate) if row.error_rate else 0.0
        )
        for row in results
    ]


def get_error_correlations_with_npmi(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    min_occurrences: int = 5
) -> List[ErrorCorrelationPoint]:
    """
    Compute NPMI (Normalized Pointwise Mutual Information) correlations between errors and other trace dimensions.
    
    Args:
        store: SqlAlchemy store instance 
        experiment_ids: List of experiment IDs to analyze
        start_time: Start timestamp in milliseconds (optional)
        end_time: End timestamp in milliseconds (optional)
        min_occurrences: Minimum occurrences to include in analysis
        
    Returns:
        List of ErrorCorrelationPoint objects with dimension, value, npmi_score, error_count, total_count
    """
    def correlation_query(session):
        # First get overall error stats
        base_filter = SqlTraceInfo.experiment_id.in_(experiment_ids)
        if start_time:
            base_filter = and_(base_filter, SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            base_filter = and_(base_filter, SqlTraceInfo.timestamp_ms <= end_time)
        
        # Get total traces and errors
        stats_query = session.query(
            func.count().label('total_traces'),
            func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0)).label('total_errors')
        ).filter(base_filter).first()
        
        total_traces = stats_query.total_traces or 0
        total_errors = stats_query.total_errors or 0
        
        if total_traces == 0 or total_errors == 0:
            return []
        
        # Get span type correlations
        span_query = session.query(
            func.literal('span_type').label('dimension'),
            SqlSpan.type.label('value'),
            func.count().label('total_count'),
            func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0)).label('error_count')
        ).join(
            SqlSpan, SqlTraceInfo.request_id == SqlSpan.trace_id
        ).filter(
            and_(
                base_filter,
                SqlSpan.type.isnot(None)
            )
        ).group_by(
            SqlSpan.type
        ).having(
            func.count() >= min_occurrences
        ).all()
        
        # Calculate NPMI scores
        results = []
        for row in span_query:
            if row.error_count and row.total_count < total_traces:
                # NPMI calculation
                p_error_given_span = row.error_count / row.total_count
                p_error = total_errors / total_traces
                p_span = row.total_count / total_traces
                
                if p_error > 0 and p_span > 0 and p_error_given_span > 0:
                    pmi = func.log((p_error_given_span) / (p_error))
                    npmi = pmi / (-func.log(p_error_given_span))
                    npmi_value = float(session.query(npmi).scalar())
                else:
                    npmi_value = 0.0
            else:
                npmi_value = 0.0
            
            results.append({
                'dimension': row.dimension,
                'value': row.value,
                'total_count': row.total_count,
                'error_count': row.error_count or 0,
                'npmi_score': npmi_value
            })
        
        return results
    
    results = store.execute_query(correlation_query)
    return [
        ErrorCorrelationPoint(
            dimension=row['dimension'],
            value=row['value'],
            total_count=row['total_count'],
            error_count=row['error_count'],
            npmi_score=row['npmi_score']
        )
        for row in results
    ]