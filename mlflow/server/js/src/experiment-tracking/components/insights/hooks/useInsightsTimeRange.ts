import { useCallback, useMemo, useEffect } from 'react';
import { useSearchParams } from '../../../../common/utils/RoutingUtils';

export const INSIGHTS_TIME_RANGE_QUERY_PARAM_KEY = 'insightsTimeRange';
export const INSIGHTS_DATE_NOW_QUERY_PARAM_KEY = 'insightsDateNow';
const INSIGHTS_START_TIME_QUERY_PARAM_KEY = 'insightsStartTime';
const INSIGHTS_END_TIME_QUERY_PARAM_KEY = 'insightsEndTime';

export type InsightsTimeRange =
  | 'LAST_HOUR'
  | 'LAST_24_HOURS'
  | 'LAST_7_DAYS'
  | 'LAST_30_DAYS'
  | 'LAST_YEAR'
  | 'ALL'
  | 'CUSTOM';

export const DEFAULT_INSIGHTS_TIME_RANGE: InsightsTimeRange = 'ALL';

export interface InsightsTimeRangeFilters {
  timeRange?: InsightsTimeRange;
  dateNow?: Date;
  startTime?: string;
  endTime?: string;
}

/**
 * Query param-powered hook that returns the insights time range filters from the URL.
 * Similar to useMonitoringFilters but for insights-specific time management.
 * Stores both the time range selection AND the pinned "NOW" timestamp in URL params.
 */
export const useInsightsTimeRange = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const timeRange =
    (searchParams.get(INSIGHTS_TIME_RANGE_QUERY_PARAM_KEY) as InsightsTimeRange | undefined) || DEFAULT_INSIGHTS_TIME_RANGE;
  
  // Get or create pinned dateNow timestamp from URL
  const dateNowParam = searchParams.get(INSIGHTS_DATE_NOW_QUERY_PARAM_KEY);
  const dateNow = dateNowParam ? new Date(dateNowParam) : new Date();

  let startTime = searchParams.get(INSIGHTS_START_TIME_QUERY_PARAM_KEY) || undefined;
  let endTime = searchParams.get(INSIGHTS_END_TIME_QUERY_PARAM_KEY) ?? undefined;
  
  if (timeRange !== 'CUSTOM') {
    const absoluteStartEndTime = getInsightsAbsoluteStartEndTime(dateNow, { timeRange });
    startTime = absoluteStartEndTime.startTime;
    endTime = absoluteStartEndTime.endTime;
  } else {
    startTime = searchParams.get(INSIGHTS_START_TIME_QUERY_PARAM_KEY) || undefined;
    endTime = searchParams.get(INSIGHTS_END_TIME_QUERY_PARAM_KEY) ?? undefined;
  }

  const timeRangeFilters = useMemo<InsightsTimeRangeFilters>(
    () => ({
      timeRange,
      dateNow,
      startTime,
      endTime,
    }),
    [timeRange, dateNow, startTime, endTime],
  );

  const setTimeRangeFilters = useCallback(
    (filters: InsightsTimeRangeFilters | undefined, replace = false) => {
      setSearchParams(
        (params) => {
          if (filters?.startTime === undefined) {
            params.delete(INSIGHTS_START_TIME_QUERY_PARAM_KEY);
          } else if (filters.timeRange === 'CUSTOM') {
            params.set(INSIGHTS_START_TIME_QUERY_PARAM_KEY, filters.startTime);
          }
          if (filters?.endTime === undefined) {
            params.delete(INSIGHTS_END_TIME_QUERY_PARAM_KEY);
          } else if (filters.timeRange === 'CUSTOM') {
            params.set(INSIGHTS_END_TIME_QUERY_PARAM_KEY, filters.endTime);
          }
          if (filters?.timeRange === undefined) {
            params.delete(INSIGHTS_TIME_RANGE_QUERY_PARAM_KEY);
          } else {
            params.set(INSIGHTS_TIME_RANGE_QUERY_PARAM_KEY, filters.timeRange);
          }
          if (filters?.dateNow === undefined) {
            // Set dateNow if not already in URL (first time loading page)
            if (!params.has(INSIGHTS_DATE_NOW_QUERY_PARAM_KEY)) {
              params.set(INSIGHTS_DATE_NOW_QUERY_PARAM_KEY, new Date().toISOString());
            }
          } else {
            params.set(INSIGHTS_DATE_NOW_QUERY_PARAM_KEY, filters.dateNow.toISOString());
          }
          return params;
        },
        { replace },
      );
    },
    [setSearchParams],
  );

  // Initialize dateNow in URL if not present (first time loading insights)
  useEffect(() => {
    if (!searchParams.has(INSIGHTS_DATE_NOW_QUERY_PARAM_KEY)) {
      setTimeRangeFilters({ dateNow: new Date() }, true);
    }
  }, []); // Only run once on mount

  // Helper function to refresh dateNow (for refresh button)
  const refreshDateNow = useCallback(() => {
    setTimeRangeFilters({ ...timeRangeFilters, dateNow: new Date() }, true);
  }, [timeRangeFilters, setTimeRangeFilters]);

  return [timeRangeFilters, setTimeRangeFilters, refreshDateNow] as const;
};

export function getInsightsAbsoluteStartEndTime(
  dateNow: Date,
  filters: InsightsTimeRangeFilters,
): {
  startTime: string | undefined;
  endTime: string | undefined;
} {
  if (filters.timeRange && filters.timeRange !== 'CUSTOM') {
    return insightsTimeRangeToStartEndTime(dateNow, filters.timeRange);
  }
  return {
    startTime: filters.startTime,
    endTime: filters.endTime,
  };
}

export function insightsTimeRangeToStartEndTime(
  dateNow: Date,
  timeRange: InsightsTimeRange,
): {
  startTime: string | undefined;
  endTime: string | undefined;
} {
  switch (timeRange) {
    case 'LAST_HOUR':
      return {
        startTime: new Date(new Date(dateNow).setUTCHours(dateNow.getUTCHours() - 1)).toISOString(),
        endTime: dateNow.toISOString(),
      };
    case 'LAST_24_HOURS':
      return {
        startTime: new Date(new Date(dateNow).setUTCDate(dateNow.getUTCDate() - 1)).toISOString(),
        endTime: dateNow.toISOString(),
      };
    case 'LAST_7_DAYS':
      return {
        startTime: new Date(new Date(dateNow).setUTCDate(dateNow.getUTCDate() - 7)).toISOString(),
        endTime: dateNow.toISOString(),
      };
    case 'LAST_30_DAYS':
      return {
        startTime: new Date(new Date(dateNow).setUTCDate(dateNow.getUTCDate() - 30)).toISOString(),
        endTime: dateNow.toISOString(),
      };
    case 'LAST_YEAR':
      return {
        startTime: new Date(new Date(dateNow).setUTCFullYear(dateNow.getUTCFullYear() - 1)).toISOString(),
        endTime: dateNow.toISOString(),
      };
    case 'ALL':
      return {
        startTime: undefined,
        endTime: dateNow.toISOString(),
      };
    default:
      throw new Error(`Unexpected insights time range: ${timeRange}`);
  }
}