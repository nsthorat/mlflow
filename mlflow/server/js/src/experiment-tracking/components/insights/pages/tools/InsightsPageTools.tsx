/**
 * MLflow Trace Insights - Tools Page
 * 
 * Tool discovery and performance analytics
 * According to PRD: insights_ui_prd.md lines 180-268
 */

import React, { useState } from 'react';
import { useDesignSystemTheme, Button, Switch } from '@databricks/design-system';
import { useNavigate } from 'react-router-dom-v5-compat';
import { useToolDiscovery, useToolMetrics, useCorrelations } from '../../hooks/useInsightsApi';
import { InsightsCard } from '../../components/InsightsCard';
import { TrendsLineChart } from '../../components/TrendsLineChart';
import { TrendsBarChart } from '../../components/TrendsBarChart';
import { TrendsCorrelationsChart } from '../../components/TrendsCorrelationsChart';
import { TrendsCardSkeleton, TrendsEmptyState } from '../../components/TrendsSkeleton';
import { ExperimentPageTabName } from '../../../../constants';
import Routes from '../../../../routes';

interface InsightsPageToolsProps {
  experimentId?: string;
}

// Helper function to generate trace view URL with filter
const getTraceViewUrl = (experimentId: string | undefined, filter: string) => {
  if (!experimentId) return '#';
  const baseUrl = Routes.getExperimentPageTabRoute(experimentId, ExperimentPageTabName.Traces);
  return `${baseUrl}?filter=${encodeURIComponent(filter)}`;
};

export const InsightsPageTools = ({ experimentId }: InsightsPageToolsProps) => {
  const { theme } = useDesignSystemTheme();
  const navigate = useNavigate();
  const [volumeViewMode, setVolumeViewMode] = useState<'traces' | 'invocations'>('invocations');
  
  // Discover all tools in the time window
  const { data: toolsData, isLoading, error } = useToolDiscovery(
    { 
      experiment_ids: experimentId ? [experimentId] : [],
      limit: 20,
    },
    { enabled: true }
  );

  if (isLoading) {
    return (
      <div css={{ padding: theme.spacing.lg }}>
        <h2>Tools</h2>
        <div css={{ 
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: theme.spacing.lg,
          marginTop: theme.spacing.lg,
        }}>
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
        <h2>Tools</h2>
        <TrendsEmptyState
          title="Error loading tools"
          description="Unable to fetch tool data. Please try again later."
        />
      </div>
    );
  }

  if (!toolsData || !toolsData.tools || toolsData.tools.length === 0) {
    return (
      <div css={{ padding: theme.spacing.lg }}>
        <h2>Tools</h2>
        <TrendsEmptyState
          title="No tools found"
          description="No tool invocations found in the selected time range."
        />
      </div>
    );
  }

  return (
    <div css={{ padding: theme.spacing.lg }}>
      <h2>Tools</h2>
      
      {/* Overall Tools Summary Section - 3 columns */}
      <div css={{ marginTop: theme.spacing.lg }}>
        <h3>All tools</h3>
        <div css={{ 
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: theme.spacing.lg,
          marginTop: theme.spacing.md,
        }}>
          {/* Counts Card */}
          <InsightsCard 
            title="Tool Usage" 
            subtitle="Distribution"
            action={
              <Button
                size="small"
                onClick={() => navigate(getTraceViewUrl(experimentId, 'span.type = "TOOL"'))}
              >
                View Traces
              </Button>
            }
          >
            <div css={{ 
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: theme.spacing.sm,
              marginBottom: theme.spacing.lg,
            }}>
              <div>
                <div css={{ fontSize: '24px', fontWeight: 600 }}>{toolsData.tools.length}</div>
                <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>Unique Tools</div>
              </div>
              <div>
                <div css={{ fontSize: '24px', fontWeight: 600 }}>
                  {toolsData.tools.reduce((sum, t) => sum + t.invocation_count, 0).toLocaleString()}
                </div>
                <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>Total Invocations</div>
              </div>
              <div>
                <div css={{ fontSize: '24px', fontWeight: 600 }}>
                  {toolsData.tools.reduce((sum, t) => sum + t.trace_count, 0).toLocaleString()}
                </div>
                <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>Traces with Tools</div>
              </div>
            </div>
            
            {/* Tool distribution chart */}
            <div css={{ marginBottom: theme.spacing.md }}>
              {/* Simplified bar chart showing tool counts */}
              {toolsData.tools.slice(0, 5).map(tool => (
                <div key={tool.name} css={{ 
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: theme.spacing.xs,
                }}>
                  <div css={{ width: '120px', fontSize: '12px', marginRight: theme.spacing.sm }}>
                    {tool.name}
                  </div>
                  <div css={{ 
                    flex: 1,
                    height: '20px',
                    background: theme.colors.backgroundSecondary,
                    borderRadius: theme.general.borderRadiusBase,
                    overflow: 'hidden',
                  }}>
                    <div css={{
                      width: `${(tool.invocation_count / Math.max(...toolsData.tools.map(t => t.invocation_count))) * 100}%`,
                      height: '100%',
                      background: theme.colors.actionDefaultBackgroundDefault,
                    }} />
                  </div>
                  <div css={{ marginLeft: theme.spacing.sm, fontSize: '12px', minWidth: '50px', textAlign: 'right' }}>
                    {tool.invocation_count.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </InsightsCard>

          {/* Latencies Card */}
          <InsightsCard title="Overall Latencies" subtitle="All tools combined">
            <div css={{ 
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: theme.spacing.sm,
              marginBottom: theme.spacing.lg,
              padding: theme.spacing.md,
              background: theme.colors.backgroundSecondary,
              borderRadius: theme.general.borderRadiusBase,
            }}>
              <div>
                <div css={{ fontSize: '20px', fontWeight: 600 }}>
                  {(() => {
                    const allLatencies = toolsData.tools
                      .map(t => t.p50_latency || 0)
                      .filter(l => l > 0)
                      .sort((a, b) => a - b);
                    if (allLatencies.length === 0) return 'N/A';
                    const p50 = allLatencies[Math.floor(allLatencies.length * 0.5)];
                    return p50 > 1000 ? `${(p50 / 1000).toFixed(2)}s` : `${p50.toFixed(0)}ms`;
                  })()}
                </div>
                <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>P50</div>
              </div>
              <div>
                <div css={{ fontSize: '20px', fontWeight: 600 }}>
                  {(() => {
                    const allLatencies = toolsData.tools
                      .map(t => t.p90_latency || 0)
                      .filter(l => l > 0)
                      .sort((a, b) => a - b);
                    if (allLatencies.length === 0) return 'N/A';
                    const p90 = allLatencies[Math.floor(allLatencies.length * 0.9)];
                    return p90 > 1000 ? `${(p90 / 1000).toFixed(2)}s` : `${p90.toFixed(0)}ms`;
                  })()}
                </div>
                <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>P90</div>
              </div>
              <div>
                <div css={{ fontSize: '20px', fontWeight: 600 }}>
                  {(() => {
                    const allLatencies = toolsData.tools
                      .map(t => t.p99_latency || 0)
                      .filter(l => l > 0)
                      .sort((a, b) => a - b);
                    if (allLatencies.length === 0) return 'N/A';
                    const p99 = allLatencies[Math.min(Math.floor(allLatencies.length * 0.99), allLatencies.length - 1)];
                    return p99 > 1000 ? `${(p99 / 1000).toFixed(2)}s` : `${p99.toFixed(0)}ms`;
                  })()}
                </div>
                <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>P99</div>
              </div>
            </div>
            
            {/* Tool latency breakdown */}
            {toolsData.tools.slice(0, 5).map(tool => (
              <div key={tool.name} css={{ 
                display: 'flex',
                alignItems: 'center',
                marginBottom: theme.spacing.xs,
              }}>
                <div css={{ width: '120px', fontSize: '12px', marginRight: theme.spacing.sm }}>
                  {tool.name}
                </div>
                <div css={{ 
                  flex: 1,
                  height: '20px',
                  background: theme.colors.backgroundSecondary,
                  borderRadius: theme.general.borderRadiusBase,
                  overflow: 'hidden',
                }}>
                  <div css={{
                    width: `${((tool.avg_latency_ms || 0) / Math.max(...toolsData.tools.map(t => t.avg_latency_ms || 0))) * 100}%`,
                    height: '100%',
                    background: theme.colors.yellow400,
                  }} />
                </div>
                <div css={{ marginLeft: theme.spacing.sm, fontSize: '12px', minWidth: '50px', textAlign: 'right' }}>
                  {(tool.avg_latency_ms || 0) > 1000 
                    ? `${((tool.avg_latency_ms || 0) / 1000).toFixed(2)}s`
                    : `${(tool.avg_latency_ms || 0).toFixed(0)}ms`}
                </div>
              </div>
            ))}
          </InsightsCard>

          {/* Errors Card */}
          <InsightsCard title="Errors" subtitle="By tool">
            <div css={{ 
              marginBottom: theme.spacing.lg,
              padding: theme.spacing.md,
              background: theme.colors.backgroundSecondary,
              borderRadius: theme.general.borderRadiusBase,
            }}>
              <div css={{ fontSize: '24px', fontWeight: 600, color: theme.colors.textValidationDanger }}>
                {((toolsData.tools.reduce((sum, t) => sum + t.error_count, 0) / 
                   toolsData.tools.reduce((sum, t) => sum + t.invocation_count, 0)) * 100).toFixed(1)}%
              </div>
              <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
                Average Error Rate
              </div>
            </div>
            
            {/* Tool error breakdown */}
            {toolsData.tools.filter(t => t.error_count > 0).slice(0, 5).map(tool => (
              <div key={tool.name} css={{ 
                display: 'flex',
                alignItems: 'center',
                marginBottom: theme.spacing.xs,
              }}>
                <div css={{ width: '120px', fontSize: '12px', marginRight: theme.spacing.sm }}>
                  {tool.name}
                </div>
                <div css={{ 
                  flex: 1,
                  height: '20px',
                  background: theme.colors.backgroundSecondary,
                  borderRadius: theme.general.borderRadiusBase,
                  overflow: 'hidden',
                }}>
                  <div css={{
                    width: `${(tool.error_count / tool.invocation_count) * 100}%`,
                    height: '100%',
                    background: theme.colors.textValidationDanger,
                  }} />
                </div>
                <div css={{ marginLeft: theme.spacing.sm, fontSize: '12px', minWidth: '50px', textAlign: 'right' }}>
                  {((tool.error_count / tool.invocation_count) * 100).toFixed(1)}%
                </div>
              </div>
            ))}
            
            {toolsData.tools.filter(t => t.error_count > 0).length === 0 && (
              <div css={{ textAlign: 'center', color: theme.colors.textSecondary, padding: theme.spacing.md }}>
                No tools with errors
              </div>
            )}
          </InsightsCard>
        </div>
      </div>

      {/* Individual Tool Cards Section - 3 columns per tool */}
      <div css={{ marginTop: theme.spacing.lg }}>
        <h3>Tool Details</h3>
        {toolsData.tools.map(tool => (
          <ToolRow key={tool.name} tool={tool} experimentId={experimentId} />
        ))}
      </div>
    </div>
  );
};

// Individual Tool Row Component
interface ToolRowProps {
  tool: {
    name: string;
    trace_count: number;
    invocation_count: number;
    error_count: number;
    avg_latency_ms?: number | null;
    p50_latency?: number | null;
    p90_latency?: number | null;
    p99_latency?: number | null;
  };
  experimentId?: string;
}

const ToolRow: React.FC<ToolRowProps> = ({ tool, experimentId }) => {
  const { theme } = useDesignSystemTheme();
  const navigate = useNavigate();
  const [volumeViewMode, setVolumeViewMode] = useState<'traces' | 'invocations'>('invocations');
  
  // Fetch detailed metrics for this tool
  const { data: metricsData } = useToolMetrics(
    {
      tool_name: tool.name,
      experiment_ids: experimentId ? [experimentId] : [],
      time_bucket: 'hour',
    },
    { refetchInterval: 30000 }
  );

  // Fetch correlations for tool errors
  const { data: errorCorrelations } = useCorrelations(
    {
      experiment_ids: experimentId ? [experimentId] : [],
      filter_string: `tool:${tool.name} AND status:error`,
      correlation_dimensions: ['tag'],
      limit: 5,
    },
    { enabled: tool.error_count > 0 }
  );

  return (
    <div css={{ 
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: theme.spacing.lg,
      marginBottom: theme.spacing.lg,
    }}>
      {/* Volume Column */}
      <InsightsCard
        title={tool.name}
        subtitle={
          <div css={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
            <span>{`${tool.trace_count} traces • ${tool.invocation_count} invocations`}</span>
            <Switch
              size="small"
              checked={volumeViewMode === 'invocations'}
              onChange={(checked) => setVolumeViewMode(checked ? 'invocations' : 'traces')}
            />
            <span css={{ fontSize: '11px' }}>{volumeViewMode}</span>
          </div>
        }
        action={
          <Button
            size="small"
            onClick={() => navigate(getTraceViewUrl(experimentId, `span.name = "${tool.name}" AND span.type = "TOOL"`))}
          >
            View Traces
          </Button>
        }
      >
        {metricsData && (
          <TrendsBarChart
            points={metricsData.time_series.map(point => ({
              timeBucket: new Date(point.time_bucket),
              value: volumeViewMode === 'invocations' ? point.count : (point.trace_count || point.count),
            }))}
            yAxisTitle={volumeViewMode === 'invocations' ? 'Invocations' : 'Traces'}
            title="Usage Over Time"
            barColor={theme.colors.actionDefaultBackgroundDefault}
            height={200}
          />
        )}
      </InsightsCard>

      {/* Latency Column */}
      <InsightsCard
        title="Latency"
        subtitle={(() => {
          if (!tool.p50_latency && !tool.p90_latency && !tool.p99_latency) return 'No data';
          const parts = [];
          if (tool.p50_latency) {
            parts.push(`P50: ${tool.p50_latency > 1000 ? `${(tool.p50_latency / 1000).toFixed(2)}s` : `${tool.p50_latency.toFixed(0)}ms`}`);
          }
          if (tool.p90_latency) {
            parts.push(`P90: ${tool.p90_latency > 1000 ? `${(tool.p90_latency / 1000).toFixed(2)}s` : `${tool.p90_latency.toFixed(0)}ms`}`);
          }
          if (tool.p99_latency) {
            parts.push(`P99: ${tool.p99_latency > 1000 ? `${(tool.p99_latency / 1000).toFixed(2)}s` : `${tool.p99_latency.toFixed(0)}ms`}`);
          }
          return parts.join(' • ');
        })()}
        action={
          <Button
            size="small"
            onClick={() => navigate(getTraceViewUrl(experimentId, `span.name = "${tool.name}" AND span.type = "TOOL"`))}
          >
            View Traces
          </Button>
        }
      >
        {metricsData && metricsData.time_series && metricsData.time_series.length > 0 ? (
          <TrendsLineChart
            points={metricsData.time_series.map(point => ({
              timeBucket: new Date(point.time_bucket),
              values: {
                P50: point.p50_latency || 0,
                P90: point.p90_latency || 0,
                P99: point.p99_latency || 0,
              }
            }))}
            yAxisTitle="Latency (ms)"
            title="Latency Percentiles"
            lineColors={[theme.colors.yellow300, theme.colors.yellow400, theme.colors.yellow500]}
            height={200}
            multiLine={true}
          />
        ) : (
          <div css={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            height: 200,
            color: theme.colors.textSecondary 
          }}>
            No latency data available
          </div>
        )}
      </InsightsCard>

      {/* Errors Column */}
      <InsightsCard
        title="Errors"
        subtitle={tool.error_count > 0 
          ? `${((tool.error_count / tool.invocation_count) * 100).toFixed(1)}% error rate`
          : 'No errors'}
        action={
          tool.error_count > 0 ? (
            <Button
              size="small"
              onClick={() => navigate(getTraceViewUrl(experimentId, `span.name = "${tool.name}" AND span.type = "TOOL" AND status = "ERROR"`))}
            >
              View Error Traces
            </Button>
          ) : null
        }
      >
        {tool.error_count > 0 ? (
          <>
            {metricsData && (
              <TrendsLineChart
                points={metricsData.time_series.map(point => ({
                  timeBucket: new Date(point.time_bucket),
                  value: (point.error_count / point.count) * 100,
                }))}
                yAxisTitle="Error Rate (%)"
                title="Error Rate Over Time"
                lineColors={[theme.colors.textValidationDanger]}
                height={150}
              />
            )}
            
            {/* MANDATORY Correlations */}
            {errorCorrelations && errorCorrelations.data.length > 0 && (
              <div css={{ marginTop: theme.spacing.md }}>
                <h5 css={{ marginBottom: theme.spacing.xs }}>Error Correlations</h5>
                <TrendsCorrelationsChart
                  title="Error Correlations"
                  data={errorCorrelations.data.map(item => ({
                    label: `${item.dimension}: ${item.value}`,
                    count: item.trace_count,
                    npmi: item.npmi_score,
                    percentage: item.percentage_of_slice,
                    type: 'tag' as const,
                  }))}
                  onItemClick={(item) => console.log('Tool error correlation clicked:', item)}
                />
              </div>
            )}
          </>
        ) : (
          <div css={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '200px',
            color: theme.colors.textValidationSuccess,
          }}>
            <div css={{ fontSize: '48px', marginBottom: theme.spacing.sm }}>✓</div>
            <div css={{ fontSize: '16px', fontWeight: 600 }}>No Errors</div>
            <div css={{ fontSize: '12px', color: theme.colors.textSecondary }}>
              All invocations completed successfully
            </div>
          </div>
        )}
      </InsightsCard>
    </div>
  );
};