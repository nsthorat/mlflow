/**
 * MLflow Trace Insights - Latency Card Component
 * 
 * Uses React Query hooks for data fetching with MANDATORY correlations
 */

import React, { useState } from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { useTraceLatency, useLatencyCorrelations } from '../../hooks/useInsightsApi';
import { InsightsCard } from '../../components/InsightsCard';
import { TrendsLineChart } from '../../components/TrendsLineChart';
import { TrendsCorrelationsChart } from '../../components/TrendsCorrelationsChart';
import { TrendsLatencyPercentileSelector } from '../../components/TrendsLatencyPercentileSelector';
import { PercentileThreshold } from '../../constants/percentileColors';
import { TrendsCardSkeleton } from '../../components/TrendsSkeleton';

interface InsightsLatencyCardProps {
  experimentId?: string;
}

export const InsightsLatencyCard = ({ experimentId }: InsightsLatencyCardProps) => {
  const { theme } = useDesignSystemTheme();
  const [selectedPercentile, setSelectedPercentile] = useState<PercentileThreshold>('P50');
  
  // Fetch latency data using React Query hook
  const { data: latencyData, isLoading, error } = useTraceLatency(
    {
      experiment_ids: experimentId ? [experimentId] : [],
      time_bucket: 'hour',
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

  // Transform time series data for chart based on selected percentile
  const chartData = latencyData.time_series.map(point => {
    let value = 0;
    switch (selectedPercentile) {
      case 'P50':
        value = point.p50_latency || 0;
        break;
      case 'P90':
        value = point.p90_latency || 0;
        break;
      case 'P99':
        value = point.p99_latency || 0;
        break;
    }
    return {
      timeBucket: new Date(point.time_bucket),
      value,
    };
  });

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
      subtitle={`Median: ${formatLatency(latencyData.summary.p50_latency)}`}
      headerContent={
        <TrendsLatencyPercentileSelector
          selectedPercentile={selectedPercentile}
          onPercentileChange={setSelectedPercentile}
          latencyData={{
            p50: latencyData.summary.p50_latency || 0,
            p90: latencyData.summary.p90_latency || 0,
            p99: latencyData.summary.p99_latency || 0,
          }}
        />
      }
    >
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
          <div css={{ fontSize: '20px', fontWeight: 600, color: theme.colors.textValidationSuccess }}>
            {formatLatency(latencyData.summary.p50_latency)}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            P50 (Median)
          </div>
        </div>
        
        <div>
          <div css={{ fontSize: '20px', fontWeight: 600, color: theme.colors.yellow400 }}>
            {formatLatency(latencyData.summary.p90_latency)}
          </div>
          <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            P90
          </div>
        </div>
        
        <div>
          <div css={{ fontSize: '20px', fontWeight: 600, color: theme.colors.textValidationDanger }}>
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
          title={`${selectedPercentile.toUpperCase()} Latency`}
          height={250}
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
    </InsightsCard>
  );
};