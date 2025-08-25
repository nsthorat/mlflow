/**
 * Chart utilities for MLflow Trace Insights
 * 
 * Provides consistent chart behavior across all insights components,
 * including proper x-axis domain handling when there's no data.
 */

import { TimeBucket } from '../types/insightsTypes';

/**
 * Configuration for rendering a chart, including whether to show it with no data
 */
export interface ChartRenderConfig {
  /** Whether there is actual data to display */
  hasData: boolean;
  /** Whether to show the chart even when there's no data (for x-axis labels) */
  showChartWithoutData: boolean;
  /** Message to show when there's no data and chart is hidden */
  noDataMessage?: string;
}

/**
 * Determines how a chart should be rendered based on data availability and domain
 * 
 * @param hasData - Whether there is actual data to display
 * @param xDomain - X-axis domain [start, end] in milliseconds
 * @param showXAxisWithoutData - Whether to always show x-axis when xDomain is provided
 * @returns Configuration for rendering the chart
 */
export function getChartRenderConfig(
  hasData: boolean,
  xDomain?: [number | undefined, number | undefined],
  showXAxisWithoutData: boolean = true
): ChartRenderConfig {
  const hasValidDomain = xDomain && xDomain[0] !== undefined && xDomain[1] !== undefined;
  
  return {
    hasData,
    showChartWithoutData: !hasData && showXAxisWithoutData && hasValidDomain,
    noDataMessage: hasData ? undefined : 'No data found for this time range'
  };
}

/**
 * Common interface for chart data points with time buckets
 */
export interface TimeSeriesPoint {
  timeBucket: Date;
  [key: string]: any;
}

/**
 * Applies timezone adjustment for day/week time buckets
 * 
 * The backend returns UTC timestamps that represent timezone boundaries.
 * For day/week buckets, we need to adjust them to display correct local dates.
 * 
 * @param points - Array of time series points
 * @param timeBucket - Time bucket granularity
 * @returns Adjusted points with correct timezone display
 */
export function adjustTimezoneForTimeBucket<T extends TimeSeriesPoint>(
  points: T[],
  timeBucket: TimeBucket
): T[] {
  if (timeBucket !== 'day' && timeBucket !== 'week') {
    return points; // No adjustment needed for hourly data
  }
  
  return points.map(point => {
    const date = new Date(point.timeBucket);
    
    // For day/week buckets, adjust the timestamp to show correct local date
    // The backend returns UTC midnight, but we want to display local midnight
    const offsetMs = date.getTimezoneOffset() * 60 * 1000;
    date.setTime(date.getTime() + offsetMs);
    
    return {
      ...point,
      timeBucket: date
    };
  });
}

/**
 * Creates empty chart data points for a given time range and bucket
 * Used to show x-axis labels even when there's no actual data
 * 
 * @param xDomain - Time range [start, end] in milliseconds  
 * @param timeBucket - Time bucket granularity
 * @param defaultValue - Default value to use for data points
 * @returns Array of empty data points covering the time range
 */
export function createEmptyTimeSeriesPoints(
  xDomain: [number, number],
  timeBucket: TimeBucket,
  defaultValue: number = 0
): TimeSeriesPoint[] {
  const [startTime, endTime] = xDomain;
  const points: TimeSeriesPoint[] = [];
  
  const startDate = new Date(startTime);
  const endDate = new Date(endTime);
  
  if (timeBucket === 'hour') {
    // Create hourly points
    const current = new Date(startDate);
    current.setMinutes(0, 0, 0); // Round to hour
    
    while (current <= endDate) {
      points.push({
        timeBucket: new Date(current),
        value: defaultValue
      });
      current.setHours(current.getHours() + 1);
    }
  } else if (timeBucket === 'day') {
    // Create daily points
    const current = new Date(startDate);
    current.setHours(0, 0, 0, 0); // Round to day
    
    while (current <= endDate) {
      points.push({
        timeBucket: new Date(current),
        value: defaultValue
      });
      current.setDate(current.getDate() + 1);
    }
  } else if (timeBucket === 'week') {
    // Create weekly points
    const current = new Date(startDate);
    current.setHours(0, 0, 0, 0);
    // Start from beginning of week (Sunday)
    current.setDate(current.getDate() - current.getDay());
    
    while (current <= endDate) {
      points.push({
        timeBucket: new Date(current),
        value: defaultValue
      });
      current.setDate(current.getDate() + 7);
    }
  }
  
  return points;
}

/**
 * Utility to determine if a chart should show data or empty state
 * 
 * @param hasData - Whether there is actual data
 * @param renderConfig - Chart render configuration
 * @returns Whether to show the chart component
 */
export function shouldShowChart(hasData: boolean, renderConfig: ChartRenderConfig): boolean {
  return hasData || renderConfig.showChartWithoutData;
}