/**
 * SQL query constants for trends components
 * Centralizes field names, query values, and database-related constants
 */

/**
 * Global flag to enable SQL query logging
 * Set to true to enable console.log for all SQL queries in trends
 */
export const ENABLE_SQL_LOGGING = false;

export const SQL_FIELDS = {
  REQUEST_TIME: 'request_time',
  EXECUTION_DURATION: 'execution_duration_ms',
  STATE: 'state',
  TRACE_ID: 'trace_id',
  CLIENT_REQUEST_ID: 'client_request_id',
  TAGS: 'tags',
  TOOL_NAME: 'request_metadata.inputs.tool_name',
} as const;

export const SQL_VALUES = {
  ERROR_STATE: 'ERROR',
  SUCCESS_STATE: 'OK',
  PERCENTILES: {
    P50: 0.5,
    P90: 0.9,
    P99: 0.99,
  },
} as const;

// Reserved for future use
const PERCENTILE_KEYS = ['p50', 'p90', 'p99'] as const;

const TIME_BUCKET_INTERVALS = {
  HOUR: 'INTERVAL 1 HOUR',
  DAY: 'INTERVAL 1 DAY',
  WEEK: 'INTERVAL 1 WEEK',
} as const;

/**
 * Helper to build time conditions for queries
 * Returns an AND clause with time range filtering, or empty string if no time range provided
 */
export const buildTimeCondition = (startTime?: string, endTime?: string): string => {
  if (!startTime || !endTime) return '';
  return `AND ${SQL_FIELDS.REQUEST_TIME} >= '${startTime}' AND ${SQL_FIELDS.REQUEST_TIME} <= '${endTime}'`;
};
