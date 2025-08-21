import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { formatLatency, formatPercentage, formatCount } from '../utils/dataTransformations';

export interface TrendsCategoricalBarData {
  label: string;
  value: number;
}

export interface TrendsCategoricalBarChartProps {
  /** Array of data points to display */
  data: TrendsCategoricalBarData[];
  /** Type of data being displayed - affects formatting */
  dataType: 'latency' | 'percentage' | 'count';
  /** Color for the bars */
  barColor: string;
  /** Height of the chart in pixels */
  height?: number;
  /** Whether to show value labels on top of bars */
  showValueLabels?: boolean;
  /** Maximum number of bars to show */
  maxBars?: number;
  /** Title for the chart (optional) */
  title?: string;
  /** Callback when a bar is clicked */
  onBarClick?: (index: number) => void;
  /** Index of the selected bar for highlighting */
  selectedIndex?: number;
}

export const TrendsCategoricalBarChart = ({
  data,
  dataType,
  barColor,
  height,
  showValueLabels = true,
  maxBars = 5,
  title,
  onBarClick,
  selectedIndex,
}: TrendsCategoricalBarChartProps) => {
  const { theme } = useDesignSystemTheme();

  // Limit the number of bars if specified
  const displayData = data.slice(0, maxBars);

  if (!displayData || displayData.length === 0) {
    return (
      <div
        css={{
          ...(height ? { height: height + 40 } : {}),
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: theme.colors.textSecondary,
          fontSize: theme.typography.fontSizeSm,
          minHeight: 60,
        }}
      >
        No data available
      </div>
    );
  }

  const maxValue = Math.max(...displayData.map((d) => d.value));
  const formatValue = (value: number) => {
    if (dataType === 'latency') {
      return formatLatency(value);
    } else if (dataType === 'count') {
      return formatCount(value);
    } else {
      // Error rates are already in percentage format (e.g., 10.5 = 10.5%)
      // So we just need to add the % symbol, not multiply by 100
      if (value === 0) return '0%';
      if (value < 0.1) return '<0.1%';
      return `${value.toFixed(1)}%`;
    }
  };

  return (
    <div css={{ width: '100%' }}>
      {title && (
        <div
          css={{
            fontSize: theme.typography.fontSizeSm,
            fontWeight: theme.typography.typographyBoldFontWeight,
            color: theme.colors.textPrimary,
            marginBottom: theme.spacing.sm,
            textAlign: 'center',
          }}
        >
          {title}
        </div>
      )}

      <div css={height ? { height: height + 20 } : {}}>
        <div
          css={{
            display: 'flex',
            flexDirection: 'column',
            gap: theme.spacing.sm,
            padding: theme.spacing.sm,
          }}
        >
          {displayData.map((item, index) => {
            const barWidth = maxValue > 0 ? (item.value / maxValue) * 100 : 1;
            const isHighValue = dataType === 'percentage' && item.value > 10;
            const isSelected = selectedIndex === index;

            return (
              <div
                key={`${item.label}-${index}`}
                css={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: theme.spacing.sm,
                  minHeight: '24px',
                  cursor: onBarClick ? 'pointer' : 'default',
                  padding: `${theme.spacing.xs}px ${theme.spacing.sm}px`,
                  marginLeft: `-${theme.spacing.sm}px`,
                  marginRight: `-${theme.spacing.sm}px`,
                  borderRadius: theme.borders.borderRadiusSm,
                  border: isSelected ? `2px solid ${theme.colors.primary}` : '2px solid transparent',
                  '&:hover': onBarClick
                    ? {
                        backgroundColor: theme.colors.actionTertiaryBackgroundHover,
                      }
                    : {},
                }}
                onClick={onBarClick ? () => onBarClick(index) : undefined}
              >
                {/* Tool label on the left */}
                <div
                  css={{
                    fontSize: theme.typography.fontSizeSm,
                    color: theme.colors.textSecondary,
                    width: '80px',
                    textAlign: 'left',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                  }}
                >
                  {item.label}
                </div>

                {/* Bar container */}
                <div
                  css={{
                    flex: 1,
                    height: '20px',
                    backgroundColor: theme.colors.backgroundSecondary,
                    borderRadius: theme.borders.borderRadiusSm,
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                >
                  {/* Actual bar */}
                  <div
                    css={{
                      width: `${barWidth}%`,
                      height: '100%',
                      backgroundColor: isHighValue
                        ? theme.colors.textValidationDanger
                        : isSelected
                        ? theme.colors.primary
                        : barColor,
                      borderRadius: theme.borders.borderRadiusSm,
                      transition: 'all 0.2s ease-in-out',
                      minWidth: '2px', // Minimum width for visibility
                      opacity: isSelected ? 1 : 0.9,
                      '&:hover': {
                        opacity: 0.8,
                      },
                    }}
                  />

                  {/* Value label */}
                  {showValueLabels && (
                    <div
                      css={{
                        position: 'absolute',
                        right: theme.spacing.xs,
                        top: '50%',
                        transform: 'translateY(-50%)',
                        fontSize: theme.typography.fontSizeSm,
                        color:
                          barWidth > 30
                            ? theme.colors.backgroundPrimary
                            : isHighValue
                            ? theme.colors.textValidationDanger
                            : theme.colors.textSecondary,
                        fontWeight: isHighValue ? theme.typography.typographyBoldFontWeight : 'normal',
                        whiteSpace: 'nowrap',
                        textShadow: barWidth > 30 ? '0 0 2px rgba(0,0,0,0.5)' : 'none',
                      }}
                    >
                      {formatValue(item.value)}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend/axis info */}
        <div
          css={{
            marginTop: theme.spacing.sm,
            textAlign: 'center',
            fontSize: theme.typography.fontSizeSm,
            color: theme.colors.textSecondary,
          }}
        >
          {dataType === 'latency' ? 'Latency →' : dataType === 'count' ? 'Invocations →' : 'Error Rate (%) →'}
        </div>
      </div>
    </div>
  );
};
