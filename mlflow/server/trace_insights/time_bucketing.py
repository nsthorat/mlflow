"""
Shared time bucketing utility for MLflow Trace Insights

This module provides consistent time bucketing logic across all insights APIs.
The bucketing logic rounds timestamps to the nearest boundary (hour/day/week).
"""

from sqlalchemy import cast, Integer
from sqlalchemy.sql import ColumnElement
from mlflow.store.tracking.dbmodels.models import SqlTraceInfo
from typing import Literal

TimeBucketType = Literal['hour', 'day', 'week']

def get_time_bucket_expression(time_bucket: TimeBucketType) -> ColumnElement:
    """
    Create SQLAlchemy expression for time bucketing.
    
    This function generates the proper SQL expression to round timestamps
    to the nearest hour, day, or week boundary using integer division.
    
    Args:
        time_bucket: Bucket size - 'hour', 'day', or 'week'
        
    Returns:
        SQLAlchemy expression that groups timestamps into buckets
        
    Examples:
        For hour bucketing: rounds 2025-08-21 14:23:45 -> 2025-08-21 14:00:00
        For day bucketing: rounds 2025-08-21 14:23:45 -> 2025-08-21 00:00:00
        For week bucketing: rounds to nearest Monday 00:00:00
    """
    
    if time_bucket == "hour":
        # Round to nearest hour using integer division: (timestamp_ms / 3600000) * 3600000
        return cast(
            cast(SqlTraceInfo.timestamp_ms / 3600000, Integer) * 3600000,
            Integer
        ).label('time_bucket')
        
    elif time_bucket == "day":
        # Round to nearest day using integer division: (timestamp_ms / 86400000) * 86400000
        return cast(
            cast(SqlTraceInfo.timestamp_ms / 86400000, Integer) * 86400000,
            Integer
        ).label('time_bucket')
        
    elif time_bucket == "week":
        # Round to nearest week using integer division: (timestamp_ms / 604800000) * 604800000
        return cast(
            cast(SqlTraceInfo.timestamp_ms / 604800000, Integer) * 604800000,
            Integer
        ).label('time_bucket')
        
    else:
        raise ValueError(f"Unsupported time_bucket: {time_bucket}. Must be 'hour', 'day', or 'week'")


def get_bucket_size_ms(time_bucket: TimeBucketType) -> int:
    """
    Get the bucket size in milliseconds.
    
    Args:
        time_bucket: Bucket size - 'hour', 'day', or 'week'
        
    Returns:
        Bucket size in milliseconds
    """
    bucket_sizes = {
        'hour': 3600000,    # 1 hour = 3,600,000 ms
        'day': 86400000,    # 1 day = 86,400,000 ms  
        'week': 604800000   # 1 week = 604,800,000 ms
    }
    
    if time_bucket not in bucket_sizes:
        raise ValueError(f"Unsupported time_bucket: {time_bucket}. Must be 'hour', 'day', or 'week'")
        
    return bucket_sizes[time_bucket]


def validate_time_bucket(time_bucket: str) -> TimeBucketType:
    """
    Validate and normalize time bucket parameter.
    
    Args:
        time_bucket: Time bucket string from API request
        
    Returns:
        Validated TimeBucketType
        
    Raises:
        ValueError: If time_bucket is not supported
    """
    if time_bucket not in ['hour', 'day', 'week']:
        raise ValueError(f"Unsupported time_bucket: {time_bucket}. Must be 'hour', 'day', or 'week'")
    
    return time_bucket  # type: ignore