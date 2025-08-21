/**
 * Time transformation utilities for trends components
 * Provides functions for converting and formatting time-related data
 */

/**
 * Convert milliseconds to seconds
 */
export const msToSeconds = (ms: number): number => ms / 1000;

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
 * Calculate percentage from count and total
 */
export const calculatePercentage = (count: number, total: number): number => (total > 0 ? (count / total) * 100 : 0);

/**
 * Constants for time formatting
 */
// Reserved for future use
const TIME_CONSTANTS = {
  /**
   * Formatting precision
   */
  PRECISION: {
    PERCENTAGE: 1,
    LATENCY_SECONDS: 2,
  },

  /**
   * Default values for missing data
   */
  DEFAULTS: {
    PERCENTAGE: 0,
    COUNT: 0,
    LATENCY_MS: 0,
  },
} as const;
