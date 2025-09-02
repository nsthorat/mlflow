/**
 * Shared TypeScript interfaces and types for trends components
 * Ensures type safety and consistency across the trends feature
 */

/**
 * Base props interface shared by all insights page components
 * Since we hit the backend directly, we only need experiment ID
 */
export interface InsightsPageBaseProps {
  /** Experiment ID for context */
  experimentId?: string;
}

/**
 * Legacy alias for backward compatibility with copied trends components
 */
export type TrendsPageBaseProps = InsightsPageBaseProps

/**
 * Time range configuration for queries
 */
export interface TimeRange {
  startTime: string | undefined;
  endTime: string | undefined;
}

/**
 * Simplified type for trace entries 
 * Since we're hitting the backend directly, we only need basic trace info
 */
export type TraceEntry = {
  trace_id?: string;
  [key: string]: any;
};

/**
 * Correlation data for charts and displays
 */
export interface TrendsCorrelationData {
  label: string;
  count: number;
  npmi?: number;
  percentage?: number;
  type: 'tag' | 'tool' | 'assessment' | 'latency';
}

/**
 * Chart data point interface
 */
export interface ChartDataPoint {
  x: string | number;
  y: number;
  [key: string]: string | number | Date | undefined;
}

/**
 * SQL query result row types
 */
export type SqlResultRow = (string | number | boolean | null)[];

/**
 * Time bucket data from SQL queries
 */
export interface TimeBucketData {
  timeBucket: string;
  value: number;
}

/**
 * Latency percentiles data
 */
export interface LatencyPercentilesData {
  timeBucket: string;
  p50: number;
  p90: number;
  p99: number;
}

/**
 * Error rate data over time
 */
export interface ErrorRateData {
  timeBucket: string;
  errorCount: number;
  totalCount: number;
  value: number; // Error rate as percentage (0.0 to 1.0)
}

/**
 * Error state information
 */
export interface TrendsError {
  message: string;
  code?: string;
  retryable?: boolean;
}

/**
 * Trace data structure from the trace API
 */
export interface TraceData {
  info?: {
    trace?: {
      trace_info?: unknown;
    };
    [key: string]: unknown;
  };
  data?: unknown;
  [key: string]: unknown;
}

/**
 * Column types for trace list display - using actual database field names
 */
export type TraceListColumn = 'execution_duration' | 'state' | 'request_time' | 'request' | 'trace_id';

/**
 * Time bucket type for aggregating data over time periods
 */
export type TimeBucket = 'hour' | 'day' | 'week';

/**
 * Dimension metadata type for SQL dimension system
 */
export interface SqlDimensionMetadata {
  id: string;
  name: string;
  description: string;
  type: 'boolean' | 'categorical' | 'numerical';
  parameters?: Record<string, unknown>;
}

/**
 * Dimension filter parameters for dynamic SQL generation
 */
export interface DimensionFilterParams {
  latencyThreshold?: number;
  tagKey?: string;
  tagValue?: string;
  toolName?: string;
  [key: string]: unknown;
}

/**
 * Dimension usage context for correlation analysis
 */
export interface DimensionContext {
  dimensionId: string;
  parameters?: DimensionFilterParams;
  correlationData?: TrendsCorrelationData[];
}

/**
 * Assessment information computed from SQL analysis
 * Similar to getAssessmentInfos but computed via SQL for better performance
 */
export interface AssessmentInfo {
  /** Assessment name */
  name: string;
  /** Data type detected from feedback values */
  dtype: 'boolean' | 'pass-fail' | 'numeric' | 'string';
  /** Source types that created this assessment */
  sources: string[];
  /** Unique values for categorical/string assessments (limited sample) */
  uniqueValues?: string[];
  /** Value range for numeric assessments */
  valueRange?: {
    min: number;
    max: number;
  };
  /** P50 (median) value for numeric assessments */
  p50Value?: number;
  /** The value that represents "passing" for this assessment type */
  passingValue?: string | number | boolean | null;
  /** Sample feedback values for type inference and validation */
  sampleValues: string[];
  /** Total number of assessment instances found */
  sampleCount: number;
}

/**
 * Modal title data for trace explorer modals
 */
export interface TrendsModalTitleData {
  sliceType: 'latency' | 'error' | 'tool' | 'tool-latency' | 'tool-error' | 'tag';
  sliceText: string;
  metricValue?: string;
  metricLabel?: string;
  filterType?: 'tag' | 'tool' | 'assessment' | 'latency';
  filterLabel?: string;
}

/**
 * Assessment data structure from trace queries
 */
export interface TraceAssessment {
  name: string;
  feedback?: {
    value?: string;
    error?: unknown;
  };
  [key: string]: unknown;
}
