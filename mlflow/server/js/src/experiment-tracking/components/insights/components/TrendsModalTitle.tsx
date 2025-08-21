import React from 'react';
import { useDesignSystemTheme, Tag, ClockIcon, DangerIcon, WrenchIcon, TagIcon } from '@databricks/design-system';
import { INSIGHTS_MODAL_TITLE_COMPONENT_ID } from '../constants/insightsLogging';
import { PERCENTILE_COLORS } from '../constants/percentileColors';
import { TrendsTagChip } from './TrendsTagChip';
import { TrendsToolChip } from './TrendsToolChip';

interface TrendsModalTitleProps {
  sliceType: 'latency' | 'error' | 'tool' | 'tool-latency' | 'tool-error' | 'tag';
  sliceText: string;
  metricValue?: string;
  metricLabel?: string;
  filterType?: 'tag' | 'tool' | 'assessment' | 'latency';
  filterLabel?: string;
  traceCount?: number;
}

export const TrendsModalTitle = ({
  sliceType,
  sliceText,
  metricValue,
  metricLabel,
  filterType,
  filterLabel,
  traceCount,
}: TrendsModalTitleProps) => {
  const { theme } = useDesignSystemTheme();

  const getSliceIcon = () => {
    switch (sliceType) {
      case 'latency':
      case 'tool-latency':
        return <ClockIcon />;
      case 'error':
      case 'tool-error':
        return <DangerIcon />;
      case 'tool':
        return <WrenchIcon />;
      case 'tag':
        return <TagIcon />;
      default:
        return null;
    }
  };

  const getPercentileColor = (label?: string) => {
    switch (label?.toLowerCase()) {
      case 'p50':
        return PERCENTILE_COLORS.P50;
      case 'p90':
        return PERCENTILE_COLORS.P90;
      case 'p99':
        return PERCENTILE_COLORS.P99;
      default:
        return theme.colors.grey200;
    }
  };

  return (
    <div
      css={{
        display: 'flex',
        alignItems: 'center',
        gap: theme.spacing.md,
      }}
    >
      {/* Slice type display - different styling for error vs latency */}
      {sliceType === 'error' ? (
        <div
          css={{
            display: 'flex',
            alignItems: 'center',
            gap: theme.spacing.xs,
            fontSize: theme.typography.fontSizeBase,
            fontWeight: 500,
          }}
        >
          <span css={{ color: theme.colors.textSecondary, display: 'flex', alignItems: 'center' }}>
            {getSliceIcon()}
          </span>
          <span css={{ color: theme.colors.textPrimary }}>{sliceText}</span>
        </div>
      ) : (
        <Tag
          componentId={INSIGHTS_MODAL_TITLE_COMPONENT_ID}
          css={{
            backgroundColor: theme.colors.grey050,
            border: 'none',
            fontSize: theme.typography.fontSizeBase,
            fontWeight: 500,
            padding: `${theme.spacing.xs / 2}px ${theme.spacing.xs / 2}px`,
          }}
        >
          <div css={{ display: 'flex', alignItems: 'center', gap: theme.spacing.xs }}>
            <span css={{ color: theme.colors.textSecondary, display: 'flex', alignItems: 'center' }}>
              {getSliceIcon()}
            </span>
            <span css={{ color: theme.colors.textPrimary }}>{sliceText}</span>
          </div>
        </Tag>
      )}

      {/* Metric display (for latency) - matches TrendsLatencyPercentileSelector styling exactly */}
      {metricValue && metricLabel && (
        <div
          css={{
            display: 'flex',
            alignItems: 'baseline',
            gap: theme.spacing.sm,
          }}
        >
          <span
            css={{
              fontSize: theme.typography.fontSizeLg,
              color: theme.colors.textPrimary,
              fontWeight: 'normal !important',
            }}
          >
            {metricValue}
          </span>
          <span
            css={{
              fontSize: theme.typography.fontSizeSm,
              color: getPercentileColor(metricLabel),
            }}
          >
            {metricLabel.toLowerCase()}
          </span>
        </div>
      )}

      {/* Filter display (for filtered traces) */}
      {filterType &&
        filterLabel &&
        (filterType === 'tag' ? (
          <TrendsTagChip label={filterLabel} size="small" />
        ) : (
          <TrendsToolChip label={filterLabel} size="small" />
        ))}

      {/* Trace count */}
      {traceCount !== undefined && (
        <span
          css={{
            fontSize: theme.typography.fontSizeSm,
            color: theme.colors.textSecondary,
            fontWeight: 'normal',
          }}
        >
          {traceCount} traces
        </span>
      )}
    </div>
  );
};
