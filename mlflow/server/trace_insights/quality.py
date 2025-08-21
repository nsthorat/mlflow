"""MLflow Trace Insights - Quality Analytics Computations

High-resolution computational functions for quality metrics analysis.
All functions focus on what they compute (e.g., token usage over time, feedback sentiment analysis).
"""

from typing import List, Optional, Dict, Any, Callable, Union
from pydantic import BaseModel
from sqlalchemy import func, case, text, Integer
from sqlalchemy.orm import Session

from mlflow.store.tracking.sqlalchemy_store import SqlAlchemyStore
from mlflow.store.tracking.dbmodels.models import SqlTraceInfo, SqlTraceTag


class TokenUsageOverTimePoint(BaseModel):
    """High-resolution data point for token usage over time."""
    time_bucket: str
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    average_input_tokens: float
    average_output_tokens: float


class FeedbackSentimentOverTimePoint(BaseModel):
    """High-resolution data point for feedback sentiment over time."""
    time_bucket: str
    positive_count: int
    negative_count: int
    neutral_count: int
    total_feedback: int
    sentiment_score: float  # Range: -1 (all negative) to 1 (all positive)


class QualityScoresOverTimePoint(BaseModel):
    """High-resolution data point for quality scores over time."""
    time_bucket: str
    average_quality_score: float
    min_quality_score: float
    max_quality_score: float
    total_scored_traces: int


class ModelPerformanceByVersionPoint(BaseModel):
    """High-resolution data point for model performance by version."""
    model_version: str
    total_traces: int
    average_latency_ms: float
    error_rate: float
    average_quality_score: Optional[float]
    total_tokens: int


class TokenUsageOverTimeResponse(BaseModel):
    """Response model for token usage over time endpoint."""
    token_usage_over_time: List[TokenUsageOverTimePoint]


class FeedbackSentimentOverTimeResponse(BaseModel):
    """Response model for feedback sentiment over time endpoint."""
    feedback_sentiment_over_time: List[FeedbackSentimentOverTimePoint]


class QualityScoresOverTimeResponse(BaseModel):
    """Response model for quality scores over time endpoint."""
    quality_scores_over_time: List[QualityScoresOverTimePoint]


class ModelPerformanceByVersionResponse(BaseModel):
    """Response model for model performance by version endpoint."""
    model_performance_by_version: List[ModelPerformanceByVersionPoint]


def get_token_usage_over_time(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    time_bucket: str = "hour"
) -> List[TokenUsageOverTimePoint]:
    """
    Compute token usage metrics over time with high-resolution bucketing.
    
    Args:
        store: SQLAlchemy store instance
        experiment_ids: List of experiment IDs to analyze
        start_time: Optional start timestamp (milliseconds)
        end_time: Optional end timestamp (milliseconds)
        time_bucket: Time bucketing ('hour', 'day', 'week')
    
    Returns:
        List of token usage data points over time
    """
    def token_usage_query(session: Session) -> List[Dict[str, Any]]:
        # Time bucket expression based on granularity
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
        else:  # week
            time_bucket_expr = func.strftime(
                '%Y-W%W',
                func.datetime(
                    func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                    'unixepoch'
                )
            ).label('time_bucket')

        # Build base query
        query = session.query(
            time_bucket_expr,
            func.sum(
                func.cast(
                    func.json_extract(SqlTraceInfo.request_metadata, '$.input_tokens'), 
                    Integer
                )
            ).label('total_input_tokens'),
            func.sum(
                func.cast(
                    func.json_extract(SqlTraceInfo.request_metadata, '$.output_tokens'), 
                    Integer
                )
            ).label('total_output_tokens'),
            func.sum(
                func.cast(
                    func.json_extract(SqlTraceInfo.request_metadata, '$.input_tokens'), 
                    Integer
                ) +
                func.cast(
                    func.json_extract(SqlTraceInfo.request_metadata, '$.output_tokens'), 
                    Integer
                )
            ).label('total_tokens'),
            func.avg(
                func.cast(
                    func.json_extract(SqlTraceInfo.request_metadata, '$.input_tokens'), 
                    Integer
                )
            ).label('average_input_tokens'),
            func.avg(
                func.cast(
                    func.json_extract(SqlTraceInfo.request_metadata, '$.output_tokens'), 
                    Integer
                )
            ).label('average_output_tokens')
        ).filter(
            SqlTraceInfo.experiment_id.in_(experiment_ids)
        )

        # Apply time filters
        if start_time:
            query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)

        # Group by time bucket and execute
        results = query.group_by(time_bucket_expr).order_by(time_bucket_expr).all()
        
        return [dict(row._mapping) for row in results]

    # Execute query using store's execute_query method
    raw_results = store.execute_query(query_func=token_usage_query)
    
    # Convert to Pydantic models
    token_usage_points = []
    for row in raw_results:
        token_usage_points.append(TokenUsageOverTimePoint(
            time_bucket=row['time_bucket'],
            total_input_tokens=row['total_input_tokens'] or 0,
            total_output_tokens=row['total_output_tokens'] or 0,
            total_tokens=row['total_tokens'] or 0,
            average_input_tokens=row['average_input_tokens'] or 0.0,
            average_output_tokens=row['average_output_tokens'] or 0.0
        ))
    
    return token_usage_points


def get_feedback_sentiment_over_time(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    time_bucket: str = "hour"
) -> List[FeedbackSentimentOverTimePoint]:
    """
    Compute feedback sentiment analysis over time with high-resolution bucketing.
    
    Args:
        store: SQLAlchemy store instance
        experiment_ids: List of experiment IDs to analyze
        start_time: Optional start timestamp (milliseconds)
        end_time: Optional end timestamp (milliseconds)
        time_bucket: Time bucketing ('hour', 'day', 'week')
    
    Returns:
        List of feedback sentiment data points over time
    """
    def feedback_sentiment_query(session: Session) -> List[Dict[str, Any]]:
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
        else:  # week
            time_bucket_expr = func.strftime(
                '%Y-W%W',
                func.datetime(
                    func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                    'unixepoch'
                )
            ).label('time_bucket')

        # Sentiment analysis from trace tags (assumes feedback stored as tags)
        query = session.query(
            time_bucket_expr,
            func.sum(
                case(
                    (func.json_extract(SqlTraceTag.value, '$.sentiment') == 'positive', 1),
                    else_=0
                )
            ).label('positive_count'),
            func.sum(
                case(
                    (func.json_extract(SqlTraceTag.value, '$.sentiment') == 'negative', 1),
                    else_=0
                )
            ).label('negative_count'),
            func.sum(
                case(
                    (func.json_extract(SqlTraceTag.value, '$.sentiment') == 'neutral', 1),
                    else_=0
                )
            ).label('neutral_count'),
            func.count(SqlTraceTag.key).label('total_feedback'),
            func.avg(
                func.cast(
                    func.json_extract(SqlTraceTag.value, '$.score'), 
                    Integer
                )
            ).label('sentiment_score')
        ).join(
            SqlTraceInfo, SqlTraceInfo.request_id == SqlTraceTag.key
        ).filter(
            SqlTraceInfo.experiment_id.in_(experiment_ids),
            SqlTraceTag.key.like('feedback_%')
        )

        # Apply time filters
        if start_time:
            query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)

        # Group by time bucket and execute
        results = query.group_by(time_bucket_expr).order_by(time_bucket_expr).all()
        
        return [dict(row._mapping) for row in results]

    # Execute query using store's execute_query method
    raw_results = store.execute_query(query_func=feedback_sentiment_query)
    
    # Convert to Pydantic models
    sentiment_points = []
    for row in raw_results:
        # Calculate sentiment score (-1 to 1 range)
        total = row['total_feedback'] or 0
        if total > 0:
            positive = row['positive_count'] or 0
            negative = row['negative_count'] or 0
            sentiment_score = (positive - negative) / total
        else:
            sentiment_score = 0.0
            
        sentiment_points.append(FeedbackSentimentOverTimePoint(
            time_bucket=row['time_bucket'],
            positive_count=row['positive_count'] or 0,
            negative_count=row['negative_count'] or 0,
            neutral_count=row['neutral_count'] or 0,
            total_feedback=total,
            sentiment_score=sentiment_score
        ))
    
    return sentiment_points


def get_quality_scores_over_time(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    time_bucket: str = "hour"
) -> List[QualityScoresOverTimePoint]:
    """
    Compute quality scores over time with high-resolution bucketing.
    
    Args:
        store: SQLAlchemy store instance
        experiment_ids: List of experiment IDs to analyze
        start_time: Optional start timestamp (milliseconds)
        end_time: Optional end timestamp (milliseconds)
        time_bucket: Time bucketing ('hour', 'day', 'week')
    
    Returns:
        List of quality score data points over time
    """
    def quality_scores_query(session: Session) -> List[Dict[str, Any]]:
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
        else:  # week
            time_bucket_expr = func.strftime(
                '%Y-W%W',
                func.datetime(
                    func.cast(SqlTraceInfo.timestamp_ms / 1000, type_=Integer),
                    'unixepoch'
                )
            ).label('time_bucket')

        # Quality scores from request metadata
        query = session.query(
            time_bucket_expr,
            func.avg(
                func.cast(
                    func.json_extract(SqlTraceInfo.request_metadata, '$.quality_score'), 
                    Integer
                )
            ).label('average_quality_score'),
            func.min(
                func.cast(
                    func.json_extract(SqlTraceInfo.request_metadata, '$.quality_score'), 
                    Integer
                )
            ).label('min_quality_score'),
            func.max(
                func.cast(
                    func.json_extract(SqlTraceInfo.request_metadata, '$.quality_score'), 
                    Integer
                )
            ).label('max_quality_score'),
            func.count(SqlTraceInfo.request_id).label('total_scored_traces')
        ).filter(
            SqlTraceInfo.experiment_id.in_(experiment_ids),
            func.json_extract(SqlTraceInfo.request_metadata, '$.quality_score').isnot(None)
        )

        # Apply time filters
        if start_time:
            query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)

        # Group by time bucket and execute
        results = query.group_by(time_bucket_expr).order_by(time_bucket_expr).all()
        
        return [dict(row._mapping) for row in results]

    # Execute query using store's execute_query method
    raw_results = store.execute_query(query_func=quality_scores_query)
    
    # Convert to Pydantic models
    quality_points = []
    for row in raw_results:
        quality_points.append(QualityScoresOverTimePoint(
            time_bucket=row['time_bucket'],
            average_quality_score=row['average_quality_score'] or 0.0,
            min_quality_score=row['min_quality_score'] or 0.0,
            max_quality_score=row['max_quality_score'] or 0.0,
            total_scored_traces=row['total_scored_traces'] or 0
        ))
    
    return quality_points


def get_model_performance_by_version(
    store: SqlAlchemyStore,
    experiment_ids: List[str],
    start_time: Optional[int] = None,
    end_time: Optional[int] = None
) -> List[ModelPerformanceByVersionPoint]:
    """
    Compute model performance metrics by version.
    
    Args:
        store: SQLAlchemy store instance
        experiment_ids: List of experiment IDs to analyze
        start_time: Optional start timestamp (milliseconds)
        end_time: Optional end timestamp (milliseconds)
    
    Returns:
        List of model performance data points by version
    """
    def model_performance_query(session: Session) -> List[Dict[str, Any]]:
        # Model performance analysis by version
        query = session.query(
            func.json_extract(SqlTraceInfo.request_metadata, '$.model_version').label('model_version'),
            func.count(SqlTraceInfo.request_id).label('total_traces'),
            func.avg(SqlTraceInfo.execution_time_ms).label('average_latency_ms'),
            (func.sum(
                case(
                    (SqlTraceInfo.status == 'ERROR', 1),
                    else_=0
                )
            ).cast(float) / func.count(SqlTraceInfo.request_id) * 100).label('error_rate'),
            func.avg(
                func.cast(
                    func.json_extract(SqlTraceInfo.request_metadata, '$.quality_score'), 
                    Integer
                )
            ).label('average_quality_score'),
            func.sum(
                func.cast(
                    func.json_extract(SqlTraceInfo.request_metadata, '$.input_tokens'), 
                    Integer
                ) +
                func.cast(
                    func.json_extract(SqlTraceInfo.request_metadata, '$.output_tokens'), 
                    Integer
                )
            ).label('total_tokens')
        ).filter(
            SqlTraceInfo.experiment_id.in_(experiment_ids),
            func.json_extract(SqlTraceInfo.request_metadata, '$.model_version').isnot(None)
        )

        # Apply time filters
        if start_time:
            query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
        if end_time:
            query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)

        # Group by model version and execute
        results = query.group_by(
            func.json_extract(SqlTraceInfo.request_metadata, '$.model_version')
        ).order_by(
            func.json_extract(SqlTraceInfo.request_metadata, '$.model_version')
        ).all()
        
        return [dict(row._mapping) for row in results]

    # Execute query using store's execute_query method
    raw_results = store.execute_query(query_func=model_performance_query)
    
    # Convert to Pydantic models
    performance_points = []
    for row in raw_results:
        performance_points.append(ModelPerformanceByVersionPoint(
            model_version=row['model_version'] or 'unknown',
            total_traces=row['total_traces'] or 0,
            average_latency_ms=row['average_latency_ms'] or 0.0,
            error_rate=row['error_rate'] or 0.0,
            average_quality_score=row['average_quality_score'],
            total_tokens=row['total_tokens'] or 0
        ))
    
    return performance_points