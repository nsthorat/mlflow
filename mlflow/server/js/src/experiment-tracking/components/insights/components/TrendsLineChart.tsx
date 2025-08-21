import { useDesignSystemTheme } from '@databricks/design-system';
import { FormattedMessage } from '@databricks/i18n';
import type { Config, Data, Layout } from 'plotly.js';
import React from 'react';

import { LazyPlot } from '../../LazyPlot';
import { TimeBucket } from '../types/insightsTypes';
import { createThemedPlotlyLayout } from '../../runs-charts/components/RunsCharts.common';

export interface TrendsLineChartDataPoint {
  timeBucket: Date;
  value: number;
  seriesName?: string;
}

export interface TrendsLineChartProps {
  title?: string;
  yAxisTitle: string;
  yAxisFormat?: string;
  points: TrendsLineChartDataPoint[];
  timeBucket?: TimeBucket;
  lineColors?: string[];
  isLoading?: boolean;
  height?: number;
  xDomain?: [number | undefined, number | undefined];
  yDomain?: [number | undefined, number | undefined];
}

export const TrendsLineChart = ({
  title,
  yAxisTitle,
  yAxisFormat,
  points,
  lineColors = ['#1f77b4'],
  isLoading = false,
  height = 300,
  xDomain,
  yDomain,
}: TrendsLineChartProps) => {
  const { theme } = useDesignSystemTheme();

  // Group points by series name if provided
  const seriesData = React.useMemo(() => {
    const grouped = new Map<string, TrendsLineChartDataPoint[]>();
    
    points.forEach(point => {
      const series = point.seriesName || 'default';
      if (!grouped.has(series)) {
        grouped.set(series, []);
      }
      grouped.get(series)!.push(point);
    });

    return Array.from(grouped.entries());
  }, [points]);

  // Create Plotly data traces
  const plotlyData: Data[] = seriesData.map(([seriesName, seriesPoints], index) => ({
    type: 'scatter',
    mode: 'lines+markers',
    x: seriesPoints.map(p => p.timeBucket),
    y: seriesPoints.map(p => p.value),
    name: seriesName === 'default' ? '' : seriesName,
    line: {
      color: lineColors[index] || lineColors[0] || '#1f77b4',
      width: 2,
    },
    marker: {
      size: 6,
      color: lineColors[index] || lineColors[0] || '#1f77b4',
    },
    hovertemplate: `<b>${yAxisTitle}</b>: %{y}<br><b>Date</b>: %{x}<extra></extra>`,
  }));

  // Create Plotly layout
  const layout: Partial<Layout> = {
    ...createThemedPlotlyLayout(theme),
    height,
    margin: { l: 60, r: 20, t: 20, b: 60 },
    xaxis: {
      title: '',
      gridcolor: theme.colors.borderDecorative,
      tickcolor: theme.colors.textPlaceholder,
      range: xDomain,
    },
    yaxis: {
      title: yAxisTitle,
      gridcolor: theme.colors.borderDecorative,
      tickcolor: theme.colors.textPlaceholder,
      tickformat: yAxisFormat,
      range: yDomain,
    },
    showlegend: seriesData.length > 1 && seriesData[0][0] !== 'default',
  };

  // Plotly config
  const config: Partial<Config> = {
    displayModeBar: false,
    responsive: true,
  };

  return (
    <div
      css={{
        display: 'flex',
        flexDirection: 'column',
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
        <LazyPlot
          data={plotlyData}
          layout={layout}
          config={config}
        />
      )}
    </div>
  );
};