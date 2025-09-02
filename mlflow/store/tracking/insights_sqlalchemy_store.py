"""
SQLAlchemy implementation of the insights store.

This module provides insights analytics using SQLAlchemy queries
for better performance and flexibility compared to REST API calls.
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, func, and_, or_, case, text
from sqlalchemy.orm import Session

from mlflow.store.tracking.sqlalchemy_store import SqlAlchemyStore
from mlflow.store.tracking.insights_abstract_store import InsightsAbstractStore
from mlflow.store.tracking.dbmodels.models import (
    SqlTraceInfo, 
    SqlTraceTag,
    SqlAssessments,
    SqlSpan
)
from mlflow.exceptions import MlflowException
from mlflow.protos.databricks_pb2 import INVALID_PARAMETER_VALUE


class InsightsSqlAlchemyStore(InsightsAbstractStore, SqlAlchemyStore):
    """SQLAlchemy implementation of the insights store.
    
    This class extends both InsightsAbstractStore and SqlAlchemyStore to provide 
    insights analytics using direct SQL queries against the MLflow database.
    Since InsightsAbstractStore now extends AbstractStore, we put it first
    in the inheritance order to ensure proper method resolution order (MRO).
    """
    
    def __init__(self, db_uri, default_artifact_root):
        """Initialize the SQLAlchemy insights store.
        
        Args:
            db_uri: The database URI (e.g., 'sqlite:///mlflow.db')
            default_artifact_root: Default location for artifacts
        """
        # Call parent SqlAlchemyStore __init__
        super().__init__(db_uri, default_artifact_root)
        self._experiment_ids = None
    
    def _get_experiment_ids(self) -> List[str]:
        """Get experiment IDs from environment or configuration.
        
        Returns:
            List of experiment IDs to analyze
        """
        if self._experiment_ids is None:
            # Try to get from environment variable
            exp_ids = os.environ.get('MLFLOW_EXPERIMENT_IDS', '')
            if exp_ids:
                self._experiment_ids = [e.strip() for e in exp_ids.split(',')]
            else:
                # Default to experiment 0 for now
                self._experiment_ids = ['0']
        return self._experiment_ids
    
    # Traffic & Cost Methods
    
    def get_traffic_volume(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_bucket: str = 'hour',
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get trace volume statistics using SQLAlchemy queries."""
        experiment_ids = self._get_experiment_ids()
        
        with self.ManagedSessionMaker() as session:
            # Build base query
            query = session.query(SqlTraceInfo)
            
            # Filter by experiment IDs
            if experiment_ids:
                query = query.filter(SqlTraceInfo.experiment_id.in_(
                    [int(eid) for eid in experiment_ids]
                ))
            
            # Apply time filters
            if start_time:
                query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
            if end_time:
                query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)
            
            # Get summary statistics
            summary_query = query.with_entities(
                func.count().label('count'),
                func.sum(case((SqlTraceInfo.status == 'OK', 1), else_=0)).label('ok_count'),
                func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0)).label('error_count')
            ).first()
            
            # Build time bucket expression based on database dialect
            dialect = self._get_dialect()
            if dialect == 'sqlite':
                # SQLite time bucketing
                if time_bucket == 'hour':
                    bucket_expr = func.strftime('%Y-%m-%d %H:00:00', 
                                               func.datetime(SqlTraceInfo.timestamp_ms / 1000, 'unixepoch'))
                elif time_bucket == 'day':
                    bucket_expr = func.strftime('%Y-%m-%d', 
                                               func.datetime(SqlTraceInfo.timestamp_ms / 1000, 'unixepoch'))
                elif time_bucket == 'week':
                    bucket_expr = func.strftime('%Y-%W', 
                                               func.datetime(SqlTraceInfo.timestamp_ms / 1000, 'unixepoch'))
                else:
                    bucket_expr = func.strftime('%Y-%m-%d %H:00:00', 
                                               func.datetime(SqlTraceInfo.timestamp_ms / 1000, 'unixepoch'))
            else:
                # PostgreSQL/MySQL time bucketing
                if time_bucket == 'hour':
                    bucket_expr = func.date_trunc('hour', 
                                                 func.to_timestamp(SqlTraceInfo.timestamp_ms / 1000))
                elif time_bucket == 'day':
                    bucket_expr = func.date_trunc('day', 
                                                 func.to_timestamp(SqlTraceInfo.timestamp_ms / 1000))
                elif time_bucket == 'week':
                    bucket_expr = func.date_trunc('week', 
                                                 func.to_timestamp(SqlTraceInfo.timestamp_ms / 1000))
                else:
                    bucket_expr = func.date_trunc('hour', 
                                                 func.to_timestamp(SqlTraceInfo.timestamp_ms / 1000))
            
            # Get time series data
            time_series_query = query.with_entities(
                bucket_expr.label('time_bucket'),
                func.count().label('count'),
                func.sum(case((SqlTraceInfo.status == 'OK', 1), else_=0)).label('ok_count'),
                func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0)).label('error_count')
            ).group_by('time_bucket').order_by('time_bucket').all()
            
            # Format response
            return {
                'summary': {
                    'count': summary_query.count or 0 if summary_query else 0,
                    'ok_count': summary_query.ok_count or 0 if summary_query else 0,
                    'error_count': summary_query.error_count or 0 if summary_query else 0
                },
                'time_series': [
                    {
                        'time_bucket': int(row.time_bucket.timestamp() * 1000) if hasattr(row.time_bucket, 'timestamp') else 0,
                        'count': row.count or 0,
                        'ok_count': row.ok_count or 0,
                        'error_count': row.error_count or 0
                    }
                    for row in time_series_query
                ] if time_series_query else []
            }
    
    def get_traffic_latency(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_bucket: str = 'hour',
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get latency percentile statistics using SQLAlchemy queries."""
        experiment_ids = self._get_experiment_ids()
        
        with self.ManagedSessionMaker() as session:
            # Build base query for successful traces
            query = session.query(SqlTraceInfo).filter(
                SqlTraceInfo.status == 'OK',
                SqlTraceInfo.execution_time_ms.isnot(None)
            )
            
            # Filter by experiment IDs
            if experiment_ids:
                query = query.filter(SqlTraceInfo.experiment_id.in_(
                    [int(eid) for eid in experiment_ids]
                ))
            
            # Apply time filters
            if start_time:
                query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
            if end_time:
                query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)
            
            # Get all execution times for percentile calculation
            execution_times = [row.execution_time_ms for row in query.all()]
            
            if execution_times:
                # Calculate percentiles
                sorted_times = sorted(execution_times)
                count = len(sorted_times)
                p50 = sorted_times[int(count * 0.5)]
                p95 = sorted_times[int(count * 0.95)]
                p99 = sorted_times[int(count * 0.99)]
                avg_latency = sum(sorted_times) / count
            else:
                p50 = p95 = p99 = avg_latency = None
                count = 0
            
            # For time series, we'd need to implement percentile calculations per bucket
            # For now, return empty time series
            return {
                'summary': {
                    'p50': p50,
                    'p95': p95,
                    'p99': p99,
                    'avg_latency_ms': avg_latency,
                    'count': count
                },
                'time_series': []
            }
    
    def get_traffic_errors(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_bucket: str = 'hour',
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get error statistics using SQLAlchemy queries."""
        experiment_ids = self._get_experiment_ids()
        
        with self.ManagedSessionMaker() as session:
            # Build base query
            query = session.query(SqlTraceInfo)
            
            # Filter by experiment IDs
            if experiment_ids:
                query = query.filter(SqlTraceInfo.experiment_id.in_(
                    [int(eid) for eid in experiment_ids]
                ))
            
            # Apply time filters
            if start_time:
                query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
            if end_time:
                query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)
            
            # Get error summary
            summary_query = query.with_entities(
                func.count().label('total_count'),
                func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0)).label('error_count')
            ).first()
            
            total_count = summary_query.total_count or 0 if summary_query else 0
            error_count = summary_query.error_count or 0 if summary_query else 0
            error_rate = (error_count / total_count * 100) if total_count > 0 else 0.0
            
            # For time series, simplified for now
            return {
                'summary': {
                    'total_count': total_count,
                    'error_count': error_count,
                    'error_rate': error_rate
                },
                'time_series': []
            }
    
    # Assessment Methods
    
    def discover_assessments(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        min_count: int = 1
    ) -> List[Dict[str, Any]]:
        """Discover assessments using SQLAlchemy queries."""
        experiment_ids = self._get_experiment_ids()
        
        with self.ManagedSessionMaker() as session:
            # Query assessments joined with traces
            query = session.query(
                SqlAssessments.name,
                func.count(func.distinct(SqlAssessments.trace_id)).label('trace_count')
            ).join(
                SqlTraceInfo,
                SqlAssessments.trace_id == SqlTraceInfo.request_id
            )
            
            # Filter by experiment IDs
            if experiment_ids:
                query = query.filter(SqlTraceInfo.experiment_id.in_(
                    [int(eid) for eid in experiment_ids]
                ))
            
            # Apply time filters
            if start_time:
                query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
            if end_time:
                query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)
            
            # Group by assessment name and filter by min_count
            results = query.group_by(SqlAssessments.name).having(
                func.count(func.distinct(SqlAssessments.trace_id)) >= min_count
            ).order_by(func.count(func.distinct(SqlAssessments.trace_id)).desc()).all()
            
            return [
                {
                    'assessment_name': row.name,
                    'trace_count': row.trace_count
                }
                for row in results
            ]
    
    def get_assessment_metrics(
        self,
        assessment_name: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_bucket: str = 'hour',
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get assessment metrics - TODO: Implement detailed metrics."""
        return {'summary': {}, 'time_series': []}
    
    # Tool Methods
    
    def discover_tools(
        self,
        experiment_ids: List[str],
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        min_count: int = 1
    ) -> List[Dict[str, Any]]:
        """Discover tools used in traces using SQLAlchemy queries."""
        
        with self.ManagedSessionMaker() as session:
            # Query trace tags for tool information
            query = session.query(
                SqlTraceTag.value.label('tool_name'),
                func.count(func.distinct(SqlTraceTag.trace_id)).label('trace_count')
            ).join(
                SqlTraceInfo,
                SqlTraceTag.trace_id == SqlTraceInfo.request_id
            ).filter(
                SqlTraceTag.key == 'mlflow.tool'
            )
            
            # Filter by experiment IDs
            if experiment_ids:
                query = query.filter(SqlTraceInfo.experiment_id.in_(
                    [int(eid) for eid in experiment_ids]
                ))
            
            # Apply time filters
            if start_time:
                query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
            if end_time:
                query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)
            
            # Group by tool name and filter by min_count
            results = query.group_by(SqlTraceTag.value).having(
                func.count(func.distinct(SqlTraceTag.trace_id)) >= min_count
            ).order_by(func.count(func.distinct(SqlTraceTag.trace_id)).desc()).all()
            
            # Calculate total traces for percentage
            total_traces_query = session.query(
                func.count(func.distinct(SqlTraceInfo.request_id))
            ).filter(SqlTraceInfo.experiment_id.in_(
                [int(eid) for eid in experiment_ids]
            ))
            
            if start_time:
                total_traces_query = total_traces_query.filter(SqlTraceInfo.timestamp_ms >= start_time)
            if end_time:
                total_traces_query = total_traces_query.filter(SqlTraceInfo.timestamp_ms <= end_time)
            
            total_traces = total_traces_query.scalar() or 1
            
            return [
                {
                    'tool_name': row.tool_name,
                    'trace_count': row.trace_count,
                    'percentage': (row.trace_count / total_traces) * 100 if total_traces > 0 else 0
                }
                for row in results
            ]
    
    def get_tool_metrics(
        self,
        experiment_ids: List[str],
        tool_name: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_bucket: str = 'hour',
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get tool metrics - TODO: Implement detailed metrics."""
        return {'summary': {}, 'time_series': []}
    
    # Tag Methods
    
    def discover_tags(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        min_count: int = 1
    ) -> List[Dict[str, Any]]:
        """Discover tags using SQLAlchemy queries."""
        experiment_ids = self._get_experiment_ids()
        
        with self.ManagedSessionMaker() as session:
            # Query distinct tag keys
            query = session.query(
                SqlTraceTag.key.label('tag_key'),
                func.count(func.distinct(SqlTraceTag.value)).label('unique_values'),
                func.count(func.distinct(SqlTraceTag.trace_id)).label('trace_count')
            ).join(
                SqlTraceInfo,
                SqlTraceTag.trace_id == SqlTraceInfo.request_id
            )
            
            # Filter by experiment IDs
            if experiment_ids:
                query = query.filter(SqlTraceInfo.experiment_id.in_(
                    [int(eid) for eid in experiment_ids]
                ))
            
            # Apply time filters
            if start_time:
                query = query.filter(SqlTraceInfo.timestamp_ms >= start_time)
            if end_time:
                query = query.filter(SqlTraceInfo.timestamp_ms <= end_time)
            
            # Group by tag key and filter by min_count
            results = query.group_by(SqlTraceTag.key).having(
                func.count(func.distinct(SqlTraceTag.trace_id)) >= min_count
            ).order_by(func.count(func.distinct(SqlTraceTag.trace_id)).desc()).all()
            
            return [
                {
                    'tag_key': row.tag_key,
                    'unique_values': row.unique_values,
                    'trace_count': row.trace_count
                }
                for row in results
            ]
    
    def get_tag_metrics(
        self,
        tag_key: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_bucket: str = 'hour',
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get tag metrics - TODO: Implement detailed metrics."""
        return {'tag_values': [], 'time_series': []}
    
    # Dimension & Correlation Methods
    
    def discover_dimensions(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        filter_string: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Discover dimensions - TODO: Implement using SQLAlchemy."""
        return []
    
    def calculate_npmi(
        self,
        dimension1: str,
        value1: str,
        dimension2: str,
        value2: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        filter_string: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate NPMI - TODO: Implement using SQLAlchemy."""
        return {
            'npmi': 0.0,
            'count1': 0,
            'count2': 0,
            'joint_count': 0,
            'total_count': 0
        }
    
    def get_correlations(
        self,
        dimension: str,
        value: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        filter_string: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get correlations - TODO: Implement using SQLAlchemy."""
        return []
    
    def get_assessments(self, experiment_id: str) -> List[Dict[str, Any]]:
        """Get assessments for an experiment."""
        # TODO: Implement assessment discovery using SQLAlchemy
        return []