/**
 * MLflow Trace Insights - Error Rate Card Component
 * 
 * Uses React Query hooks for data fetching with MANDATORY correlations
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { useTraceErrors, useErrorCorrelations } from '../../hooks/useInsightsApi';
import { InsightsCard } from '../../components/InsightsCard';
import { TrendsLineChart } from '../../components/TrendsLineChart';
import { TrendsCorrelationsChart } from '../../components/TrendsCorrelationsChart';
import { TrendsCardSkeleton } from '../../components/TrendsSkeleton';

interface InsightsErrorRateCardProps {
  experimentId?: string;
}

export const InsightsErrorRateCard = ({ experimentId }: InsightsErrorRateCardProps) => {
  const { theme } = useDesignSystemTheme();
  
  // Fetch error data using React Query hook
  const { data: errorData, isLoading, error } = useTraceErrors(
    {
      experiment_ids: experimentId ? [experimentId] : [],
      time_bucket: 'hour',
    },
    { refetchInterval: 30000 } // Auto-refresh every 30 seconds
  );

  // Fetch correlations for error traces
  const { data: correlationsData } = useErrorCorrelations(
    experimentId ? [experimentId] : [],
    { enabled: !!errorData && errorData.summary.error_count > 0 }
  );

  if (isLoading) {
    return <TrendsCardSkeleton />;
  }

  if (error) {
    return (
      <InsightsCard title="Error Rate" error={error}>
        <div style={{ color: theme.colors.textValidationDanger, padding: theme.spacing.lg }}>
          Error loading error rate data
        </div>
      </InsightsCard>
    );
  }

  if (!errorData) {
    return null;
  }

  // Transform time series data for chart
  const chartData = errorData.time_series.map(point => ({
    timeBucket: new Date(point.time_bucket),
    value: point.error_rate,
  }));

  // Transform correlations for display
  const correlations = correlationsData?.data.map(item => ({
    label: `${item.dimension}: ${item.value}`,
    count: item.trace_count,
    npmi: item.npmi_score,
    percentage: item.percentage_of_slice,
    type: 'tag' as const,
  })) || [];

  const getErrorRateColor = (rate: number) => {
    if (rate < 1) return theme.colors.textValidationSuccess;
    if (rate < 5) return theme.colors.yellow400;
    return theme.colors.textValidationDanger;
  };

  return (
    <InsightsCard
      title="Error Rate"
      subtitle={`${errorData.summary.error_count} errors out of ${errorData.summary.total_count} traces`}
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
        <div css={{ flex: 1, textAlign: 'center' }}>
          <div 
            css={{ 
              fontSize: '32px', 
              fontWeight: 700, 
              color: getErrorRateColor(errorData.summary.error_rate) 
            }}
          >
            {errorData.summary.error_rate.toFixed(1)}%
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            Overall Error Rate
          </div>
        </div>
        
        <div css={{ flex: 1, textAlign: 'center' }}>
          <div css={{ fontSize: '24px', fontWeight: 600, color: theme.colors.textValidationDanger }}>
            {errorData.summary.error_count.toLocaleString()}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            Total Errors
          </div>
        </div>
        
        <div css={{ flex: 1, textAlign: 'center' }}>
          <div css={{ fontSize: '24px', fontWeight: 600, color: theme.colors.textPrimary }}>
            {errorData.summary.total_count.toLocaleString()}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            Total Traces
          </div>
        </div>
      </div>

      {/* Time Series Chart */}
      <div css={{ marginBottom: theme.spacing.lg }}>
        <TrendsLineChart
          points={chartData}
          yAxisTitle="Error Rate (%)"
          yAxisFormat=".1%"
          title="Error Rate Over Time"
          lineColors={[theme.colors.textValidationDanger]}
          height={250}
        />
      </div>

      {/* MANDATORY Correlations Section for Errors */}
      {correlations.length > 0 && (
        <div>
          <h4 css={{ 
            margin: `0 0 ${theme.spacing.sm}px 0`,
            fontSize: '14px',
            fontWeight: 600,
            color: theme.colors.textPrimary,
          }}>
            Error Correlations (NPMI)
          </h4>
          <TrendsCorrelationsChart
            title="Error Correlations"
            data={correlations}
            onItemClick={(item) => {
              console.log('Error correlation clicked:', item);
              // TODO: Open trace explorer with filter
            }}
          />
          <div css={{ 
            marginTop: theme.spacing.xs,
            fontSize: '11px',
            color: theme.colors.textSecondary,
          }}>
            Showing top {correlations.length} correlations with error status. 
            Higher NPMI scores indicate stronger correlation with errors.
          </div>
        </div>
      )}
    </InsightsCard>
  );
};