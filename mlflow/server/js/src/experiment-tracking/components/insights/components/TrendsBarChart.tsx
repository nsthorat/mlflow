import { useDesignSystemTheme } from '@databricks/design-system';
import { Typography } from '@databricks/design-system';
import { FormattedMessage } from '@databricks/i18n';
import type { Config, Data, Layout } from 'plotly.js';
import React from 'react';

import { LazyPlot } from '../../LazyPlot';
import { TimeBucket } from '../types/insightsTypes';
import { createThemedPlotlyLayout } from '../../runs-charts/components/RunsCharts.common';
import { CHART_CONFIG } from '../constants/chartConfig';
import { getPlotlyTickConfig, getPlotlyTickConfigForRange, formatTooltipDate } from '../utils/chartDateFormatting';

export interface TrendsBarChartBar {
  timeBucket: Date;
  value: number | undefined;
}

/**
 * Simple Plotly-based bar chart component for insights
 */
export const TrendsBarChart = ({
  title,
  yAxisTitle,
  yAxisFormat,
  points,
  timeBucket = 'hour',
  barColor,
  aggregationType,
  isLoading,
  height = 300,
  xDomain,
  yDomain,
}: {
  title?: string;
  yAxisTitle: string;
  yAxisFormat?: string;
  points: TrendsBarChartBar[];
  timeBucket?: TimeBucket;
  barColor?: string;
  aggregationType?: string;
  isLoading?: boolean;
  height?: number;
  xDomain?: [number | undefined, number | undefined];
  yDomain?: [number | undefined, number | undefined];
}) => {
  const { theme } = useDesignSystemTheme();

  // Get smart tick configuration for x-axis
  const tickConfig = React.useMemo(() => {
    if (points.length === 0) return { ticktext: [], tickvals: [], tickangle: 0 };
    
    // For day/week buckets with xDomain, generate ticks for the full range
    if (xDomain && xDomain[0] && xDomain[1] && (timeBucket === 'day' || timeBucket === 'week')) {
      return getPlotlyTickConfigForRange(xDomain[0], xDomain[1], timeBucket);
    }
    
    // Otherwise use the data points
    return getPlotlyTickConfig(points, timeBucket);
  }, [points, timeBucket, xDomain]);

  // Create Plotly data with smart tooltips
  const plotlyData: Data[] = [
    {
      type: 'bar',
      x: points.map(p => p.timeBucket),
      y: points.map(p => p.value || 0),
      marker: {
        color: barColor || CHART_CONFIG.COLORS.TRAFFIC,
      },
      hovertemplate: points.map(p => 
        `<b>${yAxisTitle}</b>: %{y}<br><b>Date</b>: ${formatTooltipDate(p.timeBucket, timeBucket)}<extra></extra>`
      )[0], // Use first point's format as template
    }
  ];

  // Create Plotly layout with smart date formatting
  const layout: Partial<Layout> = {
    ...createThemedPlotlyLayout(theme),
    height,
    margin: { l: 60, r: 20, t: 20, b: tickConfig.tickangle !== 0 ? 80 : 60 },
    xaxis: {
      title: '',
      gridcolor: theme.colors.borderDecorative,
      tickcolor: theme.colors.textPlaceholder,
      range: xDomain,
      tickmode: 'array',
      ticktext: tickConfig.ticktext,
      tickvals: tickConfig.tickvals,
      tickangle: tickConfig.tickangle,
    },
    yaxis: {
      title: yAxisTitle,
      gridcolor: theme.colors.borderDecorative,
      tickcolor: theme.colors.textPlaceholder,
      tickformat: yAxisFormat,
      range: yDomain,
    },
    showlegend: false,
  };

  // Plotly config
  const config: Partial<Config> = {
    displayModeBar: false,
    responsive: true,
    autosizable: true,
  };

  return (
    <div
      css={{
        display: 'flex',
        flexDirection: 'column',
        gap: theme.spacing.sm,
        width: '100%',
      }}
    >
      {(title || aggregationType) && (
        <div css={{ display: 'flex', gap: theme.spacing.sm, alignItems: 'baseline' }}>
          {title && (
            <Typography.Title
              level={4}
              css={{
                marginBottom: '0 !important',
              }}
            >
              {title}
            </Typography.Title>
          )}
          {aggregationType && (
            <div
              css={{
                color: theme.colors.textPlaceholder,
                fontSize: 10,
              }}
            >
              {aggregationType}
            </div>
          )}
        </div>
      )}
      <div
        css={{
          width: '100%',
        }}
      >
        {isLoading ? (
          <div css={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height }}>
            Loading...
          </div>
        ) : points.length === 0 ? (
          <FormattedMessage
            defaultMessage="No data found for this time range"
            description="Description for when there is no data to show."
          />
        ) : (
          <div css={{ width: '100%', position: 'relative' }}>
            <LazyPlot
              data={plotlyData}
              layout={layout}
              config={config}
              style={{ width: '100%' }}
              useResizeHandler
            />
          </div>
        )}
      </div>
    </div>
  );
};