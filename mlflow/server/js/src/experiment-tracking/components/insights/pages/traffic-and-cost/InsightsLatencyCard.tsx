/**
 * MLflow Trace Insights - Latency Card Component
 * 
 * Uses React Query hooks for data fetching with MANDATORY correlations
 */

import React, { useState } from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { useTraceLatency, useLatencyCorrelations } from '../../hooks/useInsightsApi';
import { useInsightsChartTimeRange } from '../../hooks/useInsightsChartTimeRange';
import { useTimeBucket } from '../../hooks/useAutomaticTimeBucket';
import { InsightsCard } from '../../components/InsightsCard';
import { TrendsLineChart } from '../../components/TrendsLineChart';
import { TrendsCorrelationsChart } from '../../components/TrendsCorrelationsChart';
import { TrendsCardSkeleton } from '../../components/TrendsSkeleton';
import { PERCENTILE_COLORS } from '../../constants/percentileColors';
import { NoDataFoundMessage } from '../../components/NoDataFoundMessage';

interface InsightsLatencyCardProps {
  experimentId?: string;
}

export const InsightsLatencyCard = ({ experimentId }: InsightsLatencyCardProps) => {
  const { theme } = useDesignSystemTheme();
  
  // Get chart time domain from global time range
  const { xDomain } = useInsightsChartTimeRange();
  
  // Get automatic time bucket based on time range duration
  const timeBucket = useTimeBucket();
  
  // Fetch latency data using React Query hook
  const { data: latencyData, isLoading, error } = useTraceLatency(
    {
      experiment_ids: experimentId ? [experimentId] : [],
      time_bucket: timeBucket,
    },
    { refetchInterval: 30000 } // Auto-refresh every 30 seconds
  );

  // Fetch correlations for high latency traces (> P99)
  const { data: correlationsData } = useLatencyCorrelations(
    experimentId ? [experimentId] : [],
    latencyData?.summary.p99_latency || 0,
    { enabled: !!latencyData && latencyData.summary.p99_latency !== null }
  );

  if (isLoading) {
    return <TrendsCardSkeleton />;
  }

  if (error) {
    return (
      <InsightsCard title="Latency Distribution" error={error}>
        <div style={{ color: theme.colors.textValidationDanger, padding: theme.spacing.lg }}>
          Error loading latency data
        </div>
      </InsightsCard>
    );
  }

  if (!latencyData) {
    return null;
  }

  // Check if there's no data (check if we have any latency values)
  const hasData = latencyData.summary.p50_latency !== null;

  // Transform time series data for chart - show all three percentiles
  const chartData = [
    ...latencyData.time_series.map(point => ({
      timeBucket: new Date(point.time_bucket),
      value: point.p50_latency || 0,
      seriesName: 'P50',
    })),
    ...latencyData.time_series.map(point => ({
      timeBucket: new Date(point.time_bucket),
      value: point.p90_latency || 0,
      seriesName: 'P90',
    })),
    ...latencyData.time_series.map(point => ({
      timeBucket: new Date(point.time_bucket),
      value: point.p99_latency || 0,
      seriesName: 'P99',
    })),
  ];

  // Transform correlations for display
  const correlations = correlationsData?.data.map(item => ({
    label: `${item.dimension}: ${item.value}`,
    count: item.trace_count,
    npmi: item.npmi_score,
    percentage: item.percentage_of_slice,
    type: 'tag' as const,
  })) || [];

  const formatLatency = (ms: number | null) => {
    if (ms === null) return 'N/A';
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <InsightsCard
      title="Latency Distribution"
      subtitle={hasData ? `Median: ${formatLatency(latencyData.summary.p50_latency)}` : undefined}
    >
      {hasData ? (
        <>
          {/* Summary Statistics */}
          <div
        css={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: theme.spacing.md,
          marginBottom: theme.spacing.lg,
          padding: theme.spacing.md,
          background: theme.colors.backgroundSecondary,
          borderRadius: theme.general.borderRadiusBase,
        }}
      >
        <div>
          <div css={{ fontSize: '20px', fontWeight: 600, color: PERCENTILE_COLORS.P50 }}>
            {formatLatency(latencyData.summary.p50_latency)}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            P50 (Median)
          </div>
        </div>
        
        <div>
          <div css={{ fontSize: '20px', fontWeight: 600, color: PERCENTILE_COLORS.P90 }}>
            {formatLatency(latencyData.summary.p90_latency)}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            P90
          </div>
        </div>
        
        <div>
          <div css={{ fontSize: '20px', fontWeight: 600, color: PERCENTILE_COLORS.P99 }}>
            {formatLatency(latencyData.summary.p99_latency)}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            P99
          </div>
        </div>

        <div>
          <div css={{ fontSize: '20px', fontWeight: 600, color: theme.colors.textPrimary }}>
            {formatLatency(latencyData.summary.avg_latency)}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            Average
          </div>
        </div>

        <div>
          <div css={{ fontSize: '20px', fontWeight: 600, color: theme.colors.textSecondary }}>
            {formatLatency(latencyData.summary.min_latency)}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            Min
          </div>
        </div>

        <div>
          <div css={{ fontSize: '20px', fontWeight: 600, color: theme.colors.textSecondary }}>
            {formatLatency(latencyData.summary.max_latency)}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            Max
          </div>
        </div>
      </div>

      {/* Time Series Chart */}
      <div css={{ marginBottom: theme.spacing.lg }}>
        <TrendsLineChart
          points={chartData}
          yAxisTitle="Latency (ms)"
          title="Latency Percentiles Over Time"
          height={250}
          xDomain={xDomain}
          lineColors={[PERCENTILE_COLORS.P50, PERCENTILE_COLORS.P90, PERCENTILE_COLORS.P99]}
        />
      </div>

      {/* MANDATORY Correlations Section for High Latency */}
      {correlations.length > 0 && (
        <div>
          <h4 css={{ 
            margin: `0 0 ${theme.spacing.sm}px 0`,
            fontSize: '14px',
            fontWeight: 600,
            color: theme.colors.textPrimary,
          }}>
            High Latency Correlations (≥ P99)
          </h4>
          <TrendsCorrelationsChart
            title="High Latency Correlations"
            data={correlations}
            onItemClick={(item) => {
              console.log('Latency correlation clicked:', item);
              // TODO: Open trace explorer with filter
            }}
          />
        </div>
      )}
        </>
      ) : (
        <NoDataFoundMessage />
      )}
    </InsightsCard>
  );
};