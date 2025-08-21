/**
 * Chart configuration constants for trends components
 * Centralizes chart heights, colors, and time-related constants
 */

export const CHART_CONFIG = {
  HEIGHTS: {
    VOLUME_CHART: 125,
    LATENCY_CHART: 150,
    ERROR_RATE_CHART: 150,
    TOOL_CHART: 120,
    DEFAULT: 150,
  },
  COLORS: {
    ERROR_RATE: '#DC2626',
    TRAFFIC: '#077A9D',
    LATENCY: '#059669',
    TOOL: '#077A9D',
  },
  TIME_OFFSETS: {
    CHART_PADDING_MS: 86400000, // 24 hours in milliseconds
  },
  DEFAULTS: {
    MAX_CORRELATION_ITEMS: 5,
    Y_AXIS_FORMAT_PERCENTAGE: '.1%',
    Y_AXIS_FORMAT_SECONDS: '.2f',
  },
  THRESHOLDS: {
    NPMI_CORRELATION_THRESHOLD: 0.7,
  },
} as const;

/**
 * SQL query constants for assessment queries
 * Centralizes SQL conditions and patterns used across queries
 */
export const SQL_CONSTANTS = {
  /**
   * Boolean value patterns for different case variations
   */
  BOOLEAN_VALUES: {
    TRUE: ['true', 'True', 'TRUE'],
    FALSE: ['false', 'False', 'FALSE'],
  },

  /**
   * Pass-fail assessment patterns
   */
  PASS_FAIL_VALUES: {
    PASS: ['"yes"', 'yes', 'YES'],
    FAIL: ['"no"', 'no', 'NO'],
  },

  /**
   * Combined failure condition patterns
   */
  FAILURE_CONDITIONS: {
    PASS_FAIL_AND_BOOLEAN: ['"no"', 'no', 'NO', 'false', 'False', 'FALSE'],
  },

  /**
   * Regex patterns for data type detection
   */
  PATTERNS: {
    NUMERIC: '^-?[0-9]+(\\.[0-9]+)?$',
  },
} as const;

/**
 * Data processing constants for trends components
 * Centralizes default values, formatting precision, and limits
 */
// Reserved for future use
const DATA_PROCESSING_CONSTANTS = {
  /**
   * Default values for missing data
   */
  DEFAULTS: {
    PERCENTAGE: 0,
    COUNT: 0,
    LATENCY_MS: 0,
  },

  /**
   * Formatting precision
   */
  PRECISION: {
    PERCENTAGE: 1,
    LATENCY_SECONDS: 2,
    NPMI: 3,
  },

  /**
   * Chart data limits
   */
  LIMITS: {
    MAX_CORRELATION_ITEMS: 5,
    MAX_TRACE_SAMPLES: 50,
  },
} as const;
