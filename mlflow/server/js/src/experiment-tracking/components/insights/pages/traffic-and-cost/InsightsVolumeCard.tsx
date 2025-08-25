/**
 * MLflow Trace Insights - Volume Card Component
 * 
 * Uses React Query hooks for data fetching
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { useTraceVolume } from '../../hooks/useInsightsApi';
import { useInsightsChartTimeRange } from '../../hooks/useInsightsChartTimeRange';
import { useTimeBucket } from '../../hooks/useAutomaticTimeBucket';
import { InsightsCard } from '../../components/InsightsCard';
import { TrendsLineChart } from '../../components/TrendsLineChart';
import { TrendsCardSkeleton } from '../../components/TrendsSkeleton';
import { NoDataFoundMessage } from '../../components/NoDataFoundMessage';

interface InsightsVolumeCardProps {
  experimentId?: string;
}

export const InsightsVolumeCard = ({ experimentId }: InsightsVolumeCardProps) => {
  const { theme } = useDesignSystemTheme();
  
  // Get chart time domain from global time range
  const { xDomain } = useInsightsChartTimeRange();
  
  // Get automatic time bucket based on time range duration
  const timeBucket = useTimeBucket();
  
  // Fetch volume data using React Query hook - time range comes from URL
  const { data: volumeData, isLoading, error } = useTraceVolume(
    {
      experiment_ids: experimentId ? [experimentId] : [],
      time_bucket: timeBucket,
    },
    { refetchInterval: 30000 } // Auto-refresh every 30 seconds
  );


  if (isLoading) {
    return <TrendsCardSkeleton />;
  }

  if (error) {
    return (
      <InsightsCard title="Volume Over Time" error={error}>
        <div style={{ color: theme.colors.textValidationDanger, padding: theme.spacing.lg }}>
          Error loading volume data
        </div>
      </InsightsCard>
    );
  }

  if (!volumeData) {
    return null;
  }

  // Check if there's no data
  const hasData = volumeData.summary.count > 0;

  // Transform time series data for chart
  // For daily/weekly buckets, the backend returns UTC timestamps that represent
  // local timezone boundaries. We need to adjust them for proper display.
  const chartData = volumeData.time_series.map(point => {
    const date = new Date(point.time_bucket);
    
    // For day/week buckets, adjust the timestamp to show correct local date
    if (timeBucket === 'day' || timeBucket === 'week') {
      // The backend returns UTC midnight, but we want to display local midnight
      // Add the timezone offset to compensate
      const offsetMs = date.getTimezoneOffset() * 60 * 1000;
      date.setTime(date.getTime() + offsetMs);
    }
    
    return {
      timeBucket: date,
      value: point.count,
      successful: point.ok_count,
      errors: point.error_count,
    };
  });

  return (
    <InsightsCard
      title="Traffic"
      subtitle={
        hasData ? (
          <div css={{ fontSize: '18px', fontWeight: 300, color: '#000' }}>
            {volumeData.summary.count.toLocaleString()} traces
          </div>
        ) : undefined
      }
    >
      {/* Always show the chart - it will display x-axis labels even with no data when xDomain is provided */}
      <div>
        <TrendsLineChart
          points={chartData}
          yAxisTitle="Trace Count"
          title="Volume Over Time"
          timeBucket={timeBucket}
          height={200}
          xDomain={xDomain}
          yAxisFormat="d"
          yDomain={[0, undefined]}
          leftMargin={30}
          yAxisOptions={{ rangemode: 'tozero' }}
        />
      </div>
      
      {/* Show "no data" message below the chart when there's no data */}
      {!hasData && (
        <div css={{ marginTop: theme.spacing.md }}>
          <NoDataFoundMessage minHeight={100} />
        </div>
      )}
    </InsightsCard>
  );
};