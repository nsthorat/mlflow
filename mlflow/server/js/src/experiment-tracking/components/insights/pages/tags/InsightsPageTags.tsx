/**
 * MLflow Trace Insights - Tags Page
 * 
 * Tag distribution and value analysis
 * According to PRD: insights_ui_prd.md lines 269-346
 */

import React, { useState } from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { useTagDiscovery, useTagValues, useCorrelations } from '../../hooks/useInsightsApi';
import { InsightsCard } from '../../components/InsightsCard';
import { TrendsCorrelationsChart } from '../../components/TrendsCorrelationsChart';
import { TrendsCardSkeleton, TrendsEmptyState } from '../../components/TrendsSkeleton';

interface InsightsPageTagsProps {
  experimentId?: string;
}

export const InsightsPageTags = ({ experimentId }: InsightsPageTagsProps) => {
  const { theme } = useDesignSystemTheme();
  
  // Discover all tag keys in the time window
  const { data: tagsData, isLoading, error } = useTagDiscovery(
    experimentId ? [experimentId] : [],
    { refetchInterval: 60000 }
  );

  if (isLoading) {
    return (
      <div css={{ padding: theme.spacing.lg }}>
        <h2>Tags</h2>
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
        <h2>Tags</h2>
        <TrendsEmptyState
          title="Error loading tags"
          description="Unable to fetch tag data. Please try again later."
        />
      </div>
    );
  }

  if (!tagsData || !tagsData.tag_keys || tagsData.tag_keys.length === 0) {
    return (
      <div css={{ padding: theme.spacing.lg }}>
        <h2>Tags</h2>
        <TrendsEmptyState
          title="No tags found"
          description="No tag data available for the selected time range."
        />
      </div>
    );
  }

  // Filter out mlflow.* tags per PRD requirement
  const filteredTags = tagsData.tag_keys.filter(
    (tag) => !tag.key.toLowerCase().startsWith('mlflow.')
  );

  if (filteredTags.length === 0) {
    return (
      <div css={{ padding: theme.spacing.lg }}>
        <h2>Tags</h2>
        <TrendsEmptyState
          title="No user tags found"
          description="No user-defined tags available. Only MLflow system tags were found."
        />
      </div>
    );
  }

  return (
    <div css={{ padding: theme.spacing.lg }}>
      <h2>Tags</h2>
      
      {/* Two-column card layout for tag keys */}
      <div css={{ 
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: theme.spacing.lg,
        marginTop: theme.spacing.lg,
      }}>
        {filteredTags.map((tag) => (
          <TagCard
            key={tag.key}
            tag={tag}
            experimentId={experimentId}
          />
        ))}
      </div>
    </div>
  );
};

// Individual Tag Card Component
interface TagCardProps {
  tag: {
    key: string;
    trace_count: number;
    unique_values_count: number;
  };
  experimentId?: string;
}

const TagCard: React.FC<TagCardProps> = ({ tag, experimentId }) => {
  const { theme } = useDesignSystemTheme();
  const [selectedValue, setSelectedValue] = useState<string | null>(null);
  
  // Fetch tag value distribution
  const { data: valuesData, isLoading } = useTagValues(
    tag.key,
    experimentId ? [experimentId] : [],
    { limit: 10, refetchInterval: 30000 }
  );

  // Fetch correlations for selected tag value
  const { data: correlationsData } = useCorrelations(
    {
      experiment_ids: experimentId ? [experimentId] : [],
      filter_string: selectedValue ? `tag.${tag.key}:"${selectedValue}"` : '',
      correlation_dimensions: ['tool', 'tag'],
      limit: 5,
    },
    { 
      enabled: !!selectedValue,
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

  // Color scale for value bars
  const getBarColor = (index: number, total: number) => {
    if (index === 0) return theme.colors.actionDefaultBackgroundDefault;
    if (index < total / 3) return theme.colors.actionDefaultBackgroundHover;
    if (index < (total * 2) / 3) return theme.colors.backgroundSecondary;
    return theme.colors.backgroundPrimary;
  };

  return (
    <InsightsCard
      title={tag.key}
      subtitle={`${tag.trace_count.toLocaleString()} usage(s) across ${tag.unique_values_count.toLocaleString()} value(s)`}
      headerContent={
        <button
          css={{
            padding: `${theme.spacing.xs}px ${theme.spacing.sm}px`,
            background: theme.colors.actionDefaultBackgroundDefault,
            color: theme.colors.actionDefaultTextDefault,
            border: 'none',
            borderRadius: theme.general.borderRadiusBase,
            fontSize: theme.typography.fontSizeSm,
            cursor: 'pointer',
            '&:hover': {
              background: theme.colors.actionDefaultBackgroundHover,
            },
          }}
          onClick={() => console.log('View traces for tag:', tag.key)}
        >
          View Traces
        </button>
      }
    >
      {/* Value Distribution Chart */}
      {valuesData && valuesData.values.length > 0 && (
        <div css={{ marginBottom: theme.spacing.lg }}>
          <h4 css={{ 
            margin: `0 0 ${theme.spacing.sm}px 0`,
            fontSize: '14px',
            fontWeight: 600,
            color: theme.colors.textPrimary,
          }}>
            Top Values
          </h4>
          
          {/* Horizontal bar chart for tag values */}
          <div css={{ marginBottom: theme.spacing.md }}>
            {valuesData.values.map((value, index) => (
              <div
                key={value.value}
                css={{ 
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: theme.spacing.xs,
                  cursor: 'pointer',
                  padding: theme.spacing.xs,
                  borderRadius: theme.general.borderRadiusBase,
                  background: selectedValue === value.value 
                    ? theme.colors.backgroundSecondary 
                    : 'transparent',
                  '&:hover': {
                    background: theme.colors.backgroundSecondary,
                  },
                }}
                onClick={() => setSelectedValue(value.value === selectedValue ? null : value.value)}
              >
                <div css={{ 
                  width: '200px', 
                  fontSize: '12px', 
                  marginRight: theme.spacing.sm,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                title={value.value}>
                  {value.value}
                </div>
                <div css={{ 
                  flex: 1,
                  height: '20px',
                  background: theme.colors.backgroundSecondary,
                  borderRadius: theme.general.borderRadiusBase,
                  overflow: 'hidden',
                  position: 'relative',
                }}>
                  <div css={{
                    width: `${(value.count / Math.max(...valuesData.values.map(v => v.count))) * 100}%`,
                    height: '100%',
                    background: getBarColor(index, valuesData.values.length),
                    transition: 'all 0.2s ease',
                  }} />
                </div>
                <div css={{ 
                  marginLeft: theme.spacing.sm, 
                  fontSize: '12px', 
                  minWidth: '60px', 
                  textAlign: 'right' 
                }}>
                  {value.count.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
          
          <div css={{ 
            fontSize: '11px', 
            color: theme.colors.textSecondary,
            textAlign: 'center',
          }}>
            Invocations →
          </div>
        </div>
      )}

      {/* MANDATORY Correlations Section */}
      <div>
        <h4 css={{ 
          margin: `0 0 ${theme.spacing.sm}px 0`,
          fontSize: '14px',
          fontWeight: 600,
          color: theme.colors.textPrimary,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          Correlations
          {selectedValue && (
            <button
              css={{
                padding: `${theme.spacing.xs}px ${theme.spacing.xs}px`,
                background: theme.colors.backgroundSecondary,
                color: theme.colors.textSecondary,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.general.borderRadiusBase,
                fontSize: '11px',
                cursor: 'pointer',
                '&:hover': {
                  background: theme.colors.backgroundPrimary,
                },
              }}
              onClick={() => setSelectedValue(null)}
            >
              Clear selection
            </button>
          )}
        </h4>
        
        {selectedValue ? (
          correlations.length > 0 ? (
            <TrendsCorrelationsChart
              title={`Correlations for ${tag.key}="${selectedValue}"`}
              data={correlations}
              onItemClick={(item) => {
                console.log('Tag correlation clicked:', item);
              }}
            />
          ) : (
            <div css={{
              padding: theme.spacing.md,
              background: theme.colors.backgroundSecondary,
              borderRadius: theme.general.borderRadiusBase,
              textAlign: 'center',
              color: theme.colors.textSecondary,
            }}>
              No correlations found for this value
            </div>
          )
        ) : (
          <div css={{
            padding: theme.spacing.md,
            background: theme.colors.backgroundSecondary,
            borderRadius: theme.general.borderRadiusBase,
            textAlign: 'center',
            color: theme.colors.textSecondary,
          }}>
            Select a value to see correlations
          </div>
        )}
      </div>
    </InsightsCard>
  );
};