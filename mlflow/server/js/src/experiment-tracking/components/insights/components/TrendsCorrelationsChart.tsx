import React, { useMemo } from 'react';
import { useDesignSystemTheme, HoverCard, Typography } from '@databricks/design-system';
import { TrendsCorrelationItem } from './TrendsCorrelationItem';
import { NPMI_THRESHOLDS } from '../constants/npmiThresholds';
import { CHART_CONFIG } from '../constants/chartConfig';
import { TrendsCorrelationData } from '../types/insightsTypes';

interface TrendsCorrelationsChartProps {
  title: string;
  data: TrendsCorrelationData[];
  isLoading?: boolean;
  maxItems?: number;
  totalTraces?: number; // Optional: total number of traces for percentage calculation
  totalTracesInWindow?: number; // Total traces in the entire time window
  onItemClick?: (item: TrendsCorrelationData) => void;
}

export const TrendsCorrelationsChart = ({
  title,
  data,
  isLoading = false,
  maxItems = CHART_CONFIG.DEFAULTS.MAX_CORRELATION_ITEMS,
  totalTraces,
  totalTracesInWindow,
  onItemClick,
}: TrendsCorrelationsChartProps) => {
  const { theme } = useDesignSystemTheme();

  // Calculate total for percentages - memoized for performance
  const { topItems, total } = useMemo(() => {
    const items = data?.slice(0, maxItems) || [];
    const totalCount = totalTraces || items.reduce((sum, item) => Number(item.count) || 0, 0);
    return { topItems: items, total: totalCount };
  }, [data, maxItems, totalTraces]);

  // Memoize processed items with percentage calculations for performance
  const processedItems = useMemo(() => {
    return topItems.map((item) => {
      const count = Number(item.count) || 0;
      const percentage = item.percentage !== undefined ? item.percentage : total > 0 ? (count / total) * 100 : 0;
      const percentageOfAll = totalTracesInWindow && totalTracesInWindow > 0 ? (count / totalTracesInWindow) * 100 : 0;

      return {
        ...item,
        count,
        percentage,
        percentageOfAll,
      };
    });
  }, [topItems, total, totalTracesInWindow]);

  return (
    <div
      css={{
        backgroundColor: theme.colors.backgroundPrimary,
      }}
    >
      <Typography.Hint
        css={{
          margin: 0,
          marginBottom: theme.spacing.sm,
          fontSize: theme.typography.fontSizeSm,
          textTransform: 'uppercase',
          color: theme.colors.textSecondary,
          letterSpacing: '0.5px',
        }}
      >
        {title}
      </Typography.Hint>

      <div css={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.sm }}>
        {isLoading ? (
          <div
            css={{
              backgroundColor: theme.colors.backgroundSecondary,
              borderRadius: theme.general.borderRadiusBase,
              padding: `${theme.spacing.sm}px ${theme.spacing.md}px`,
              color: theme.colors.textSecondary,
              fontSize: theme.typography.fontSizeSm,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            Loading {title.toLowerCase()}...
          </div>
        ) : !data || data.length === 0 ? (
          <div
            css={{
              backgroundColor: theme.colors.backgroundSecondary,
              borderRadius: theme.general.borderRadiusBase,
              padding: `${theme.spacing.sm}px ${theme.spacing.md}px`,
              color: theme.colors.textSecondary,
              fontSize: theme.typography.fontSizeSm,
            }}
          >
            No {title.toLowerCase()} found
          </div>
        ) : (
          processedItems.map((item, index) => {
            const { count, percentage, percentageOfAll } = item;

            // Tooltip content
            const tooltipContent = (
              <div css={{ padding: theme.spacing.xs }}>
                <div css={{ marginBottom: theme.spacing.xs }}>
                  <strong>{item.label}</strong>
                </div>
                <div css={{ fontSize: theme.typography.fontSizeSm }}>
                  <div>
                    {count.toLocaleString()} traces • {percentage.toFixed(1)}% of slice
                    {totalTracesInWindow ? ` • ${percentageOfAll.toFixed(1)}% of total` : ''}
                  </div>
                  {item.npmi !== undefined && (
                    <>
                      <div
                        css={{
                          marginTop: theme.spacing.xs,
                          paddingTop: theme.spacing.xs,
                          borderTop: `1px solid ${theme.colors.borderDecorative}`,
                        }}
                      >
                        <div>NPMI: {item.npmi.toFixed(3)}</div>
                        <div css={{ fontSize: theme.typography.fontSizeSm, color: theme.colors.textSecondary }}>
                          {item.npmi >= NPMI_THRESHOLDS.STRONG_CORRELATION
                            ? '✓ Strong association'
                            : item.npmi > NPMI_THRESHOLDS.MODERATE_CORRELATION
                            ? '~ Moderate association'
                            : item.npmi > NPMI_THRESHOLDS.WEAK_CORRELATION
                            ? '○ Weak association'
                            : item.npmi > -0.1
                            ? '○ No association'
                            : '✗ Negative association'}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            );

            return (
              <HoverCard
                key={`${item.label}-${index}`}
                content={tooltipContent}
                trigger={
                  <div>
                    <TrendsCorrelationItem
                      label={item.label}
                      percentage={percentage}
                      npmi={item.npmi}
                      type={item.type}
                      count={count}
                      totalTracesInWindow={totalTracesInWindow}
                      onClick={onItemClick ? () => onItemClick(item) : undefined}
                    />
                  </div>
                }
              />
            );
          })
        )}
      </div>
    </div>
  );
};
