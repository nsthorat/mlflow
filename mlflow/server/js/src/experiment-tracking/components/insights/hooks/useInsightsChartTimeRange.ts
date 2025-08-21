/**
 * Hook for calculating consistent time domain for all charts based on global time range
 */
import { useMemo } from 'react';
import { useInsightsTimeRange } from './useInsightsTimeRange';

export interface ChartTimeDomain {
  xDomain: [number | undefined, number | undefined];
  startTime: Date | undefined;
  endTime: Date | undefined;
}

/**
 * Hook that provides consistent time domain for all charts based on the global time range selection
 */
export const useInsightsChartTimeRange = (): ChartTimeDomain => {
  const [timeRangeFilters] = useInsightsTimeRange();

  return useMemo(() => {
    const { startTime, endTime } = timeRangeFilters;

    // Parse times to Date objects
    const startDate = startTime ? new Date(startTime) : undefined;
    const endDate = endTime ? new Date(endTime) : undefined;

    // Convert to milliseconds for Plotly xDomain (Plotly expects milliseconds since epoch)
    const xDomain: [number | undefined, number | undefined] = [
      startDate ? startDate.getTime() : undefined,
      endDate ? endDate.getTime() : undefined,
    ];

    return {
      xDomain,
      startTime: startDate,
      endTime: endDate,
    };
  }, [timeRangeFilters]);
};