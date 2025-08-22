"""MLflow Trace Insights - Pydantic Models

This module defines all request and response models for the trace insights REST API.
All models follow the summary + time_series pattern defined in insights_rest_api.md.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# Common Base Models
# ============================================================================

class BaseRequest(BaseModel):
    """Base request for all trace insights endpoints."""
    experiment_ids: List[str] = Field(description="List of experiment IDs to analyze")
    start_time: Optional[int] = Field(None, description="Start timestamp in milliseconds")
    end_time: Optional[int] = Field(None, description="End timestamp in milliseconds")


class TimeSeriesRequest(BaseRequest):
    """Base request for endpoints that support time bucketing."""
    time_bucket: str = Field("hour", description="Time bucketing: hour, day, or week")
    timezone: Optional[str] = Field(None, description="IANA timezone name (e.g., 'America/New_York')")


# ============================================================================
# Traffic & Cost Models
# ============================================================================

# Volume Models
class VolumeRequest(TimeSeriesRequest):
    """Request for trace volume computation."""
    pass


class VolumeSummary(BaseModel):
    """Summary statistics for trace volume."""
    count: int = Field(description="Total trace count")
    ok_count: int = Field(description="Count of successful traces")
    error_count: int = Field(description="Count of error traces")


class VolumeTimeSeries(BaseModel):
    """Time series data point for volume."""
    time_bucket: int = Field(description="Unix timestamp in milliseconds")
    count: int = Field(description="Total trace count")
    ok_count: int = Field(description="Count of successful traces")
    error_count: int = Field(description="Count of error traces")


class VolumeResponse(BaseModel):
    """Response for volume endpoint."""
    summary: VolumeSummary
    time_series: List[VolumeTimeSeries]


# Latency Models
class LatencyRequest(TimeSeriesRequest):
    """Request for latency percentiles computation."""
    pass


class LatencySummary(BaseModel):
    """Summary statistics for latency."""
    p50_latency: Optional[float] = Field(description="50th percentile latency (ms)")
    p90_latency: Optional[float] = Field(description="90th percentile latency (ms)")
    p99_latency: Optional[float] = Field(description="99th percentile latency (ms)")
    avg_latency: Optional[float] = Field(description="Average latency (ms)")
    min_latency: Optional[float] = Field(description="Minimum latency (ms)")
    max_latency: Optional[float] = Field(description="Maximum latency (ms)")


class LatencyTimeSeries(BaseModel):
    """Time series data point for latency."""
    time_bucket: int = Field(description="Unix timestamp in milliseconds")
    p50_latency: Optional[float] = Field(description="50th percentile latency (ms)")
    p90_latency: Optional[float] = Field(description="90th percentile latency (ms)")
    p99_latency: Optional[float] = Field(description="99th percentile latency (ms)")
    avg_latency: Optional[float] = Field(description="Average latency (ms)")


class LatencyResponse(BaseModel):
    """Response for latency endpoint."""
    summary: LatencySummary
    time_series: List[LatencyTimeSeries]


# Error Models
class ErrorRequest(TimeSeriesRequest):
    """Request for error rate computation."""
    pass


class ErrorSummary(BaseModel):
    """Summary statistics for errors."""
    total_count: int = Field(description="Total trace count")
    error_count: int = Field(description="Count of error traces")
    error_rate: float = Field(description="Error rate percentage")


class ErrorTimeSeries(BaseModel):
    """Time series data point for errors."""
    time_bucket: int = Field(description="Unix timestamp in milliseconds")
    total_count: int = Field(description="Total trace count")
    error_count: int = Field(description="Count of error traces")
    error_rate: float = Field(description="Error rate percentage")


class ErrorResponse(BaseModel):
    """Response for error endpoint."""
    summary: ErrorSummary
    time_series: List[ErrorTimeSeries]


# ============================================================================
# Assessment Models
# ============================================================================

class AssessmentDiscoveryRequest(BaseRequest):
    """Request for assessment discovery."""
    pass


class AssessmentInfo(BaseModel):
    """Information about a discovered assessment."""
    assessment_name: str = Field(description="Name of the assessment")
    assessment_type: str = Field(description="Type: boolean, numeric, or string")
    sources: List[str] = Field(description="Sources of the assessment (e.g., LLM_JUDGE)")
    trace_count: int = Field(description="Number of traces with this assessment")


class AssessmentDiscoveryResponse(BaseModel):
    """Response for assessment discovery endpoint."""
    data: List[AssessmentInfo]


class AssessmentMetricsRequest(TimeSeriesRequest):
    """Request for assessment metrics."""
    assessment_name: str = Field(description="Name of the assessment to analyze")


# Boolean Assessment Models
class BooleanAssessmentSummary(BaseModel):
    """Summary statistics for boolean assessments."""
    total_count: int = Field(description="Total evaluations")
    failure_count: int = Field(description="Number of failures")
    failure_rate: float = Field(description="Failure rate percentage")


class BooleanAssessmentTimeSeries(BaseModel):
    """Time series data for boolean assessments."""
    time_bucket: int = Field(description="Unix timestamp in milliseconds")
    total_count: int = Field(description="Total evaluations")
    failure_count: int = Field(description="Number of failures")
    failure_rate: float = Field(description="Failure rate percentage")


# Numeric Assessment Models
class NumericAssessmentSummary(BaseModel):
    """Summary statistics for numeric assessments."""
    p50: float = Field(description="50th percentile")
    p90: float = Field(description="90th percentile")
    p99: float = Field(description="99th percentile")
    avg: float = Field(description="Average value")
    min: float = Field(description="Minimum value")
    max: float = Field(description="Maximum value")


class NumericAssessmentTimeSeries(BaseModel):
    """Time series data for numeric assessments."""
    time_bucket: int = Field(description="Unix timestamp in milliseconds")
    p50: float = Field(description="50th percentile")
    p90: float = Field(description="90th percentile")
    p99: float = Field(description="99th percentile")
    avg: float = Field(description="Average value")


# String Assessment Models
class StringAssessmentSummary(BaseModel):
    """Summary statistics for string assessments."""
    total_count: int = Field(description="Total evaluations")
    unique_values: int = Field(description="Number of unique values")
    top_values: List[Dict[str, Any]] = Field(description="Top values with counts")


class AssessmentMetricsResponse(BaseModel):
    """Response for assessment metrics endpoint."""
    assessment_name: str
    assessment_type: str
    sources: List[str]
    # Use union type for different assessment types
    summary: Any  # Will be BooleanAssessmentSummary, NumericAssessmentSummary, or StringAssessmentSummary
    time_series: List[Any]  # Will be corresponding time series type


# ============================================================================
# Tool Models
# ============================================================================

class ToolDiscoveryRequest(BaseRequest):
    """Request for tool discovery."""
    limit: int = Field(50, description="Maximum number of tools to return")


class ToolInfo(BaseModel):
    """Information about a discovered tool."""
    tool_name: str = Field(description="Name of the tool")
    trace_count: int = Field(description="Number of traces using this tool")
    invocation_count: int = Field(description="Total invocations of this tool")
    error_count: int = Field(description="Number of errors")
    error_rate: float = Field(description="Error rate percentage")
    avg_latency_ms: Optional[float] = Field(None, description="Average latency (ms)")
    p50_latency: Optional[float] = Field(None, description="50th percentile latency (ms)")
    p90_latency: Optional[float] = Field(None, description="90th percentile latency (ms)")
    p99_latency: Optional[float] = Field(None, description="99th percentile latency (ms)")
    time_series: Dict[str, List[Any]] = Field(
        default_factory=lambda: {"volume": [], "latency": [], "errors": []},
        description="Time series data for volume, latency, and errors"
    )


class ToolDiscoveryResponse(BaseModel):
    """Response for tool discovery endpoint."""
    data: List[ToolInfo]


class ToolMetricsRequest(TimeSeriesRequest):
    """Request for tool metrics."""
    tool_name: str = Field(description="Name of the tool to analyze")


class ToolMetricsResponse(BaseModel):
    """Response for tool metrics endpoint."""
    data: ToolInfo


# ============================================================================
# Tag Models
# ============================================================================

class TagDiscoveryRequest(BaseRequest):
    """Request for tag discovery."""
    limit: int = Field(100, description="Maximum number of tags to return")


class TagInfo(BaseModel):
    """Information about a discovered tag key."""
    tag_key: str = Field(description="Tag key name")
    trace_count: int = Field(description="Number of traces with this tag")
    unique_values: int = Field(description="Number of unique values")


class TagDiscoveryResponse(BaseModel):
    """Response for tag discovery endpoint."""
    data: List[TagInfo]


class TagMetricsRequest(BaseRequest):
    """Request for tag metrics."""
    tag_key: str = Field(description="Tag key to analyze")
    limit: int = Field(10, description="Number of top values to return")


class TagValueInfo(BaseModel):
    """Information about a tag value."""
    value: str = Field(description="Tag value")
    count: int = Field(description="Number of occurrences")
    percentage: float = Field(description="Percentage of total")


class TagMetricsResponse(BaseModel):
    """Response for tag metrics endpoint."""
    data: Dict[str, Any] = Field(description="Tag metrics data including top values")


# ============================================================================
# Dimension Models
# ============================================================================

class DimensionDiscoveryRequest(BaseRequest):
    """Request for dimension discovery."""
    pass


class DimensionParameter(BaseModel):
    """Parameter for a dimension."""
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type: string, number, boolean")
    required: bool = Field(description="Whether parameter is required")


class Dimension(BaseModel):
    """Discovered dimension for correlation analysis."""
    name: str = Field(description="Dimension name")
    type: str = Field(description="Dimension type: tag, span_attribute, assessment, etc.")
    data_type: str = Field(description="Data type: string, numeric, boolean")
    parameters: List[DimensionParameter] = Field(description="Required parameters")


class DimensionDiscoveryResponse(BaseModel):
    """Response for dimension discovery endpoint."""
    data: List[Dimension]


class NPMIRequest(BaseRequest):
    """Request for NPMI calculation."""
    dimension1: Dict[str, Any] = Field(description="First dimension")
    dimension2: Dict[str, Any] = Field(description="Second dimension")


class DimensionValue(BaseModel):
    """Value and count for a dimension."""
    name: str = Field(description="Dimension name")
    value: Any = Field(description="Dimension value")
    count: int = Field(description="Number of occurrences")


class IntersectionInfo(BaseModel):
    """Intersection information for NPMI."""
    count: int = Field(description="Number of traces in intersection")


class CorrelationInfo(BaseModel):
    """Correlation information."""
    npmi_score: float = Field(description="NPMI score (-1 to 1)")
    strength: str = Field(description="Strength: Strong, Moderate, or Weak")


class NPMIResponse(BaseModel):
    """Response for NPMI calculation endpoint."""
    dimension1: DimensionValue
    dimension2: DimensionValue
    intersection: IntersectionInfo
    correlation: CorrelationInfo


# ============================================================================
# Correlation Models
# ============================================================================

class CorrelationsRequest(BaseRequest):
    """Request for correlations."""
    filter_string: str = Field(description="Filter to correlate against")
    correlation_dimensions: List[str] = Field(
        default=["tag", "assessment", "span_attribute"],
        description="Dimensions to check for correlations"
    )
    limit: int = Field(10, description="Number of top correlations to return")


class CorrelationItem(BaseModel):
    """Single correlation item."""
    dimension: str = Field(description="Dimension name")
    value: Any = Field(description="Dimension value")
    npmi_score: float = Field(description="NPMI correlation score")
    trace_count: int = Field(description="Number of traces")
    percentage_of_slice: float = Field(description="Percentage of filtered slice")
    percentage_of_total: float = Field(description="Percentage of total traces")
    strength: str = Field(description="Correlation strength")


class CorrelationsResponse(BaseModel):
    """Response for correlations endpoint."""
    data: List[CorrelationItem]


# ============================================================================
# Legacy Models (for backward compatibility during migration)
# ============================================================================

class VolumeOverTimePoint(BaseModel):
    """Legacy: Single data point for volume over time computation."""
    time_bucket: str = Field(description="Time bucket (hour or day)")
    count: int = Field(description="Total trace count")
    ok_count: int = Field(description="Count of successful traces")
    error_count: int = Field(description="Count of error traces")


class VolumeOverTimeResponse(BaseModel):
    """Legacy: Response for volume over time endpoint."""
    volume_over_time: List[VolumeOverTimePoint]


class LatencyPercentilesPoint(BaseModel):
    """Legacy: Single data point for latency percentiles computation."""
    time_bucket: str = Field(description="Time bucket (hour or day)")
    p50_latency: Optional[float] = Field(description="50th percentile latency (ms)")
    p90_latency: Optional[float] = Field(description="90th percentile latency (ms)")
    p99_latency: Optional[float] = Field(description="99th percentile latency (ms)")
    avg_latency: Optional[float] = Field(description="Average latency (ms)")
    min_latency: Optional[int] = Field(description="Minimum latency (ms)")
    max_latency: Optional[int] = Field(description="Maximum latency (ms)")


class LatencyPercentilesOverTimeResponse(BaseModel):
    """Legacy: Response for latency percentiles over time endpoint."""
    latency_percentiles_over_time: List[LatencyPercentilesPoint]


class ErrorRatePoint(BaseModel):
    """Legacy: Single data point for error rate computation."""
    time_bucket: str = Field(description="Time bucket (hour or day)")
    total_count: int = Field(description="Total trace count")
    error_count: int = Field(description="Count of error traces")
    error_rate: float = Field(description="Error rate percentage")


class ErrorRateOverTimeResponse(BaseModel):
    """Legacy: Response for error rate over time endpoint."""
    error_rate_over_time: List[ErrorRatePoint]


class ErrorCorrelationPoint(BaseModel):
    """Legacy: Single data point for error correlation analysis."""
    dimension: str = Field(description="Dimension being analyzed (e.g., span_type)")
    value: str = Field(description="Value within the dimension")
    total_count: int = Field(description="Total occurrences")
    error_count: int = Field(description="Error occurrences")
    npmi_score: float = Field(description="NPMI correlation score (-1 to 1)")


class ErrorCorrelationsNPMIResponse(BaseModel):
    """Legacy: Response for error correlations NPMI endpoint."""
    error_correlations: List[ErrorCorrelationPoint]


class TokenCostByModelPoint(BaseModel):
    """Legacy: Single data point for token cost by model computation."""
    model_name: str = Field(description="Model name")
    total_tokens: int = Field(description="Total tokens used")
    input_tokens: int = Field(description="Input tokens")
    output_tokens: int = Field(description="Output tokens")
    estimated_cost: float = Field(description="Estimated cost in USD")


class TokenCostByModelResponse(BaseModel):
    """Legacy: Response for token cost by model endpoint."""
    token_cost_by_model: List[TokenCostByModelPoint]


# Legacy Request Models (kept for compatibility)
TraceInsightsRequest = BaseRequest
VolumeOverTimeRequest = VolumeRequest
LatencyPercentilesOverTimeRequest = LatencyRequest
ErrorRateOverTimeRequest = ErrorRequest
ErrorCorrelationsNPMIRequest = BaseRequest
TokenCostByModelRequest = BaseRequest