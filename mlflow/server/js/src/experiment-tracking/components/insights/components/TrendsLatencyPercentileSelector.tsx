import React from 'react';
import { useDesignSystemTheme, Typography } from '@databricks/design-system';
import { PERCENTILE_COLORS, PercentileThreshold } from '../constants/percentileColors';
import { formatLatency } from '../utils/dataTransformations';

interface TrendsLatencyPercentileSelectorProps {
  selectedPercentile: PercentileThreshold;
  onPercentileChange: (percentile: PercentileThreshold) => void;
  latencyData?: { p50: number; p90: number; p99: number };
}

export const TrendsLatencyPercentileSelector = ({
  selectedPercentile,
  onPercentileChange,
  latencyData,
}: TrendsLatencyPercentileSelectorProps) => {
  const { theme } = useDesignSystemTheme();

  const createPercentileDisplay = (percentile: PercentileThreshold, value: number | undefined) => {
    const isSelected = selectedPercentile === percentile;
    const color = PERCENTILE_COLORS[percentile];

    return (
      <div
        css={{
          cursor: 'pointer',
          padding: `${theme.spacing.sm}px ${theme.spacing.sm}px ${theme.spacing.xs}px ${theme.spacing.sm}px`,
          borderRadius: theme.general.borderRadiusBase,
          '&:hover': {
            backgroundColor: theme.colors.actionDefaultBackgroundHover,
          },
        }}
        onClick={() => onPercentileChange(percentile)}
      >
        <div
          css={{
            display: 'flex',
            alignItems: 'baseline',
            gap: theme.spacing.sm,
            borderBottom: isSelected ? `2px solid ${color}` : '2px solid transparent',
            paddingBottom: theme.spacing.xs,
          }}
        >
          <span
            css={{
              fontSize: theme.typography.fontSizeLg,
              color: theme.colors.textPrimary,
            }}
          >
            {value !== undefined ? formatLatency(value) : '...'}
          </span>

          {/* Percentile label with color */}
          <span
            css={{
              fontSize: theme.typography.fontSizeSm,
              color: color,
            }}
          >
            {percentile.toLowerCase()}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div
      css={{
        display: 'flex',
        alignItems: 'center',
        gap: theme.spacing.md,
      }}
    >
      {createPercentileDisplay('P50', latencyData?.p50)}
      {createPercentileDisplay('P90', latencyData?.p90)}
      {createPercentileDisplay('P99', latencyData?.p99)}
    </div>
  );
};
