/**
 * MLflow Trace Insights - Volume Over Time Hook
 * 
 * High-resolution computational hook following the comprehensive plan.
 * Fetches volume over time data with time bucketing from REST API endpoints.
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

// Backend response format
export interface VolumeOverTimeBackendPoint {
  time_bucket: string;
  ok_count: number;
  error_count: number;
  count: number;
}

// Frontend normalized format
export interface VolumeOverTimePoint {
  time_bucket: string;
  successful_traces: number;
  error_traces: number;
  total_traces: number;
}

export interface VolumeOverTimeResponse {
  volume_over_time: VolumeOverTimeBackendPoint[];
}

export const useVolumeOverTime = (
  experimentId: string | undefined,
  timeRange?: { start?: number; end?: number },
  timeBucket = 'hour'
) => {
  const queryKey = ['insights', 'volume-over-time', experimentId, timeRange, timeBucket];
  
  const { data, isLoading, error, refetch } = useQuery<VolumeOverTimeResponse>({
    queryKey,
    queryFn: async () => {
      if (!experimentId) {
        return { volume_over_time: [] };
      }

      const requestParams = {
        experiment_ids: [experimentId],
        time_bucket: timeBucket,
        ...(timeRange?.start && { start_time: timeRange.start }),
        ...(timeRange?.end && { end_time: timeRange.end })
      };

      const response = await fetch('/ajax-api/2.0/mlflow/traces/insights/volume-over-time', {
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

  // Post-process the data using useMemo to normalize field names
  const processedData = useMemo(() => {
    if (!data?.volume_over_time) return [];
    
    // Map backend field names to frontend field names
    return data.volume_over_time.map(point => ({
      time_bucket: point.time_bucket,
      successful_traces: point.ok_count || 0,
      error_traces: point.error_count || 0,
      total_traces: point.count || 0,
    }));
  }, [data]);

  return {
    data: processedData,
    isLoading,
    error,
    refetch
  };
};