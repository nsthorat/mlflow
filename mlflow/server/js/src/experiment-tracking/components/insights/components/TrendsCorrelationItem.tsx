import React, { useMemo, useCallback } from 'react';
import { useDesignSystemTheme, Tag, Typography } from '@databricks/design-system';
import { NPMI_THRESHOLDS } from '../constants/npmiThresholds';
import { CARD_STYLES } from '../constants/cardStyles';
import {
  INSIGHTS_CORRELATION_ITEM_STRONG_COMPONENT_ID,
  INSIGHTS_CORRELATION_ITEM_MODERATE_COMPONENT_ID,
  INSIGHTS_CORRELATION_ITEM_WEAK_COMPONENT_ID,
  INSIGHTS_CORRELATION_ITEM_LABEL_COMPONENT_ID,
} from '../constants/insightsLogging';
import { TrendsTagChip } from './TrendsTagChip';
import { TrendsToolChip } from './TrendsToolChip';

interface TrendsCorrelationItemProps {
  label: string;
  percentage: number;
  npmi?: number;
  type: 'tag' | 'tool' | 'assessment' | 'latency';
  count: number;
  totalTracesInWindow?: number;
  onClick?: () => void;
}

export const TrendsCorrelationItem = ({
  label,
  percentage,
  npmi,
  type,
  count,
  totalTracesInWindow,
  onClick,
}: TrendsCorrelationItemProps) => {
  const { theme } = useDesignSystemTheme();

  // Determine correlation strength badge - memoized for performance
  const getCorrelationBadge = useCallback(() => {
    if (npmi === undefined) return null;

    if (npmi >= NPMI_THRESHOLDS.STRONG_CORRELATION) {
      return (
        <Tag
          componentId={INSIGHTS_CORRELATION_ITEM_STRONG_COMPONENT_ID}
          color="lime"
          css={{
            fontSize: theme.typography.fontSizeSm,
          }}
        >
          Strong
        </Tag>
      );
    } else if (npmi > NPMI_THRESHOLDS.MODERATE_CORRELATION) {
      return (
        <Tag
          color="teal"
          componentId={INSIGHTS_CORRELATION_ITEM_MODERATE_COMPONENT_ID}
          css={{
            fontSize: theme.typography.fontSizeSm,
          }}
        >
          Moderate
        </Tag>
      );
    } else if (npmi > NPMI_THRESHOLDS.WEAK_CORRELATION) {
      return (
        <Tag
          componentId={INSIGHTS_CORRELATION_ITEM_WEAK_COMPONENT_ID}
          css={{
            fontSize: theme.typography.fontSizeSm,
          }}
        >
          Weak
        </Tag>
      );
    } else {
      return null; // Don't show badge for very weak correlations
    }
  }, [npmi, theme.typography.fontSizeSm]);

  // Memoize correlation badge calculation for performance
  const correlationBadge = useMemo(() => getCorrelationBadge(), [getCorrelationBadge]);

  return (
    <div
      css={{
        color: CARD_STYLES.COLORS.PRIMARY_TEXT,
        backgroundColor: CARD_STYLES.COLORS.BACKGROUND,
        display: 'flex',
        flexDirection: 'column',
        borderRadius: theme.spacing.sm,
        border: CARD_STYLES.BORDERS.DEFAULT,
        boxShadow: CARD_STYLES.SHADOWS.DEFAULT,
        padding: theme.spacing.sm,
        gap: theme.spacing.sm,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: onClick ? CARD_STYLES.SHADOWS.HOVER : CARD_STYLES.SHADOWS.DEFAULT,
        },
      }}
      onClick={onClick}
    >
      {/* First row: Icon + Label ... justify between ... Badge */}
      <div
        css={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div
          css={{
            display: 'flex',
            alignItems: 'center',
            flex: 1,
            paddingRight: theme.spacing.sm,
            overflow: 'hidden',
          }}
        >
          {type === 'tag' ? (
            <TrendsTagChip label={label} componentId={INSIGHTS_CORRELATION_ITEM_LABEL_COMPONENT_ID} size="small" />
          ) : type === 'tool' ? (
            <TrendsToolChip label={label} componentId={INSIGHTS_CORRELATION_ITEM_LABEL_COMPONENT_ID} size="small" />
          ) : (
            <TrendsTagChip label={label} componentId={INSIGHTS_CORRELATION_ITEM_LABEL_COMPONENT_ID} size="small" />
          )}
        </div>
        {correlationBadge && <div css={{ flexShrink: 0 }}>{correlationBadge}</div>}
      </div>

      {/* Second row: Custom progress bar */}
      <div
        css={{
          position: 'relative',
          width: '100%',
          height: 8,
          backgroundColor: theme.colors.blue200,
          borderRadius: theme.spacing.sm, // Large rounded corners
          overflow: 'hidden',
        }}
      >
        <div
          css={{
            position: 'absolute',
            top: 0,
            left: 0,
            height: '100%',
            backgroundColor: CARD_STYLES.COLORS.PROGRESS_BAR,
            borderRadius: theme.spacing.sm, // Match parent radius
            width: `${Math.min(Math.max(percentage, 0), 100)}%`,
            transition: 'width 0.3s ease',
          }}
        />
      </div>

      {/* Third row: Percentage */}
      <Typography.Hint
        css={{
          fontSize: theme.typography.fontSizeSm,
          color: theme.colors.textSecondary,
          textAlign: 'left',
        }}
      >
        {count.toLocaleString()} traces • {percentage.toFixed(1)}% of slice
        {totalTracesInWindow ? ` • ${((count / totalTracesInWindow) * 100).toFixed(1)}% of total` : ''}
      </Typography.Hint>
    </div>
  );
};
