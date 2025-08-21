import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { PERCENTILE_COLORS, PercentileThreshold } from '../constants/percentileColors';
import { formatNumericValue } from '../utils/dataTransformations';

interface TrendsNumericPercentileSelectorProps {
  selectedPercentile: PercentileThreshold;
  onPercentileChange: (percentile: PercentileThreshold) => void;
  assessmentData?: { p50Value: number; p90Value: number; p99Value: number };
}

export const TrendsNumericPercentileSelector = ({
  selectedPercentile,
  onPercentileChange,
  assessmentData,
}: TrendsNumericPercentileSelectorProps) => {
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
            {value !== undefined ? formatNumericValue(value) : '...'}
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
      {createPercentileDisplay('P50', assessmentData?.p50Value)}
      {createPercentileDisplay('P90', assessmentData?.p90Value)}
      {createPercentileDisplay('P99', assessmentData?.p99Value)}
    </div>
  );
};
