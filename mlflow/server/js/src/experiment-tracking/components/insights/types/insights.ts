/**
 * MLflow Trace Insights TypeScript Types
 * 
 * These types EXACTLY mirror the backend Pydantic models from mlflow/server/trace_insights/models.py
 * DO NOT MODIFY without updating the backend models!
 */

// ============================================================================
// Base Types
// ============================================================================

export type TimeBucket = 'hour' | 'day' | 'week';

// ============================================================================
// Traffic & Cost Types
// ============================================================================

// Volume types
export interface VolumeSummary {
  count: number;
  ok_count: number;
  error_count: number;
}

export interface VolumeTimeSeries {
  time_bucket: number;
  count: number;
  ok_count: number;
  error_count: number;
}

export interface VolumeRequest {
  experiment_ids: string[];
  start_time?: number | null;
  end_time?: number | null;
  time_bucket?: TimeBucket;
  timezone?: string;
}

export interface VolumeResponse {
  summary: VolumeSummary;
  time_series: VolumeTimeSeries[];
}

// Latency types
export interface LatencySummary {
  p50_latency: number | null;
  p90_latency: number | null;
  p99_latency: number | null;
  avg_latency: number | null;
  min_latency: number | null;
  max_latency: number | null;
}

export interface LatencyTimeSeries {
  time_bucket: number;
  p50_latency: number | null;
  p90_latency: number | null;
  p99_latency: number | null;
  avg_latency: number | null;
}

export interface LatencyRequest {
  experiment_ids: string[];
  start_time?: number | null;
  end_time?: number | null;
  time_bucket?: TimeBucket;
}

export interface LatencyResponse {
  summary: LatencySummary;
  time_series: LatencyTimeSeries[];
}

// Error types
export interface ErrorSummary {
  total_count: number;
  error_count: number;
  error_rate: number;
}

export interface ErrorTimeSeries {
  time_bucket: number;
  total_count: number;
  error_count: number;
  error_rate: number;
}

export interface ErrorRequest {
  experiment_ids: string[];
  start_time?: number | null;
  end_time?: number | null;
  time_bucket?: TimeBucket;
}

export interface ErrorResponse {
  summary: ErrorSummary;
  time_series: ErrorTimeSeries[];
}

// ============================================================================
// Assessment Types
// ============================================================================

export type AssessmentType = 'boolean' | 'numeric' | 'string';

export interface AssessmentInfo {
  name: string;
  type: AssessmentType;
  sources: string[];
  trace_count: number;
  unique_values?: number;
  value_range?: {
    min: number;
    max: number;
  };
}

export interface AssessmentDiscoveryRequest {
  experiment_ids: string[];
  start_time?: number | null;
  end_time?: number | null;
}

export interface AssessmentDiscoveryResponse {
  data: AssessmentInfo[];
}

// Boolean assessment types
export interface BooleanAssessmentSummary {
  total_count: number;
  failure_count: number;
  failure_rate: number;
}

export interface BooleanAssessmentTimeSeries {
  time_bucket: number;
  total_count: number;
  failure_count: number;
  failure_rate: number;
}

// Numeric assessment types  
export interface NumericAssessmentSummary {
  avg_value: number | null;
  p50_value: number | null;
  p90_value: number | null;
  p99_value: number | null;
  min_value: number | null;
  max_value: number | null;
}

export interface NumericAssessmentTimeSeries {
  time_bucket: number;
  avg_value: number | null;
  p50_value: number | null;
  p90_value: number | null;
  p99_value: number | null;
}

// String assessment types
export interface StringAssessmentSummary {
  total_count: number;
  unique_values: number;
  top_values: Array<{
    value: string;
    count: number;
    percentage: number;
  }>;
}

export interface AssessmentMetricsRequest {
  experiment_ids: string[];
  assessment_name: string;
  start_time?: number | null;
  end_time?: number | null;
  time_bucket?: TimeBucket;
}

export interface AssessmentMetricsResponse {
  assessment_name: string;
  assessment_type: AssessmentType;
  sources: string[];
  summary: BooleanAssessmentSummary | NumericAssessmentSummary | StringAssessmentSummary;
  time_series: BooleanAssessmentTimeSeries[] | NumericAssessmentTimeSeries[] | Array<any>;
}

// ============================================================================
// Tool Types
// ============================================================================

export interface ToolInfo {
  tool_name: string;
  trace_count: number;
  invocation_count: number;
  error_count: number;
  error_rate: number;
  p50_latency: number | null;
  p90_latency: number | null;
  p99_latency: number | null;
  time_series: {
    volume: VolumeTimeSeries[];
    latency: LatencyTimeSeries[];
    errors: ErrorTimeSeries[];
  };
}

export interface ToolDiscoveryRequest {
  experiment_ids: string[];
  start_time?: number | null;
  end_time?: number | null;
}

export interface ToolDiscoveryResponse {
  data: ToolInfo[];
}

export interface ToolMetricsRequest {
  experiment_ids: string[];
  tool_name: string;
  start_time?: number | null;
  end_time?: number | null;
  time_bucket?: TimeBucket;
}

export interface ToolMetricsResponse {
  data: ToolInfo;
}

// ============================================================================
// Tag Types
// ============================================================================

export interface TagInfo {
  tag_key: string;
  trace_count: number;
  unique_values: number;
}

export interface TagValueInfo {
  value: string;
  count: number;
  percentage: number;
}

export interface TagDiscoveryRequest {
  experiment_ids: string[];
  start_time?: number | null;
  end_time?: number | null;
}

export interface TagDiscoveryResponse {
  data: TagInfo[];
}

export interface TagMetricsRequest {
  experiment_ids: string[];
  tag_key: string;
  start_time?: number | null;
  end_time?: number | null;
  limit?: number;
}

export interface TagMetricsResponse {
  data: {
    tag_key: string;
    trace_count: number;
    unique_values: number;
    top_values: TagValueInfo[];
  };
}

// ============================================================================
// Dimension & Correlation Types
// ============================================================================

export interface DimensionParameter {
  name: string;
  type: string;
  required: boolean;
  default?: any;
}

export interface Dimension {
  name: string;
  type: 'tag' | 'span_attribute' | 'builtin';
  data_type: 'boolean' | 'numeric' | 'string';
  parameters: DimensionParameter[];
}

export interface DimensionDiscoveryRequest {
  experiment_ids: string[];
  start_time?: number | null;
  end_time?: number | null;
}

export interface DimensionDiscoveryResponse {
  data: Dimension[];
}

export interface DimensionValue {
  name: string;
  value: any;
  count: number;
}

export interface IntersectionInfo {
  count: number;
}

export interface CorrelationInfo {
  npmi_score: number;
  strength: 'Strong' | 'Moderate' | 'Weak' | 'None';
}

export interface NPMIRequest {
  experiment_ids: string[];
  dimension1: Record<string, any>;
  dimension2: Record<string, any>;
  start_time?: number | null;
  end_time?: number | null;
}

export interface NPMIResponse {
  dimension1: DimensionValue;
  dimension2: DimensionValue;
  intersection: IntersectionInfo;
  correlation: CorrelationInfo;
}

export interface CorrelationItem {
  dimension: string;
  value: string;
  npmi_score: number;
  trace_count: number;
  percentage_of_slice: number;
  percentage_of_total: number;
  strength: 'Strong' | 'Moderate' | 'Weak' | 'None';
}

export interface CorrelationsRequest {
  experiment_ids: string[];
  filter_string: string;
  correlation_dimensions: string[];
  start_time?: number | null;
  end_time?: number | null;
  limit?: number;
}

export interface CorrelationsResponse {
  data: CorrelationItem[];
}