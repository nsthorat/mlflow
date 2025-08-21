/**
 * Skeleton loading components for trends features
 * Provides consistent loading states across all trend components
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';

interface TrendsSkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  className?: string;
}

/**
 * Base skeleton component with shimmer animation
 */
const TrendsSkeleton = ({ width = '100%', height = 16, borderRadius = 4, className }: TrendsSkeletonProps) => {
  const { theme } = useDesignSystemTheme();

  return (
    <div
      className={className}
      css={{
        width,
        height,
        borderRadius,
        backgroundColor: theme.colors.backgroundSecondary,
        position: 'relative',
        overflow: 'hidden',
        '&::after': {
          content: '""',
          position: 'absolute',
          top: 0,
          right: 0,
          bottom: 0,
          left: 0,
          background: `linear-gradient(90deg, transparent, ${theme.colors.backgroundSecondary}, transparent)`,
          animation: 'shimmer 1.5s infinite',
        },
        '@keyframes shimmer': {
          '0%': {
            transform: 'translateX(-100%)',
          },
          '100%': {
            transform: 'translateX(100%)',
          },
        },
      }}
    />
  );
};

/**
 * Skeleton for card components
 */
export const TrendsCardSkeleton = () => {
  const { theme } = useDesignSystemTheme();

  return (
    <div
      css={{
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.general.borderRadiusBase,
        padding: theme.spacing.md,
        backgroundColor: theme.colors.backgroundPrimary,
        minHeight: 300,
      }}
    >
      {/* Header */}
      <div css={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm, marginBottom: theme.spacing.md }}>
        <TrendsSkeleton width={24} height={24} borderRadius="50%" />
        <TrendsSkeleton width={80} height={20} />
      </div>

      {/* Main display */}
      <div css={{ marginBottom: theme.spacing.lg }}>
        <TrendsSkeleton width={120} height={32} />
      </div>

      {/* Chart area */}
      <div css={{ marginBottom: theme.spacing.md }}>
        <TrendsSkeleton width="100%" height={150} borderRadius={8} />
      </div>

      {/* Correlations section */}
      <div>
        <TrendsSkeleton width={100} height={16} css={{ marginBottom: theme.spacing.sm }} />
        <div css={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.xs }}>
          {[1, 2, 3].map((i) => (
            <div key={i} css={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
              <TrendsSkeleton width={60} height={14} />
              <TrendsSkeleton width={40} height={14} />
              <TrendsSkeleton width={30} height={14} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * Skeleton for chart components
 */
const TrendsChartSkeleton = ({ height = 150 }: { height?: number }) => {
  const { theme } = useDesignSystemTheme();

  return (
    <div css={{ width: '100%', height }}>
      <TrendsSkeleton width="100%" height="100%" borderRadius={8} />
    </div>
  );
};

/**
 * Skeleton for trace list
 */
export const TrendsTraceListSkeleton = () => {
  const { theme } = useDesignSystemTheme();

  return (
    <div css={{ padding: theme.spacing.sm }}>
      {/* Header */}
      <div
        css={{
          display: 'flex',
          gap: theme.spacing.md,
          marginBottom: theme.spacing.sm,
          paddingBottom: theme.spacing.sm,
          borderBottom: `1px solid ${theme.colors.border}`,
        }}
      >
        <TrendsSkeleton width={200} height={16} />
        <TrendsSkeleton width={80} height={16} />
        <TrendsSkeleton width={60} height={16} />
        <TrendsSkeleton width={100} height={16} />
      </div>

      {/* Rows */}
      <div css={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.xs }}>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} css={{ display: 'flex', gap: theme.spacing.md, alignItems: 'center' }}>
            <TrendsSkeleton width={200} height={16} />
            <TrendsSkeleton width={80} height={16} />
            <TrendsSkeleton width={60} height={16} />
            <TrendsSkeleton width={100} height={16} />
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * Skeleton for correlation items
 */
const TrendsCorrelationSkeleton = () => {
  const { theme } = useDesignSystemTheme();

  return (
    <div css={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.xs }}>
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} css={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div css={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
            <TrendsSkeleton width={80} height={14} />
            <TrendsSkeleton width={40} height={14} />
          </div>
          <TrendsSkeleton width={30} height={14} />
        </div>
      ))}
    </div>
  );
};

/**
 * Empty state component for when there's no data
 */
export const TrendsEmptyState = ({
  title = 'No data available',
  description = 'There is no data to display for the selected time range.',
  icon,
}: {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
}) => {
  const { theme } = useDesignSystemTheme();

  return (
    <div
      css={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: theme.spacing.lg,
        textAlign: 'center',
        gap: theme.spacing.md,
        minHeight: 200,
        color: theme.colors.textSecondary,
      }}
    >
      {icon && <div css={{ fontSize: 48, opacity: 0.6 }}>{icon}</div>}
      <div>
        <div
          css={{
            fontSize: theme.typography.fontSizeMd,
            fontWeight: 400,
            marginBottom: theme.spacing.xs,
            color: theme.colors.textPrimary,
          }}
        >
          {title}
        </div>
        <div
          css={{
            fontSize: theme.typography.fontSizeSm,
            color: theme.colors.textSecondary,
          }}
        >
          {description}
        </div>
      </div>
    </div>
  );
};
