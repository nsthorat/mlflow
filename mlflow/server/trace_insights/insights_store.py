"""MLflow Trace Insights Store - Central Analytics Engine

This module provides the central store for all trace insights computations.
All REST API handlers should use this store for data retrieval.
"""

import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import func, case, and_, or_, Integer, Float, distinct, desc, cast
from mlflow.store.tracking.sqlalchemy_store import SqlAlchemyStore
from mlflow.store.tracking.dbmodels.models import (
    SqlTraceInfo, 
    SqlSpan, 
    SqlTraceTag
)
from mlflow.server.trace_insights.models import (
    # Traffic models
    VolumeRequest, VolumeResponse, VolumeSummary, VolumeTimeSeries,
    LatencyRequest, LatencyResponse, LatencySummary, LatencyTimeSeries,
    ErrorRequest, ErrorResponse, ErrorSummary, ErrorTimeSeries,
    # Assessment models
    AssessmentDiscoveryRequest, AssessmentDiscoveryResponse, AssessmentInfo,
    AssessmentMetricsRequest, AssessmentMetricsResponse,
    BooleanAssessmentSummary, BooleanAssessmentTimeSeries,
    NumericAssessmentSummary, NumericAssessmentTimeSeries,
    StringAssessmentSummary,
    # Tool models
    ToolDiscoveryRequest, ToolDiscoveryResponse, ToolInfo,
    ToolMetricsRequest, ToolMetricsResponse,
    # Tag models
    TagDiscoveryRequest, TagDiscoveryResponse, TagInfo,
    TagMetricsRequest, TagMetricsResponse, TagValueInfo,
    # Dimension models
    DimensionDiscoveryRequest, DimensionDiscoveryResponse, Dimension, DimensionParameter,
    NPMIRequest, NPMIResponse, DimensionValue, IntersectionInfo, CorrelationInfo,
    # Correlation models
    CorrelationsRequest, CorrelationsResponse, CorrelationItem
)
from mlflow.server.trace_insights.dimensions import (
    discover_dimensions,
    calculate_npmi_score,
    get_correlations_for_filter
)
from mlflow.server.trace_insights.time_bucketing import get_time_bucket_expression, validate_time_bucket
from mlflow.server.trace_insights.tag_utils import should_filter_tag


class InsightsStore:
    """Central store for all trace insights computations."""
    
    def __init__(self, store: SqlAlchemyStore):
        """
        Initialize the insights store with a SQLAlchemy tracking store.
        
        Args:
            store: SqlAlchemyStore instance for database access
        """
        self.store = store
    
    # Traffic & Cost Methods
    
    def get_traffic_volume(self, request: VolumeRequest) -> VolumeResponse:
        """Get trace volume statistics with summary and time series.
        
        Args:
            request: Volume request parameters
            
        Returns:
            VolumeResponse with summary and time series data
        """
        def query_func(session):
            # Build base query
            base_query = session.query(SqlTraceInfo).filter(
                SqlTraceInfo.experiment_id.in_(request.experiment_ids)
            )
            
            # Add time filters
            if request.start_time:
                base_query = base_query.filter(SqlTraceInfo.timestamp_ms >= request.start_time)
            if request.end_time:
                base_query = base_query.filter(SqlTraceInfo.timestamp_ms <= request.end_time)
            
            # Get summary totals
            summary_query = base_query.with_entities(
                func.count().label('count'),
                func.sum(case((SqlTraceInfo.status == 'OK', 1), else_=0)).label('ok_count'),
                func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0)).label('error_count')
            ).first()
            
            # Build time bucket expression using shared utility
            validated_bucket = validate_time_bucket(request.time_bucket or 'hour')
            time_bucket_expr = get_time_bucket_expression(validated_bucket)
            
            # Get time series data
            time_series_query = base_query.with_entities(
                time_bucket_expr,
                func.count().label('count'),
                func.sum(case((SqlTraceInfo.status == 'OK', 1), else_=0)).label('ok_count'),
                func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0)).label('error_count')
            ).group_by(time_bucket_expr).order_by(time_bucket_expr).all()
            
            return {
                'summary': summary_query,
                'time_series': time_series_query
            }
        
        results = self.store.execute_query(query_func)
        
        return VolumeResponse(
            summary=VolumeSummary(
                count=results['summary'].count or 0,
                ok_count=results['summary'].ok_count or 0,
                error_count=results['summary'].error_count or 0
            ),
            time_series=[
                VolumeTimeSeries(
                    time_bucket=int(row.time_bucket) if row.time_bucket else 0,
                    count=row.count or 0,
                    ok_count=row.ok_count or 0,
                    error_count=row.error_count or 0
                )
                for row in results['time_series']
            ]
        )
    
    def get_traffic_latency(self, request: LatencyRequest) -> LatencyResponse:
        """Get latency percentile statistics with summary and time series.
        
        Args:
            request: Latency request parameters
            
        Returns:
            LatencyResponse with summary and time series data
        """
        def query_func(session):
            # Build base query for successful traces only
            base_query = session.query(SqlTraceInfo).filter(
                and_(
                    SqlTraceInfo.experiment_id.in_(request.experiment_ids),
                    SqlTraceInfo.status == 'OK',
                    SqlTraceInfo.execution_time_ms.isnot(None)
                )
            )
            
            # Add time filters
            if request.start_time:
                base_query = base_query.filter(SqlTraceInfo.timestamp_ms >= request.start_time)
            if request.end_time:
                base_query = base_query.filter(SqlTraceInfo.timestamp_ms <= request.end_time)
            
            # Get all execution times for percentile calculation
            exec_times = base_query.with_entities(SqlTraceInfo.execution_time_ms).all()
            exec_times_list = sorted([t[0] for t in exec_times if t[0] is not None])
            
            # Calculate percentiles
            def get_percentile(data, p):
                if not data:
                    return None
                k = (len(data) - 1) * p / 100
                f = int(k)
                c = f + 1 if f < len(data) - 1 else f
                return data[f] if f == c else data[f] + (k - f) * (data[c] - data[f])
            
            summary = {
                'p50_latency': get_percentile(exec_times_list, 50),
                'p90_latency': get_percentile(exec_times_list, 90),
                'p99_latency': get_percentile(exec_times_list, 99),
                'avg_latency': sum(exec_times_list) / len(exec_times_list) if exec_times_list else None,
                'min_latency': min(exec_times_list) if exec_times_list else None,
                'max_latency': max(exec_times_list) if exec_times_list else None
            }
            
            # Build time bucket expression for SQLite
            if request.time_bucket == "hour":
                time_bucket_expr = cast(
                    (SqlTraceInfo.timestamp_ms / 3600000) * 3600000,
                    Integer
                )
            elif request.time_bucket == "day":
                time_bucket_expr = cast(
                    (SqlTraceInfo.timestamp_ms / 86400000) * 86400000,
                    Integer
                )
            else:
                time_bucket_expr = cast(
                    (SqlTraceInfo.timestamp_ms / 604800000) * 604800000,
                    Integer
                )
            
            # Get time series data - group execution times by bucket
            time_series_data = []
            time_bucket_groups = {}
            
            # Group execution times by time bucket
            for trace in base_query.all():
                if request.time_bucket == "hour":
                    bucket = int((trace.timestamp_ms / 3600000) * 3600000)
                elif request.time_bucket == "day":
                    bucket = int((trace.timestamp_ms / 86400000) * 86400000)
                else:
                    bucket = int((trace.timestamp_ms / 604800000) * 604800000)
                
                if bucket not in time_bucket_groups:
                    time_bucket_groups[bucket] = []
                time_bucket_groups[bucket].append(trace.execution_time_ms)
            
            # Calculate percentiles for each bucket
            for bucket in sorted(time_bucket_groups.keys()):
                bucket_times = sorted(time_bucket_groups[bucket])
                time_series_data.append({
                    'time_bucket': bucket,
                    'p50_latency': get_percentile(bucket_times, 50),
                    'p90_latency': get_percentile(bucket_times, 90),
                    'p99_latency': get_percentile(bucket_times, 99),
                    'avg_latency': sum(bucket_times) / len(bucket_times) if bucket_times else None
                })
            
            return {
                'summary': summary,
                'time_series': time_series_data
            }
        
        results = self.store.execute_query(query_func)
        
        return LatencyResponse(
            summary=LatencySummary(
                p50_latency=results['summary']['p50_latency'],
                p90_latency=results['summary']['p90_latency'],
                p99_latency=results['summary']['p99_latency'],
                avg_latency=results['summary']['avg_latency'],
                min_latency=results['summary']['min_latency'],
                max_latency=results['summary']['max_latency']
            ),
            time_series=[
                LatencyTimeSeries(
                    time_bucket=row['time_bucket'],
                    p50_latency=row['p50_latency'],
                    p90_latency=row['p90_latency'],
                    p99_latency=row['p99_latency'],
                    avg_latency=row['avg_latency']
                )
                for row in results['time_series']
            ]
        )
    
    def get_traffic_errors(self, request: ErrorRequest) -> ErrorResponse:
        """Get error rate statistics with summary and time series.
        
        Args:
            request: Error request parameters
            
        Returns:
            ErrorResponse with summary and time series data
        """
        def query_func(session):
            # Build base query
            base_query = session.query(SqlTraceInfo).filter(
                SqlTraceInfo.experiment_id.in_(request.experiment_ids)
            )
            
            # Add time filters
            if request.start_time:
                base_query = base_query.filter(SqlTraceInfo.timestamp_ms >= request.start_time)
            if request.end_time:
                base_query = base_query.filter(SqlTraceInfo.timestamp_ms <= request.end_time)
            
            # Get summary totals
            summary_query = base_query.with_entities(
                func.count().label('total_count'),
                func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0)).label('error_count')
            ).first()
            
            total = summary_query.total_count or 0
            errors = summary_query.error_count or 0
            error_rate = (errors / total * 100) if total > 0 else 0
            
            # Build time bucket expression for SQLite
            if request.time_bucket == "hour":
                time_bucket_expr = cast(
                    (SqlTraceInfo.timestamp_ms / 3600000) * 3600000,
                    Integer
                )
            elif request.time_bucket == "day":
                time_bucket_expr = cast(
                    (SqlTraceInfo.timestamp_ms / 86400000) * 86400000,
                    Integer
                )
            else:
                time_bucket_expr = cast(
                    (SqlTraceInfo.timestamp_ms / 604800000) * 604800000,
                    Integer
                )
            
            # Get time series data
            error_count_expr = func.sum(case((SqlTraceInfo.status == 'ERROR', 1), else_=0))
            total_count_expr = func.count()
            
            time_series_query = base_query.with_entities(
                time_bucket_expr.label('time_bucket'),
                total_count_expr.label('total_count'),
                error_count_expr.label('error_count')
            ).group_by(time_bucket_expr).order_by(time_bucket_expr).all()
            
            return {
                'summary': {
                    'total_count': total,
                    'error_count': errors,
                    'error_rate': error_rate
                },
                'time_series': time_series_query
            }
        
        results = self.store.execute_query(query_func)
        
        return ErrorResponse(
            summary=ErrorSummary(
                total_count=results['summary']['total_count'],
                error_count=results['summary']['error_count'],
                error_rate=results['summary']['error_rate']
            ),
            time_series=[
                ErrorTimeSeries(
                    time_bucket=int(row.time_bucket) if row.time_bucket else 0,
                    total_count=row.total_count or 0,
                    error_count=row.error_count or 0,
                    error_rate=((row.error_count or 0) / row.total_count * 100) if row.total_count else 0
                )
                for row in results['time_series']
            ]
        )
    
    # Assessment Methods
    
    def get_assessment_discovery(self, request: AssessmentDiscoveryRequest) -> AssessmentDiscoveryResponse:
        """Discover all assessments in the specified experiments.
        
        Args:
            request: Assessment discovery request parameters
            
        Returns:
            AssessmentDiscoveryResponse with list of discovered assessments
        """
        # TODO: Implement assessment discovery from span attributes
        # For now, return empty list
        return AssessmentDiscoveryResponse(data=[])
    
    def get_assessment_metrics(self, request: AssessmentMetricsRequest) -> AssessmentMetricsResponse:
        """Get detailed metrics for a specific assessment.
        
        Args:
            request: Assessment metrics request parameters
            
        Returns:
            AssessmentMetricsResponse with assessment metrics
        """
        # TODO: Implement assessment metrics computation
        # For now, return a placeholder response
        return AssessmentMetricsResponse(
            assessment_name=request.assessment_name,
            assessment_type="boolean",
            sources=["LLM_JUDGE"],
            summary=BooleanAssessmentSummary(
                total_count=0,
                failure_count=0,
                failure_rate=0.0
            ),
            time_series=[]
        )
    
    # Tool Methods
    
    def get_tool_discovery(self, request: ToolDiscoveryRequest) -> ToolDiscoveryResponse:
        """Discover all tools used in the specified experiments.
        
        Args:
            request: Tool discovery request parameters
            
        Returns:
            ToolDiscoveryResponse with list of discovered tools
        """
        from mlflow.server.trace_insights.tools import (
            get_tool_discovery as get_tools,
            get_tool_volume_over_time,
            get_tool_latency_over_time,
            get_tool_error_rate_over_time
        )
        
        # Use existing tool discovery logic
        tools = get_tools(
            self.store,
            request.experiment_ids,
            request.start_time,
            request.end_time
        )
        
        # Get time series data for all tools
        tool_names = [tool.tool_name for tool in tools]
        
        # Get volume over time for all tools
        volume_data = get_tool_volume_over_time(
            self.store,
            request.experiment_ids,
            tool_names=tool_names[:10],  # Limit to top 10 for performance
            start_time=request.start_time,
            end_time=request.end_time,
            time_bucket='hour'
        )
        
        # Get latency over time for all tools
        latency_data = get_tool_latency_over_time(
            self.store,
            request.experiment_ids,
            tool_names=tool_names[:10],  # Limit to top 10 for performance
            start_time=request.start_time,
            end_time=request.end_time,
            time_bucket='hour'
        )
        
        # Get error rate over time for all tools
        error_data = get_tool_error_rate_over_time(
            self.store,
            request.experiment_ids,
            tool_names=tool_names[:10],  # Limit to top 10 for performance
            start_time=request.start_time,
            end_time=request.end_time,
            time_bucket='hour'
        )
        
        # Group time series data by tool
        tool_time_series = {}
        for tool_name in tool_names[:10]:
            tool_time_series[tool_name] = {
                "volume": [v for v in volume_data if v.tool_name == tool_name],
                "latency": [l for l in latency_data if l.tool_name == tool_name],
                "errors": [e for e in error_data if e.tool_name == tool_name]
            }
        
        # Convert to response format
        tool_infos = []
        for tool in tools:
            # Get time series for this tool
            ts = tool_time_series.get(tool.tool_name, {"volume": [], "latency": [], "errors": []})
            
            tool_infos.append(ToolInfo(
                tool_name=tool.tool_name,
                trace_count=tool.total_calls,
                invocation_count=tool.total_calls,
                error_count=tool.error_count,
                error_rate=(tool.error_count / tool.total_calls * 100) if tool.total_calls else 0,
                avg_latency_ms=tool.avg_latency_ms,
                p50_latency=tool.p50_latency_ms,
                p90_latency=tool.p90_latency_ms,
                p99_latency=tool.p99_latency_ms,
                time_series=ts
            ))
        
        return ToolDiscoveryResponse(data=tool_infos)
    
    def get_tool_metrics(self, request: ToolMetricsRequest) -> ToolMetricsResponse:
        """Get detailed metrics for a specific tool.
        
        Args:
            request: Tool metrics request parameters
            
        Returns:
            ToolMetricsResponse with tool metrics
        """
        from mlflow.server.trace_insights.tools import (
            get_tool_discovery,
            get_tool_volume_over_time,
            get_tool_latency_over_time,
            get_tool_error_rate_over_time
        )
        
        # Get all tools and filter for the requested one
        tools = get_tool_discovery(
            self.store,
            request.experiment_ids,
            request.start_time,
            request.end_time
        )
        
        # Find the specific tool
        tool_data = None
        for tool in tools:
            if tool.tool_name == request.tool_name:
                tool_data = tool
                break
        
        if not tool_data:
            # Return empty metrics if tool not found
            tool_data = ToolInfo(
                tool_name=request.tool_name,
                trace_count=0,
                invocation_count=0,
                error_count=0,
                error_rate=0.0,
                avg_latency_ms=None,
                p50_latency=None,
                p90_latency=None,
                p99_latency=None,
                time_series={
                    "volume": [],
                    "latency": [],
                    "errors": []
                }
            )
        else:
            # Get time series data for this specific tool
            volume_data = get_tool_volume_over_time(
                self.store,
                request.experiment_ids,
                tool_names=[request.tool_name],
                start_time=request.start_time,
                end_time=request.end_time,
                time_bucket=request.time_bucket
            )
            
            latency_data = get_tool_latency_over_time(
                self.store,
                request.experiment_ids,
                tool_names=[request.tool_name],
                start_time=request.start_time,
                end_time=request.end_time,
                time_bucket=request.time_bucket
            )
            
            error_data = get_tool_error_rate_over_time(
                self.store,
                request.experiment_ids,
                tool_names=[request.tool_name],
                start_time=request.start_time,
                end_time=request.end_time,
                time_bucket=request.time_bucket
            )
            
            # Convert to response format
            tool_data = ToolInfo(
                tool_name=tool_data.tool_name,
                trace_count=tool_data.total_calls,
                invocation_count=tool_data.total_calls,
                error_count=tool_data.error_count,
                error_rate=(tool_data.error_count / tool_data.total_calls * 100) if tool_data.total_calls else 0,
                avg_latency_ms=tool_data.avg_latency_ms,
                p50_latency=tool_data.p50_latency_ms,
                p90_latency=tool_data.p90_latency_ms,
                p99_latency=tool_data.p99_latency_ms,
                time_series={
                    "volume": volume_data,
                    "latency": latency_data,
                    "errors": error_data
                }
            )
        
        return ToolMetricsResponse(data=tool_data)
    
    # Tag Methods
    
    def get_tag_discovery(self, request: TagDiscoveryRequest) -> TagDiscoveryResponse:
        """Discover all tag keys used in the specified experiments.
        
        Args:
            request: Tag discovery request parameters
            
        Returns:
            TagDiscoveryResponse with list of discovered tag keys
        """
        def query_func(session):
            # Build base query
            base_query = session.query(SqlTraceTag).join(
                SqlTraceInfo, SqlTraceTag.request_id == SqlTraceInfo.request_id
            ).filter(
                SqlTraceInfo.experiment_id.in_(request.experiment_ids)
            )
            
            # Add time filters
            if request.start_time:
                base_query = base_query.filter(SqlTraceInfo.timestamp_ms >= request.start_time)
            if request.end_time:
                base_query = base_query.filter(SqlTraceInfo.timestamp_ms <= request.end_time)
            
            # Get unique tag keys with counts
            tag_query = base_query.with_entities(
                SqlTraceTag.key.label('tag_key'),
                func.count(distinct(SqlTraceTag.request_id)).label('trace_count'),
                func.count(distinct(SqlTraceTag.value)).label('unique_values')
            ).group_by(SqlTraceTag.key).order_by(desc('trace_count')).all()
            
            return tag_query
        
        results = self.store.execute_query(query_func)
        
        # Convert to response format, filtering out built-in MLflow tags
        tag_infos = [
            TagInfo(
                tag_key=row.tag_key,
                trace_count=row.trace_count,
                unique_values=row.unique_values
            )
            for row in results
            if not should_filter_tag(row.tag_key)
        ]
        
        return TagDiscoveryResponse(data=tag_infos)
    
    def get_tag_metrics(self, request: TagMetricsRequest) -> TagMetricsResponse:
        """Get detailed metrics for a specific tag key.
        
        Args:
            request: Tag metrics request parameters
            
        Returns:
            TagMetricsResponse with tag value distribution
        """
        def query_func(session):
            # Build base query
            base_query = session.query(SqlTraceTag).join(
                SqlTraceInfo, SqlTraceTag.request_id == SqlTraceInfo.request_id
            ).filter(
                and_(
                    SqlTraceInfo.experiment_id.in_(request.experiment_ids),
                    SqlTraceTag.key == request.tag_key
                )
            )
            
            # Add time filters
            if request.start_time:
                base_query = base_query.filter(SqlTraceInfo.timestamp_ms >= request.start_time)
            if request.end_time:
                base_query = base_query.filter(SqlTraceInfo.timestamp_ms <= request.end_time)
            
            # Get total trace count for this tag
            total_count = base_query.with_entities(
                func.count(distinct(SqlTraceTag.request_id))
            ).scalar()
            
            # Get top values with counts
            value_query = base_query.with_entities(
                SqlTraceTag.value.label('value'),
                func.count(SqlTraceTag.request_id).label('count')
            ).group_by(SqlTraceTag.value).order_by(desc('count')).limit(request.limit or 10).all()
            
            # Get unique value count
            unique_values = base_query.with_entities(
                func.count(distinct(SqlTraceTag.value))
            ).scalar()
            
            return {
                'total_count': total_count,
                'unique_values': unique_values,
                'top_values': value_query
            }
        
        results = self.store.execute_query(query_func)
        
        # Convert to response format
        top_values = [
            TagValueInfo(
                value=row.value,
                count=row.count,
                percentage=(row.count / results['total_count'] * 100) if results['total_count'] else 0
            )
            for row in results['top_values']
        ]
        
        return TagMetricsResponse(
            data={
                "tag_key": request.tag_key,
                "trace_count": results['total_count'] or 0,
                "unique_values": results['unique_values'] or 0,
                "top_values": top_values
            }
        )
    
    # Dimension Methods
    
    def get_dimension_discovery(self, request: DimensionDiscoveryRequest) -> DimensionDiscoveryResponse:
        """Discover all available dimensions for correlation analysis.
        
        Args:
            request: Dimension discovery request parameters
            
        Returns:
            DimensionDiscoveryResponse with list of available dimensions
        """
        dimensions = discover_dimensions(
            self.store,
            request.experiment_ids,
            request.start_time,
            request.end_time
        )
        
        return DimensionDiscoveryResponse(data=dimensions)
    
    def calculate_npmi(self, request: NPMIRequest) -> NPMIResponse:
        """Calculate NPMI correlation between two dimensions.
        
        Args:
            request: NPMI calculation request parameters
            
        Returns:
            NPMIResponse with correlation score and statistics
        """
        result = calculate_npmi_score(
            self.store,
            request.experiment_ids,
            request.dimension1,
            request.dimension2,
            request.start_time,
            request.end_time
        )
        
        return NPMIResponse(
            dimension1=DimensionValue(
                name=result['dimension1']['name'],
                value=result['dimension1']['value'],
                count=result['dimension1']['count']
            ),
            dimension2=DimensionValue(
                name=result['dimension2']['name'],
                value=result['dimension2']['value'],
                count=result['dimension2']['count']
            ),
            intersection=IntersectionInfo(
                count=result['intersection']['count']
            ),
            correlation=CorrelationInfo(
                npmi_score=result['correlation']['npmi_score'],
                strength=result['correlation']['strength']
            )
        )
    
    def get_correlations(self, request: CorrelationsRequest) -> CorrelationsResponse:
        """Get NPMI correlations for a given filter.
        
        Args:
            request: Correlations request parameters
            
        Returns:
            CorrelationsResponse with top correlations
        """
        correlations = get_correlations_for_filter(
            self.store,
            request.experiment_ids,
            request.filter_string,
            request.correlation_dimensions,
            request.start_time,
            request.end_time,
            request.limit
        )
        
        # Convert to response format
        correlation_items = [
            CorrelationItem(
                dimension=corr['dimension'],
                value=corr['value'],
                npmi_score=corr['npmi_score'],
                trace_count=corr['trace_count'],
                percentage_of_slice=corr['percentage_of_slice'],
                percentage_of_total=corr['percentage_of_total'],
                strength=corr['strength']
            )
            for corr in correlations
        ]
        
        return CorrelationsResponse(data=correlation_items)