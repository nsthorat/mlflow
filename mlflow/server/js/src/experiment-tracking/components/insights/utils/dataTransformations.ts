/**
 * Shared data transformation utilities for trends components
 * Consolidates common data processing functions used across multiple components
 */

import { NPMI_THRESHOLDS } from '../constants/npmiThresholds';
import { SQL_CONSTANTS } from '../constants/chartConfig';

/**
 * Convert milliseconds to seconds
 */
const msToSeconds = (ms: number): number => ms / 1000;

/**
 * Format latency from milliseconds to readable string
 * Shows seconds (with 2 decimals) for values >= 1000ms, otherwise shows milliseconds
 */
export const formatLatency = (ms: number): string => {
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(2)}s`;
  }
  return `${ms.toFixed(0)}ms`;
};

/**
 * Format percentage from decimal to percentage string
 */
export const formatPercentage = (value: number, decimals = 1): string => `${(value * 100).toFixed(decimals)}%`;

/**
 * Format count with locale string (adds commas)
 */
export const formatCount = (count: number): string => count.toLocaleString();

/**
 * Safely parse numeric value with fallback
 */
export const parseNumericValue = (value: any, defaultValue = 0): number => {
  const parsed = Number(value);
  return isNaN(parsed) ? defaultValue : parsed;
};

/**
 * Format numeric value with appropriate precision
 */
export const formatNumericValue = (value: number, precision = 2): string => {
  if (value === 0) return '0';
  if (Math.abs(value) < 0.01) return value.toExponential(2);
  if (Math.abs(value) >= 1000) return value.toLocaleString(undefined, { maximumFractionDigits: precision });
  return value.toFixed(precision);
};

/**
 * Determine optimal latency display format based on the data
 * Returns configuration for displaying latency values with appropriate units
 */
export const getLatencyDisplayConfig = (
  latencyData: Array<{ value: number }> | { p50: number; p90: number; p99: number },
) => {
  let maxValue = 0;

  // Handle different data formats
  if (Array.isArray(latencyData)) {
    maxValue = Math.max(...latencyData.map((d) => d.value));
  } else {
    maxValue = Math.max(latencyData.p50, latencyData.p90, latencyData.p99);
  }

  // If max value >= 1000ms, use seconds
  const useSeconds = maxValue >= 1000;

  return {
    useSeconds,
    yAxisTitle: useSeconds ? 'Latency (s)' : 'Latency (ms)',
    yAxisFormat: useSeconds ? '.1f' : '.0f',
    // Custom format function for y-axis labels with units
    formatValue: (value: number) => {
      if (useSeconds) {
        return `${(value / 1000).toFixed(1)}s`;
      } else {
        return `${Math.round(value)}ms`;
      }
    },
    // Transform data if needed (convert to seconds)
    transformData: <T extends { value: number }>(data: T[]): T[] => {
      if (useSeconds) {
        return data.map((item) => ({
          ...item,
          value: item.value / 1000,
        }));
      }
      return data;
    },
  };
};

/**
 * Calculate percentage from count and total
 */
const calculatePercentage = (count: number, total: number): number => (total > 0 ? (count / total) * 100 : 0);

/**
 * Helper functions for boolean value handling
 */
export const BOOLEAN_VALUE_HELPERS = {
  /**
   * Get all boolean true values in different case formats
   */
  getBooleanTrueValues: () => SQL_CONSTANTS.BOOLEAN_VALUES.TRUE,

  /**
   * Get all boolean false values in different case formats
   */
  getBooleanFalseValues: () => SQL_CONSTANTS.BOOLEAN_VALUES.FALSE,

  /**
   * Get all pass values for pass-fail assessments
   */
  getPassValues: () => SQL_CONSTANTS.PASS_FAIL_VALUES.PASS,

  /**
   * Get all fail values for pass-fail assessments
   */
  getFailValues: () => SQL_CONSTANTS.PASS_FAIL_VALUES.FAIL,

  /**
   * Get combined failure condition values (pass-fail + boolean)
   */
  getFailureConditionValues: () => SQL_CONSTANTS.FAILURE_CONDITIONS.PASS_FAIL_AND_BOOLEAN,

  /**
   * Get SQL IN clause for failure conditions
   */
  getFailureConditionSql: () =>
    `feedback_value IN (${SQL_CONSTANTS.FAILURE_CONDITIONS.PASS_FAIL_AND_BOOLEAN.map((v) => `'${v}'`).join(', ')})`,
} as const;

/**
 * Data processing utilities for chart data
 */
const DATA_PROCESSING = {
  /**
   * Transform time bucket data for charts
   */
  transformTimeBucketData: <T extends { timeBucket: string | Date; value: number }>(
    data: T[],
  ): Array<T & { timeBucket: Date }> => {
    return data.map((item) => ({
      ...item,
      timeBucket: new Date(item.timeBucket),
    }));
  },

  /**
   * Safely convert string/number to number with fallback
   * @deprecated Use parseNumericValue instead
   */
  safeNumberConversion: (value: string | number | undefined, fallback = 0): number => {
    return parseNumericValue(value, fallback);
  },

  /**
   * Calculate NPMI correlation strength using consistent thresholds
   */
  getNPMIStrength: (npmi: number): 'strong' | 'moderate' | 'weak' | 'none' | 'negative' => {
    if (npmi >= NPMI_THRESHOLDS.STRONG_CORRELATION) return 'strong';
    if (npmi >= NPMI_THRESHOLDS.MODERATE_CORRELATION) return 'moderate';
    if (npmi >= NPMI_THRESHOLDS.WEAK_CORRELATION) return 'weak';
    if (npmi > 0.0) return 'none';
    return 'negative';
  },

  /**
   * Transform latency percentiles data for line charts
   */
  transformLatencyPercentiles: (data: Array<{ timeBucket: string; p50: number; p90: number; p99: number }>) => {
    const transformedData: Array<{ timeBucket: Date; value: number; seriesName: string }> = [];

    data.forEach((item) => {
      const timeBucket = new Date(item.timeBucket);

      // Add P50 series
      transformedData.push({
        timeBucket,
        value: item.p50, // Keep in milliseconds
        seriesName: 'P50',
      });

      // Add P90 series
      transformedData.push({
        timeBucket,
        value: item.p90, // Keep in milliseconds
        seriesName: 'P90',
      });

      // Add P99 series
      transformedData.push({
        timeBucket,
        value: item.p99, // Keep in milliseconds
        seriesName: 'P99',
      });
    });

    return transformedData;
  },

  /**
   * Transform error rate data for line charts
   */
  transformErrorRateData: (data: Array<{ timeBucket: string; value: number }>) => {
    return data.map((item) => ({
      timeBucket: new Date(item.timeBucket),
      value: item.value, // Already a percentage (0.0 to 1.0)
    }));
  },
} as const;

/**
 * Constants for common data processing
 */
const PROCESSING_CONSTANTS = {
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
