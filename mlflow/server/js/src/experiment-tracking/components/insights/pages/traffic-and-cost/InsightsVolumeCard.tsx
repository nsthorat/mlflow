/**
 * MLflow Trace Insights - Volume Card Component
 * 
 * Uses React Query hooks for data fetching with MANDATORY correlations
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { useTraceVolume, useCorrelations } from '../../hooks/useInsightsApi';
import { InsightsCard } from '../../components/InsightsCard';
import { TrendsLineChart } from '../../components/TrendsLineChart';
import { TrendsCorrelationsChart } from '../../components/TrendsCorrelationsChart';
import { TrendsCardSkeleton } from '../../components/TrendsSkeleton';

interface InsightsVolumeCardProps {
  experimentId?: string;
}

export const InsightsVolumeCard = ({ experimentId }: InsightsVolumeCardProps) => {
  const { theme } = useDesignSystemTheme();
  
  // Fetch volume data using React Query hook
  const { data: volumeData, isLoading, error } = useTraceVolume(
    {
      experiment_ids: experimentId ? [experimentId] : [],
      time_bucket: 'hour',
    },
    { refetchInterval: 30000 } // Auto-refresh every 30 seconds
  );

  // Fetch correlations for high-volume periods
  const { data: correlationsData } = useCorrelations(
    {
      experiment_ids: experimentId ? [experimentId] : [],
      filter_string: 'volume:high',
      correlation_dimensions: ['tag'],
      limit: 5,
    },
    { enabled: !!volumeData && volumeData.summary.count > 0 }
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

  // Transform time series data for chart
  const chartData = volumeData.time_series.map(point => ({
    timeBucket: new Date(point.time_bucket),
    value: point.count,
    successful: point.ok_count,
    errors: point.error_count,
  }));

  // Transform correlations for display
  const correlations = correlationsData?.data.map(item => ({
    label: `${item.dimension}: ${item.value}`,
    count: item.trace_count,
    npmi: item.npmi_score,
    percentage: item.percentage_of_slice,
    type: 'tag' as const,
  })) || [];

  return (
    <InsightsCard
      title="Volume Over Time"
      subtitle={`${volumeData.summary.count} total traces`}
    >
      {/* Summary Statistics */}
      <div
        css={{
          display: 'flex',
          gap: theme.spacing.lg,
          marginBottom: theme.spacing.lg,
          padding: theme.spacing.md,
          background: theme.colors.backgroundSecondary,
          borderRadius: theme.general.borderRadiusBase,
        }}
      >
        <div css={{ flex: 1 }}>
          <div css={{ fontSize: '24px', fontWeight: 600, color: theme.colors.textValidationSuccess }}>
            {volumeData.summary.ok_count.toLocaleString()}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            Successful Traces
          </div>
        </div>
        
        <div css={{ flex: 1 }}>
          <div css={{ fontSize: '24px', fontWeight: 600, color: theme.colors.textValidationDanger }}>
            {volumeData.summary.error_count.toLocaleString()}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            Error Traces
          </div>
        </div>
        
        <div css={{ flex: 1 }}>
          <div css={{ fontSize: '24px', fontWeight: 600, color: theme.colors.textPrimary }}>
            {volumeData.summary.count.toLocaleString()}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            Total Traces
          </div>
        </div>

        <div css={{ flex: 1 }}>
          <div css={{ fontSize: '24px', fontWeight: 600, color: theme.colors.actionDangerPrimaryBackgroundDefault }}>
            {((volumeData.summary.error_count / volumeData.summary.count) * 100).toFixed(1)}%
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            Error Rate
          </div>
        </div>
      </div>

      {/* Time Series Chart */}
      <div css={{ marginBottom: theme.spacing.lg }}>
        <TrendsLineChart
          points={chartData}
          yAxisTitle="Trace Count"
          title="Volume Over Time"
          height={300}
        />
      </div>

      {/* MANDATORY Correlations Section */}
      {correlations.length > 0 && (
        <div>
          <h4 css={{ 
            margin: `0 0 ${theme.spacing.sm}px 0`,
            fontSize: '14px',
            fontWeight: 600,
            color: theme.colors.textPrimary,
          }}>
            Top Correlations
          </h4>
          <TrendsCorrelationsChart
            title="Top Correlations"
            data={correlations}
            onItemClick={(item) => {
              console.log('Correlation clicked:', item);
              // TODO: Open trace explorer with filter
            }}
          />
        </div>
      )}
    </InsightsCard>
  );
};