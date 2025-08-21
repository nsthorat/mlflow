/**
 * Hook for automatically calculating optimal time bucket size based on time range duration
 * 
 * Bucket sizing strategy:
 * - ≤ 2 days (48 hours): 'hour' bucket → up to 48 data points
 * - 2 days - 4 weeks: 'day' bucket → 2-28 data points  
 * - > 4 weeks: 'week' bucket → varies
 * 
 * Target: 20-50 data points for optimal chart readability
 */
import { useMemo } from 'react';
import { useInsightsTimeRange } from './useInsightsTimeRange';
import { TimeBucket } from '../types/insights';

export interface AutomaticTimeBucketResult {
  bucket: TimeBucket;
  estimatedDataPoints: number;
  rationale: string;
}

/**
 * Hook that automatically calculates the optimal time bucket based on the selected time range
 */
export const useAutomaticTimeBucket = (): AutomaticTimeBucketResult => {
  const [timeRangeFilters] = useInsightsTimeRange();

  return useMemo(() => {
    const { startTime, endTime } = timeRangeFilters;

    // Handle "All time" or missing time range - default to daily buckets
    if (!startTime || !endTime) {
      const result = {
        bucket: 'day' as TimeBucket,
        estimatedDataPoints: 30, // Rough estimate
        rationale: 'All time range - using daily buckets'
      };
      console.log('🕒 Automatic Time Bucket:', result);
      return result;
    }

    // Calculate duration
    const startDate = new Date(startTime);
    const endDate = new Date(endTime);
    const durationMs = endDate.getTime() - startDate.getTime();
    const durationHours = durationMs / (1000 * 60 * 60);
    const durationDays = durationHours / 24;
    const durationWeeks = durationDays / 7;

    // Apply bucket sizing rules with current backend constraints
    let result: AutomaticTimeBucketResult;
    
    if (durationHours <= 48) { // ≤ 2 days
      result = {
        bucket: 'hour' as TimeBucket,
        estimatedDataPoints: Math.ceil(durationHours),
        rationale: `${durationHours.toFixed(1)} hours - using hourly buckets`
      };
    } else if (durationDays <= 28) { // ≤ 4 weeks
      result = {
        bucket: 'day' as TimeBucket,
        estimatedDataPoints: Math.ceil(durationDays),
        rationale: `${durationDays.toFixed(1)} days - using daily buckets`
      };
    } else { // > 4 weeks
      result = {
        bucket: 'week' as TimeBucket,
        estimatedDataPoints: Math.ceil(durationWeeks),
        rationale: `${durationWeeks.toFixed(1)} weeks - using weekly buckets`
      };
    }
    
    console.log('🕒 Automatic Time Bucket:', result);
    return result;
  }, [timeRangeFilters]);
};

/**
 * Simplified hook that returns just the bucket size (most common use case)
 */
export const useTimeBucket = (): TimeBucket => {
  const { bucket } = useAutomaticTimeBucket();
  return bucket;
};