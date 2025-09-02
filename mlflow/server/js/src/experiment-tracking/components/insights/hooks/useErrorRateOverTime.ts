/**
 * MLflow Trace Insights - Error Rate Over Time Hook
 * 
 * High-resolution computational hook following the comprehensive plan.
 * Fetches error rate over time data with time bucketing from REST API endpoints.
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

export interface ErrorRateOverTimePoint {
  time_bucket: string;
  error_count: number;
  total_count: number;
  error_rate: number;
}

export interface ErrorRateOverTimeResponse {
  error_rate_over_time: ErrorRateOverTimePoint[];
}

export const useErrorRateOverTime = (
  experimentId: string | undefined,
  timeRange?: { start?: number; end?: number },
  timeBucket = 'hour'
) => {
  const queryKey = ['insights', 'error-rate', experimentId, timeRange, timeBucket];
  
  const { data, isLoading, error, refetch } = useQuery<ErrorRateOverTimeResponse>({
    queryKey,
    queryFn: async () => {
      if (!experimentId) {
        return { error_rate_over_time: [] };
      }

      const requestParams = {
        experiment_ids: [experimentId],
        time_bucket: timeBucket,
        ...(timeRange?.start && { start_time: timeRange.start }),
        ...(timeRange?.end && { end_time: timeRange.end })
      };

      const response = await fetch('/ajax-api/2.0/mlflow/traces/insights/error-rate-over-time', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestParams),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return response.json();
    },
    enabled: !!experimentId,
    staleTime: 1000 * 60 * 5, // Consider data fresh for 5 minutes
  });

  // Post-process the data using useMemo
  const processedData = useMemo(() => {
    return data?.error_rate_over_time || [];
  }, [data]);

  return {
    data: processedData,
    isLoading,
    error,
    refetch
  };
};