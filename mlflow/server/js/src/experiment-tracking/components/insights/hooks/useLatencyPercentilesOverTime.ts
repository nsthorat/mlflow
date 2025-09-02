/**
 * MLflow Trace Insights - Latency Percentiles Over Time Hook
 * 
 * High-resolution computational hook following the comprehensive plan.
 * Fetches latency percentiles over time data with time bucketing from REST API endpoints.
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

export interface LatencyPercentilesOverTimePoint {
  time_bucket: string;
  p50_latency_ms: number;
  p90_latency_ms: number;
  p99_latency_ms: number;
  average_latency_ms: number;
}

export interface LatencyPercentilesOverTimeResponse {
  latency_percentiles_over_time: LatencyPercentilesOverTimePoint[];
}

export const useLatencyPercentilesOverTime = (
  experimentId: string | undefined,
  timeRange?: { start?: number; end?: number },
  timeBucket = 'hour'
) => {
  const queryKey = ['insights', 'latency-percentiles', experimentId, timeRange, timeBucket];
  
  const { data, isLoading, error, refetch } = useQuery<LatencyPercentilesOverTimeResponse>({
    queryKey,
    queryFn: async () => {
      if (!experimentId) {
        return { latency_percentiles_over_time: [] };
      }

      const requestParams = {
        experiment_ids: [experimentId],
        time_bucket: timeBucket,
        ...(timeRange?.start && { start_time: timeRange.start }),
        ...(timeRange?.end && { end_time: timeRange.end })
      };

      const response = await fetch('/ajax-api/2.0/mlflow/traces/insights/latency-percentiles-over-time', {
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
    return data?.latency_percentiles_over_time || [];
  }, [data]);

  return {
    data: processedData,
    isLoading,
    error,
    refetch
  };
};