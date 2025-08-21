/**
 * MLflow Trace Insights - Quality Metrics Page
 * 
 * Displays assessment analysis and quality scoring
 * According to PRD: insights_ui_prd.md lines 115-179
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { useAssessmentDiscovery, useAssessmentData, useCorrelations } from '../../hooks/useInsightsApi';
import { InsightsCard } from '../../components/InsightsCard';
import { TrendsLineChart } from '../../components/TrendsLineChart';
import { TrendsCorrelationsChart } from '../../components/TrendsCorrelationsChart';
import { TrendsCardSkeleton, TrendsEmptyState } from '../../components/TrendsSkeleton';

interface InsightsPageQualityMetricsProps {
  experimentId?: string;
}

export const InsightsPageQualityMetrics = ({ experimentId }: InsightsPageQualityMetricsProps) => {
  const { theme } = useDesignSystemTheme();
  
  // Discover all assessments in the time window
  const { data: assessmentsData, isLoading, error } = useAssessmentDiscovery(
    experimentId ? [experimentId] : [],
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
    data_type: 'boolean' | 'numeric' | 'string';
    source: string;
    count: number;
  };
  experimentId?: string;
}

const AssessmentCard: React.FC<AssessmentCardProps> = ({ assessment, experimentId }) => {
  const { theme } = useDesignSystemTheme();
  
  // Fetch detailed assessment data
  const { data: assessmentData, isLoading } = useAssessmentData(
    assessment.name,
    experimentId ? [experimentId] : [],
    { refetchInterval: 30000 }
  );

  // Fetch correlations for assessment failures/below P50
  const { data: correlationsData } = useCorrelations(
    {
      experiment_ids: experimentId ? [experimentId] : [],
      filter_string: assessment.data_type === 'boolean' 
        ? `assessment.${assessment.name}:false`
        : assessment.data_type === 'numeric'
        ? `assessment.${assessment.name}:below_p50`
        : '',
      correlation_dimensions: ['tag', 'tool'],
      limit: 5,
    },
    { 
      enabled: !!assessmentData && assessment.data_type !== 'string',
    }
  );

  if (isLoading) {
    return <TrendsCardSkeleton />;
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
  if (assessment.data_type === 'boolean' && assessmentData) {
    const failureRate = assessmentData.summary.failure_rate || 0;
    const chartData = assessmentData.time_series.map(point => ({
      timeBucket: new Date(point.time_bucket),
      value: point.failure_rate || 0,
    }));

    return (
      <InsightsCard
        title={assessment.name}
        subtitle={`${assessmentData.summary.total_count} assessments • ${assessmentData.summary.failure_count} failures`}
      >
        {/* Failure Rate Display */}
        <div css={{
          fontSize: '32px',
          fontWeight: 700,
          color: failureRate > 10 ? theme.colors.textValidationDanger : theme.colors.textValidationSuccess,
          marginBottom: theme.spacing.md,
        }}>
          {failureRate.toFixed(1)}% failure rate
        </div>

        {/* Source Information */}
        <div css={{
          fontSize: theme.typography.fontSizeSm,
          color: theme.colors.textSecondary,
          marginBottom: theme.spacing.lg,
        }}>
          Sources: {assessment.source}
        </div>

        {/* Failure Rate Chart */}
        <div css={{ marginBottom: theme.spacing.lg }}>
          <TrendsLineChart
            points={chartData}
            yAxisTitle="Failure Rate (%)"
            yAxisFormat=".1%"
            title="Failure Rate Over Time"
            lineColors={[theme.colors.textValidationDanger]}
            height={200}
          />
        </div>

        {/* MANDATORY Correlations Section */}
        {correlations.length > 0 ? (
          <div>
            <h4 css={{ 
              margin: `0 0 ${theme.spacing.sm}px 0`,
              fontSize: '14px',
              fontWeight: 600,
              color: theme.colors.textPrimary,
            }}>
              Correlations for Failures
            </h4>
            <TrendsCorrelationsChart
              title="Failure Correlations"
              data={correlations}
              onItemClick={(item) => {
                console.log('Assessment failure correlation clicked:', item);
              }}
            />
          </div>
        ) : (
          <div css={{
            padding: theme.spacing.md,
            background: theme.colors.backgroundSecondary,
            borderRadius: theme.general.borderRadiusBase,
            textAlign: 'center',
            color: theme.colors.textSecondary,
          }}>
            No correlations for failures found
          </div>
        )}
      </InsightsCard>
    );
  }

  if (assessment.data_type === 'numeric' && assessmentData) {
    const chartData = assessmentData.time_series.map(point => ({
      timeBucket: new Date(point.time_bucket),
      value: point.p50_value || 0,
    }));

    return (
      <InsightsCard
        title={assessment.name}
        subtitle={`${assessmentData.summary.total_count} assessments • ${assessmentData.summary.below_p50_count} below P50`}
      >
        {/* Percentile Metrics Display */}
        <div css={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: theme.spacing.md,
          marginBottom: theme.spacing.lg,
          padding: theme.spacing.md,
          background: theme.colors.backgroundSecondary,
          borderRadius: theme.general.borderRadiusBase,
        }}>
          <div>
            <div css={{ fontSize: '20px', fontWeight: 600 }}>
              {assessmentData.summary.p50_value?.toFixed(2) || 'N/A'}
            </div>
            <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
              P50
            </div>
          </div>
          <div>
            <div css={{ fontSize: '20px', fontWeight: 600 }}>
              {assessmentData.summary.p90_value?.toFixed(2) || 'N/A'}
            </div>
            <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
              P90
            </div>
          </div>
          <div>
            <div css={{ fontSize: '20px', fontWeight: 600 }}>
              {assessmentData.summary.p99_value?.toFixed(2) || 'N/A'}
            </div>
            <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
              P99
            </div>
          </div>
        </div>

        {/* Source Information */}
        <div css={{
          fontSize: theme.typography.fontSizeSm,
          color: theme.colors.textSecondary,
          marginBottom: theme.spacing.lg,
        }}>
          Sources: {assessment.source}
        </div>

        {/* Value Trend Chart */}
        <div css={{ marginBottom: theme.spacing.lg }}>
          <TrendsLineChart
            points={chartData}
            yAxisTitle="Assessment Value"
            title="P50 Trend Over Time"
            lineColors={[theme.colors.actionDefaultBackgroundDefault]}
            height={200}
          />
        </div>

        {/* MANDATORY Correlations Section */}
        {correlations.length > 0 ? (
          <div>
            <h4 css={{ 
              margin: `0 0 ${theme.spacing.sm}px 0`,
              fontSize: '14px',
              fontWeight: 600,
              color: theme.colors.textPrimary,
            }}>
              Correlations for Below P50
            </h4>
            <TrendsCorrelationsChart
              title="Below P50 Correlations"
              data={correlations}
              onItemClick={(item) => {
                console.log('Assessment below P50 correlation clicked:', item);
              }}
            />
          </div>
        ) : (
          <div css={{
            padding: theme.spacing.md,
            background: theme.colors.backgroundSecondary,
            borderRadius: theme.general.borderRadiusBase,
            textAlign: 'center',
            color: theme.colors.textSecondary,
          }}>
            No correlations found
          </div>
        )}
      </InsightsCard>
    );
  }

  // String assessments - not yet supported
  return (
    <InsightsCard
      title={assessment.name}
      subtitle={`Data type: string`}
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

      {/* MANDATORY Correlations Section - Empty for string types */}
      <div css={{
        marginTop: theme.spacing.lg,
        padding: theme.spacing.md,
        background: theme.colors.backgroundSecondary,
        borderRadius: theme.general.borderRadiusBase,
        textAlign: 'center',
        color: theme.colors.textSecondary,
      }}>
        Correlations not available for string assessments
      </div>
    </InsightsCard>
  );
};