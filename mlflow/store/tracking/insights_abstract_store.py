"""
Abstract base class for trace insights storage implementations.

This module defines the interface that all insights store implementations must follow.
The insights store provides analytics and aggregations for trace data.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from mlflow.store.tracking.abstract_store import AbstractStore


class InsightsAbstractStore(AbstractStore, ABC):
    """Abstract base class for trace insights storage.
    
    This class extends AbstractStore to provide insights-related operations
    that can be performed on trace data. Implementations should provide
    efficient queries for analytics and aggregations while maintaining
    compatibility with standard MLflow tracking operations.
    
    Note: experiment_ids are not passed as parameters - they should be
    determined from the store's configuration or environment.
    """
    
    # Traffic & Cost Methods
    
    @abstractmethod
    def get_traffic_volume(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_bucket: str = 'hour',
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get trace volume statistics with summary and time series.
        
        Args:
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            time_bucket: Time aggregation bucket ('hour', 'day', 'week')
            timezone: Timezone for time bucketing (e.g., 'America/New_York')
            
        Returns:
            Dictionary with 'summary' and 'time_series' keys
        """
        pass
    
    @abstractmethod
    def get_traffic_latency(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_bucket: str = 'hour',
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get latency percentile statistics with summary and time series.
        
        Args:
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            time_bucket: Time aggregation bucket ('hour', 'day', 'week')
            timezone: Timezone for time bucketing
            
        Returns:
            Dictionary with 'summary' and 'time_series' keys
        """
        pass
    
    @abstractmethod
    def get_traffic_errors(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_bucket: str = 'hour',
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get error statistics with summary and time series.
        
        Args:
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            time_bucket: Time aggregation bucket ('hour', 'day', 'week')
            timezone: Timezone for time bucketing
            
        Returns:
            Dictionary with 'summary' and 'time_series' keys
        """
        pass
    
    # Assessment Methods
    
    @abstractmethod
    def discover_assessments(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        min_count: int = 1
    ) -> List[Dict[str, Any]]:
        """Discover all assessments logged within the time range.
        
        Args:
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            min_count: Minimum number of occurrences to include
            
        Returns:
            List of assessment info dictionaries
        """
        pass
    
    @abstractmethod
    def get_assessment_metrics(
        self,
        assessment_name: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_bucket: str = 'hour',
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get metrics for a specific assessment.
        
        Args:
            assessment_name: Name of the assessment to get metrics for
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            time_bucket: Time aggregation bucket ('hour', 'day', 'week')
            timezone: Timezone for time bucketing
            
        Returns:
            Dictionary with assessment metrics (varies by assessment type)
        """
        pass
    
    # Assessment Methods
    
    @abstractmethod
    def get_assessments(self, experiment_id: str) -> List[Dict[str, Any]]:
        """Get assessments for an experiment.
        
        Args:
            experiment_id: The experiment ID to get assessments for
            
        Returns:
            List of assessment info dictionaries
        """
        pass
    
    # Tool Methods
    
    @abstractmethod
    def discover_tools(
        self,
        experiment_ids: List[str],
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        min_count: int = 1
    ) -> List[Dict[str, Any]]:
        """Discover all tools used within the time range.
        
        Args:
            experiment_ids: List of experiment IDs to analyze
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            min_count: Minimum number of occurrences to include
            
        Returns:
            List of tool info dictionaries
        """
        pass
    
    @abstractmethod
    def get_tool_metrics(
        self,
        experiment_ids: List[str],
        tool_name: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_bucket: str = 'hour',
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get metrics for a specific tool.
        
        Args:
            experiment_ids: List of experiment IDs to analyze
            tool_name: Name of the tool to get metrics for
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            time_bucket: Time aggregation bucket ('hour', 'day', 'week')
            timezone: Timezone for time bucketing
            
        Returns:
            Dictionary with tool usage metrics
        """
        pass
    
    # Tag Methods
    
    @abstractmethod
    def discover_tags(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        min_count: int = 1
    ) -> List[Dict[str, Any]]:
        """Discover all tags used within the time range.
        
        Args:
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            min_count: Minimum number of occurrences to include
            
        Returns:
            List of tag info dictionaries
        """
        pass
    
    @abstractmethod
    def get_tag_metrics(
        self,
        tag_key: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_bucket: str = 'hour',
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get metrics for a specific tag key.
        
        Args:
            tag_key: Tag key to get metrics for
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            time_bucket: Time aggregation bucket ('hour', 'day', 'week')
            timezone: Timezone for time bucketing
            
        Returns:
            Dictionary with tag value distribution and time series
        """
        pass
    
    # Dimension Methods
    
    @abstractmethod
    def discover_dimensions(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        filter_string: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Discover all available dimensions for analysis.
        
        Args:
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            filter_string: Optional filter to apply before discovery
            
        Returns:
            List of dimension dictionaries with metadata
        """
        pass
    
    @abstractmethod
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
        """Calculate NPMI (Normalized Pointwise Mutual Information) between two dimension values.
        
        Args:
            dimension1: First dimension name (e.g., 'status', 'tags.tool')
            value1: Value for first dimension (e.g., 'ERROR', 'langchain')
            dimension2: Second dimension name
            value2: Value for second dimension
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            filter_string: Optional base filter to apply
            
        Returns:
            Dictionary with NPMI score, counts, and confidence intervals
        """
        pass
    
    # Correlation Methods
    
    @abstractmethod
    def get_correlations(
        self,
        dimension: str,
        value: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        filter_string: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top correlations for a specific dimension value.
        
        Args:
            dimension: Dimension name (e.g., 'status', 'tags.tool')
            value: Value to find correlations for (e.g., 'ERROR')
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            filter_string: Optional base filter to apply
            limit: Maximum number of correlations to return
            
        Returns:
            List of correlation dictionaries sorted by NPMI score
        """
        pass