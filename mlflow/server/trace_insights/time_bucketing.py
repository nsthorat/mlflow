"""
Shared time bucketing utility for MLflow Trace Insights

This module provides consistent time bucketing logic across all insights APIs.
The bucketing logic rounds timestamps to the nearest boundary (hour/day/week).
"""

from sqlalchemy import cast, Integer
from sqlalchemy.sql import ColumnElement
from mlflow.store.tracking.dbmodels.models import SqlTraceInfo
from typing import Literal, Optional
from datetime import datetime
import pytz

TimeBucketType = Literal['hour', 'day', 'week']

def get_time_bucket_expression(time_bucket: TimeBucketType, timezone: Optional[str] = None) -> ColumnElement:
    """
    Create SQLAlchemy expression for time bucketing.
    
    This function generates the proper SQL expression to round timestamps
    to the nearest hour, day, or week boundary using integer division.
    
    Args:
        time_bucket: Bucket size - 'hour', 'day', or 'week'
        timezone: IANA timezone name (e.g., 'America/New_York') for timezone-aware bucketing
        
    Returns:
        SQLAlchemy expression that groups timestamps into buckets
        
    Examples:
        For hour bucketing: rounds 2025-08-21 14:23:45 -> 2025-08-21 14:00:00
        For day bucketing: rounds 2025-08-21 14:23:45 -> 2025-08-21 00:00:00
        For week bucketing: rounds to nearest Monday 00:00:00
    """
    
    # Calculate timezone offset in milliseconds if timezone is provided
    offset_ms = 0
    if timezone and time_bucket in ["day", "week"]:
        try:
            tz = pytz.timezone(timezone)
            # Get current UTC offset for this timezone
            # We use a reference time to get the offset
            now = datetime.now(pytz.UTC)
            localized = now.astimezone(tz)
            # Get offset in seconds and convert to milliseconds
            offset_ms = int(localized.utcoffset().total_seconds() * 1000)
        except:
            # If timezone is invalid, fall back to UTC
            offset_ms = 0
    
    if time_bucket == "hour":
        # Round to nearest hour using integer division: (timestamp_ms / 3600000) * 3600000
        # Hours don't need timezone adjustment as they're the same in all timezones
        return cast(
            cast(SqlTraceInfo.timestamp_ms / 3600000, Integer) * 3600000,
            Integer
        ).label('time_bucket')
        
    elif time_bucket == "day":
        # For timezone-aware day bucketing, adjust timestamp before bucketing
        # This ensures days align with local midnight instead of UTC midnight
        adjusted_timestamp = SqlTraceInfo.timestamp_ms + offset_ms
        return cast(
            cast(adjusted_timestamp / 86400000, Integer) * 86400000 - offset_ms,
            Integer
        ).label('time_bucket')
        
    elif time_bucket == "week":
        # For timezone-aware week bucketing, adjust timestamp before bucketing
        # This ensures weeks align with local Monday midnight instead of UTC Monday
        adjusted_timestamp = SqlTraceInfo.timestamp_ms + offset_ms
        return cast(
            cast(adjusted_timestamp / 604800000, Integer) * 604800000 - offset_ms,
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


def get_time_bucket_value(timestamp_ms: int, time_bucket: TimeBucketType, offset_ms: int = 0) -> int:
    """
    Calculate the bucket value for a given timestamp.
    
    This is the Python equivalent of the SQL expression in get_time_bucket_expression.
    
    Args:
        timestamp_ms: Timestamp in milliseconds
        time_bucket: Bucket size - 'hour', 'day', or 'week'
        offset_ms: Timezone offset in milliseconds (for day/week bucketing)
        
    Returns:
        The bucket value (start of the bucket) in milliseconds
    """
    if time_bucket == "hour":
        # Round to nearest hour
        return (timestamp_ms // 3600000) * 3600000
    elif time_bucket == "day":
        # Adjust for timezone, round to day, then adjust back
        adjusted = timestamp_ms + offset_ms
        return (adjusted // 86400000) * 86400000 - offset_ms
    elif time_bucket == "week":
        # Adjust for timezone, round to week, then adjust back
        adjusted = timestamp_ms + offset_ms
        return (adjusted // 604800000) * 604800000 - offset_ms
    else:
        raise ValueError(f"Unsupported time_bucket: {time_bucket}")