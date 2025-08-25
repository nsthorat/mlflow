/**
 * Smart date formatting utilities for Insights charts
 * Provides intelligent x-axis date labels based on time bucket granularity
 */

import { format, differenceInDays, addDays, isSameDay } from 'date-fns';

export type TimeBucket = 'hour' | 'day' | 'week';

interface DataPoint {
  timeBucket: Date;
  [key: string]: any;
}

/**
 * Formats a date label based on the time bucket and context
 */
export function formatDateLabel(
  date: Date,
  bucket: TimeBucket,
  index: number,
  allPoints: DataPoint[],
  showAllLabels: boolean = false
): string | null {
  // Skip some labels if we have too many points and showAllLabels is false
  if (!showAllLabels && !shouldShowLabel(index, allPoints.length)) {
    return null;
  }

  const spansDays = checkIfSpansDays(allPoints);
  const dayRange = getDayRange(allPoints);

  switch (bucket) {
    case 'hour':
      return formatHourLabel(date, spansDays);
    case 'day':
      return formatDayLabel(date, dayRange);
    case 'week':
      return formatWeekLabel(date, dayRange);
    default:
      return format(date, 'MMM d');
  }
}

/**
 * Formats hour bucket labels
 */
function formatHourLabel(date: Date, spansDays: boolean): string {
  if (spansDays) {
    // Show "3 PM (8/20)" format when spanning multiple days
    return `${format(date, 'h a')} (${format(date, 'M/d')})`;
  }
  // Just show "3 PM" when all within same day
  return format(date, 'h a');
}

/**
 * Formats day bucket labels
 */
function formatDayLabel(date: Date, dayRange: number): string {
  if (dayRange <= 7) {
    // For last 7 days, show day of week: "Mon 8/20"
    return format(date, 'EEE M/d');
  } else if (dayRange <= 30) {
    // For last 30 days, just show date: "8/20"
    return format(date, 'M/d');
  } else if (dayRange <= 90) {
    // For last 90 days, show month and day: "Aug 20"
    return format(date, 'MMM d');
  } else {
    // For longer ranges, show month and day, year if needed
    const currentYear = new Date().getFullYear();
    if (date.getFullYear() !== currentYear) {
      return format(date, "MMM d ''yy");
    }
    return format(date, 'MMM d');
  }
}

/**
 * Formats week bucket labels
 */
function formatWeekLabel(date: Date, dayRange: number): string {
  const weekEnd = addDays(date, 6);
  
  if (dayRange <= 90) {
    // For shorter ranges, show full week range: "8/20-8/26"
    if (date.getMonth() === weekEnd.getMonth()) {
      // Same month: "Aug 20-26"
      return `${format(date, 'MMM d')}-${format(weekEnd, 'd')}`;
    } else {
      // Different months: "Aug 28 - Sep 3"
      return `${format(date, 'MMM d')} - ${format(weekEnd, 'MMM d')}`;
    }
  } else if (dayRange <= 365) {
    // For yearly view, just show month: "Aug '24"
    return format(date, "MMM ''yy");
  } else {
    // For multi-year, show month and year
    return format(date, 'MMM yyyy');
  }
}

/**
 * Determines if we should show a label at this index based on density
 */
function shouldShowLabel(index: number, totalPoints: number): boolean {
  // Always show first and last
  if (index === 0 || index === totalPoints - 1) {
    return true;
  }

  // Determine step size based on total points
  let step = 1;
  if (totalPoints <= 7) {
    step = 1; // Show all
  } else if (totalPoints <= 14) {
    step = 2; // Show every other
  } else if (totalPoints <= 21) {
    step = 3; // Show every 3rd
  } else if (totalPoints <= 30) {
    step = 4; // Show every 4th
  } else {
    // For very dense data, show ~10 labels total
    step = Math.floor(totalPoints / 10);
  }

  return index % step === 0;
}

/**
 * Gets optimal number of ticks for x-axis
 */
export function getOptimalTickCount(pointCount: number): number {
  if (pointCount <= 7) return pointCount;
  if (pointCount <= 14) return 7;
  if (pointCount <= 21) return 10;
  if (pointCount <= 30) return 12;
  return 15; // Max ticks for readability
}

/**
 * Checks if data points span multiple days
 */
function checkIfSpansDays(points: DataPoint[]): boolean {
  if (points.length <= 1) return false;
  const firstDay = points[0].timeBucket;
  const lastDay = points[points.length - 1].timeBucket;
  return !isSameDay(firstDay, lastDay);
}

/**
 * Gets the day range of the data points
 */
function getDayRange(points: DataPoint[]): number {
  if (points.length === 0) return 0;
  const firstDay = points[0].timeBucket;
  const lastDay = points[points.length - 1].timeBucket;
  return Math.abs(differenceInDays(lastDay, firstDay)) + 1;
}

/**
 * Formats tick labels for Plotly charts
 * Returns arrays of ticktext and tickvals for custom formatting
 */
export function getPlotlyTickConfig(
  points: DataPoint[],
  bucket: TimeBucket
): {
  ticktext: string[];
  tickvals: Date[];
  tickangle: number;
} {
  const labels: string[] = [];
  const values: Date[] = [];
  
  points.forEach((point, index) => {
    const label = formatDateLabel(point.timeBucket, bucket, index, points, false);
    if (label !== null) {
      labels.push(label);
      values.push(point.timeBucket);
    }
  });

  // Determine if we need to angle the labels
  const maxLabelLength = Math.max(...labels.map(l => l.length));
  const needsRotation = maxLabelLength > 10 || labels.length > 10;

  return {
    ticktext: labels,
    tickvals: values,
    tickangle: needsRotation ? -45 : 0,
  };
}

/**
 * Generates tick configuration for a full date range
 * This ensures all days/weeks in the range are shown, not just those with data
 */
export function getPlotlyTickConfigForRange(
  startTime: number,
  endTime: number, 
  bucket: TimeBucket
): {
  ticktext: string[];
  tickvals: Date[];
  tickangle: number;
} {
  const labels: string[] = [];
  const values: Date[] = [];
  
  const startDate = new Date(startTime);
  const endDate = new Date(endTime);
  
  if (bucket === 'day') {
    // Generate a tick for each day in the range
    const currentDate = new Date(startDate);
    currentDate.setHours(0, 0, 0, 0);
    
    while (currentDate <= endDate) {
      const dayRange = Math.abs(differenceInDays(endDate, startDate)) + 1;
      const label = formatDayLabel(new Date(currentDate), dayRange);
      labels.push(label);
      values.push(new Date(currentDate));
      currentDate.setDate(currentDate.getDate() + 1);
    }
  } else if (bucket === 'week') {
    // Generate a tick for each week in the range
    const currentDate = new Date(startDate);
    currentDate.setHours(0, 0, 0, 0);
    // Start from beginning of week (Sunday)
    currentDate.setDate(currentDate.getDate() - currentDate.getDay());
    
    while (currentDate <= endDate) {
      const dayRange = Math.abs(differenceInDays(endDate, startDate)) + 1;
      const label = formatWeekLabel(new Date(currentDate), dayRange);
      labels.push(label);
      values.push(new Date(currentDate));
      currentDate.setDate(currentDate.getDate() + 7);
    }
  } else {
    // For hour buckets, we should limit the number of ticks for readability
    // Generate ticks at reasonable intervals
    const hoursDiff = (endTime - startTime) / (1000 * 60 * 60);
    const interval = hoursDiff <= 24 ? 2 : hoursDiff <= 48 ? 4 : 6;
    
    const currentDate = new Date(startDate);
    currentDate.setMinutes(0, 0, 0);
    
    while (currentDate <= endDate) {
      const spansDays = !isSameDay(startDate, endDate);
      const label = formatHourLabel(new Date(currentDate), spansDays);
      labels.push(label);
      values.push(new Date(currentDate));
      currentDate.setHours(currentDate.getHours() + interval);
    }
  }

  // Determine if we need to angle the labels
  const maxLabelLength = Math.max(...labels.map(l => l.length));
  const needsRotation = maxLabelLength > 10 || labels.length > 10;

  return {
    ticktext: labels,
    tickvals: values,
    tickangle: needsRotation ? -45 : 0,
  };
}

/**
 * Gets a simple date format string for Plotly's tickformat
 * This is a fallback when not using custom tick text
 */
export function getPlotlyDateFormat(bucket: TimeBucket): string {
  switch (bucket) {
    case 'hour':
      return '%I %p'; // "3 PM"
    case 'day':
      return '%b %d'; // "Aug 20"
    case 'week':
      return '%b %d'; // "Aug 20"
    default:
      return '%b %d';
  }
}

/**
 * Formats a date for hover tooltips (always show full precision)
 */
export function formatTooltipDate(date: Date, bucket: TimeBucket): string {
  switch (bucket) {
    case 'hour':
      return format(date, 'MMM d, yyyy h:mm a');
    case 'day':
      return format(date, 'EEEE, MMM d, yyyy');
    case 'week':
      const weekEnd = addDays(date, 6);
      return `Week of ${format(date, 'MMM d')} - ${format(weekEnd, 'MMM d, yyyy')}`;
    default:
      return format(date, 'MMM d, yyyy');
  }
}