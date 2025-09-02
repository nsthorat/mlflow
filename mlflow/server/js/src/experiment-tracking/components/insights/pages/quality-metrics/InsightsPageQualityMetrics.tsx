/**
 * MLflow Trace Insights - Quality Metrics Page
 * 
 * Displays assessment analysis and quality scoring
 * According to PRD: insights_ui_prd.md lines 115-179
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { useAssessmentDiscovery, useAssessmentData, useCorrelations } from '../../hooks/useInsightsApi';
import { useInsightsChartTimeRange } from '../../hooks/useInsightsChartTimeRange';
import { useTimeBucket } from '../../hooks/useAutomaticTimeBucket';
import { useIntersectionObserver } from '../../hooks/useIntersectionObserver';
import { InsightsCard } from '../../components/InsightsCard';
import { TrendsLineChart } from '../../components/TrendsLineChart';
import { TrendsCorrelationsChart } from '../../components/TrendsCorrelationsChart';
import { TrendsCardSkeleton, TrendsEmptyState } from '../../components/TrendsSkeleton';
import { NumericValueSelector } from '../../components/NumericValueSelector';
import { DataTypeTag } from '../../components/DataTypeTag';

interface InsightsPageQualityMetricsProps {
  experimentId?: string;
}

export const InsightsPageQualityMetrics = ({ experimentId }: InsightsPageQualityMetricsProps) => {
  const { theme } = useDesignSystemTheme();
  
  // Get chart time domain from global time range
  const { xDomain } = useInsightsChartTimeRange();
  
  // Get automatic time bucket based on time range duration
  const timeBucket = useTimeBucket();
  
  // Discover all assessments in the time window
  // Handle experimentId properly - "0" is a valid experiment ID
  const experimentIds = experimentId !== undefined && experimentId !== null ? [experimentId] : [];
  const { data: assessmentsData, isLoading, error } = useAssessmentDiscovery(
    experimentIds,
    { refetchInterval: 60000 } // Refresh every minute
  );

  if (isLoading) {
    return (
      <div css={{ padding: theme.spacing.lg }}>
        <h2>Quality Metrics</h2>
        <div css={{ 
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: theme.spacing.lg,
          marginTop: theme.spacing.lg,
        }}>
          <TrendsCardSkeleton />
          <TrendsCardSkeleton />
          <TrendsCardSkeleton />
          <TrendsCardSkeleton />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div css={{ padding: theme.spacing.lg }}>
        <h2>Quality Metrics</h2>
        <TrendsEmptyState
          title="Error loading assessments"
          description="Unable to fetch assessment data. Please try again later."
        />
      </div>
    );
  }

  if (!assessmentsData || !assessmentsData.assessments || assessmentsData.assessments.length === 0) {
    return (
      <div css={{ padding: theme.spacing.lg }}>
        <h2>Quality Metrics</h2>
        <TrendsEmptyState
          title="No assessments found"
          description="No assessment data available for the selected time range."
        />
      </div>
    );
  }

  return (
    <div css={{ padding: theme.spacing.lg }}>
      <h2>Quality Metrics</h2>
      
      {/* Two-column card layout for assessments */}
      <div css={{ 
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: theme.spacing.lg,
        marginTop: theme.spacing.lg,
      }}>
        {assessmentsData.assessments.map((assessment) => (
          <AssessmentCard
            key={assessment.name}
            assessment={assessment}
            experimentId={experimentId}
            xDomain={xDomain}
            timeBucket={timeBucket}
          />
        ))}
      </div>
    </div>
  );
};

// Individual Assessment Card Component
interface AssessmentCardProps {
  assessment: {
    name: string;
    data_type: 'boolean' | 'pass-fail' | 'numeric' | 'string';
    source: string;
    count: number;
  };
  experimentId?: string;
  xDomain?: [number | undefined, number | undefined];
  timeBucket: 'hour' | 'day' | 'week';
}

const AssessmentCard: React.FC<AssessmentCardProps> = ({ assessment, experimentId, xDomain, timeBucket }) => {
  const { theme } = useDesignSystemTheme();
  
  // Use intersection observer to detect when assessment card is in view
  const [cardRef, isInView] = useIntersectionObserver();
  
  // Handle experimentId properly - "0" is a valid experiment ID
  const experimentIds = experimentId !== undefined && experimentId !== null ? [experimentId] : [];
  
  // Fetch detailed assessment data with the correct time bucket
  // Only fetch when the card is in view
  const { data: assessmentData, isLoading } = useAssessmentData(
    assessment.name,
    experimentIds,
    { 
      refetchInterval: 30000,
      enabled: isInView  // Only fetch when the card is in view
    },
    timeBucket  // Pass the time bucket to the hook
  );

  // Fetch correlations for assessment failures/below P50
  const { data: correlationsData } = useCorrelations(
    {
      experiment_ids: experimentIds,
      filter_string: assessment.data_type === 'boolean' 
        ? `assessment.${assessment.name}:false`
        : assessment.data_type === 'numeric'
        ? `assessment.${assessment.name}:below_p50`
        : '',
      correlation_dimensions: ['tag', 'tool'],
      limit: 5,
    },
    { 
      enabled: !!assessmentData && assessment.data_type !== 'string' && isInView,  // Only fetch when in view and has data
    }
  );

  // Always show skeleton for cards not in view yet
  if (!isInView || isLoading) {
    return (
      <div ref={cardRef}>
        <TrendsCardSkeleton />
      </div>
    );
  }

  // Transform correlations for display
  const correlations = correlationsData?.data.map(item => ({
    label: `${item.dimension}: ${item.value}`,
    count: item.trace_count,
    npmi: item.npmi_score,
    percentage: item.percentage_of_slice,
    type: item.dimension.startsWith('tag') ? 'tag' as const : 'tool' as const,
  })) || [];


  // Render based on assessment type
  if ((assessment.data_type === 'boolean' || assessment.data_type === 'pass-fail') && assessmentData) {
    const failureRate = assessmentData.summary.failure_rate || 0;
    const chartData = assessmentData.time_series.map(point => ({
      timeBucket: new Date(point.time_bucket),
      value: (point.failure_rate || 0) / 100, // Convert to decimal for Plotly percentage format
    }));

    return (
      <div ref={cardRef}>
        <InsightsCard
        title={
          <span>
            {assessment.name}
            <DataTypeTag dataType={assessment.data_type} />
          </span>
        }
        subtitle={
          <div css={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: theme.spacing.md,
          }}>
            <div>
              <div css={{ 
                fontSize: '18px', 
                fontWeight: 300, 
                color: failureRate > 10 ? theme.colors.textValidationDanger : theme.colors.textValidationSuccess,
              }}>
                {failureRate.toFixed(1)}%
              </div>
              <div css={{ fontSize: '11px', color: theme.colors.textSecondary }}>
                Failure Rate
              </div>
            </div>
            <div>
              <div css={{ fontSize: '18px', fontWeight: 300, color: '#000' }}>
                {assessmentData.summary.total_count}
              </div>
              <div css={{ fontSize: '11px', color: theme.colors.textSecondary }}>
                Assessments
              </div>
            </div>
          </div>
        }
      >
        {/* Failure Rate Chart */}
        <TrendsLineChart
          points={chartData}
          yAxisTitle="Failure Rate (%)"
          yAxisFormat=".1%"
          title="Failure Rate Over Time"
          timeBucket={timeBucket}
          lineColors={[theme.colors.textValidationDanger]}
          height={200}
          xDomain={xDomain}
          yAxisOptions={{
            rangemode: 'tozero', // Always include zero but auto-scale the maximum
          }}
        />
        </InsightsCard>
      </div>
    );
  }

  if (assessment.data_type === 'numeric' && assessmentData) {
    const chartData = assessmentData.time_series.map(point => ({
      timeBucket: new Date(point.time_bucket),
      value: point.p50_value || 0,
    }));

    return (
      <div ref={cardRef}>
        <InsightsCard
        title={
          <span>
            {assessment.name}
            <DataTypeTag dataType={assessment.data_type} />
          </span>
        }
        subtitle={
          <div css={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: theme.spacing.md,
          }}>
            <div>
              <div css={{ fontSize: '18px', fontWeight: 300, color: '#000' }}>
                {assessmentData.summary.total_count}
              </div>
              <div css={{ fontSize: '11px', color: theme.colors.textSecondary }}>
                Assessments
              </div>
            </div>
            <div>
              <NumericValueSelector 
                values={{
                  p50: assessmentData.summary.p50_value,
                  p90: assessmentData.summary.p90_value,
                  p99: assessmentData.summary.p99_value,
                }}
              />
            </div>
          </div>
        }
      >
        {/* Value Trend Chart */}
        <TrendsLineChart
          points={chartData}
          yAxisTitle="Assessment Value"
          title="P50 Trend Over Time"
          timeBucket={timeBucket}
          lineColors={[theme.colors.actionDefaultBackgroundDefault]}
          height={200}
          xDomain={xDomain}
        />
        </InsightsCard>
      </div>
    );
  }

  // String assessments - not yet supported
  return (
    <div ref={cardRef}>
      <InsightsCard
        title={
        <span>
          {assessment.name}
          <DataTypeTag dataType={assessment.data_type} />
        </span>
      }
      subtitle="Visualization not yet supported"
    >
      <div css={{
        display: 'flex',
        alignItems: 'center',
        gap: theme.spacing.sm,
        padding: theme.spacing.lg,
        background: theme.colors.backgroundSecondary,
        borderRadius: theme.general.borderRadiusBase,
      }}>
        <span css={{ fontSize: '24px' }}>⚠️</span>
        <div>
          <div css={{ fontWeight: 600, marginBottom: theme.spacing.xs }}>
            Visualization not yet supported
          </div>
          <div css={{ fontSize: theme.typography.fontSizeSm, color: theme.colors.textSecondary }}>
            String assessment types will be supported in a future update
          </div>
        </div>
      </div>

      </InsightsCard>
    </div>
  );
};