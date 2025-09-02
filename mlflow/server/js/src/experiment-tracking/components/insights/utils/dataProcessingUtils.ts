/**
 * Data processing utilities for trends components
 * Provides functions for transforming and processing chart data
 */

import { NPMI_THRESHOLDS } from '../constants/npmiThresholds';
import { TimeBucket } from '../types/insightsTypes';

/**
 * Transform time bucket data for charts
 */
export const transformTimeBucketData = <T extends { timeBucket: string | Date; value: number }>(
  data: T[],
): Array<T & { timeBucket: Date }> => {
  return data.map((item) => ({
    ...item,
    timeBucket: new Date(item.timeBucket),
  }));
};

/**
 * Safely convert string/number to number with fallback
 */
export const safeNumberConversion = (value: string | number | undefined, fallback = 0): number => {
  const num = Number(value);
  return isNaN(num) ? fallback : num;
};

/**
 * Calculate NPMI correlation strength using consistent thresholds
 */
export const getNPMIStrength = (npmi: number): 'strong' | 'moderate' | 'weak' | 'none' | 'negative' => {
  if (npmi >= NPMI_THRESHOLDS.STRONG_CORRELATION) return 'strong';
  if (npmi >= NPMI_THRESHOLDS.MODERATE_CORRELATION) return 'moderate';
  if (npmi >= NPMI_THRESHOLDS.WEAK_CORRELATION) return 'weak';
  if (npmi > 0.0) return 'none';
  return 'negative';
};

/**
 * Transform latency percentiles data for line charts
 */
export const transformLatencyPercentiles = (
  data: Array<{ timeBucket: string; p50: number; p90: number; p99: number }>,
) => {
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
};

/**
 * Transform error rate data for line charts
 */
export const transformErrorRateData = (data: Array<{ timeBucket: string; value: number }>) => {
  return data.map((item) => ({
    timeBucket: new Date(item.timeBucket),
    value: item.value, // Already a percentage (0.0 to 1.0)
  }));
};

/**
 * Truncate a date to the specified time bucket
 */
export const truncateDate = (date: Date, timeBucket: TimeBucket): Date => {
  const truncated = new Date(date);

  switch (timeBucket) {
    case 'week':
      const dayOfWeek = truncated.getUTCDay();
      truncated.setUTCDate(truncated.getUTCDate() - dayOfWeek);
      truncated.setUTCHours(0, 0, 0, 0);
      break;
    case 'day':
      truncated.setUTCHours(0, 0, 0, 0);
      break;
    case 'hour':
      truncated.setUTCMinutes(0, 0, 0);
      break;
  }

  return truncated;
};
