import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';

interface TrendsMetricCardProps {
  icon: React.ReactNode | null;
  title: string;
  value: string;
  subtitle?: string;
  color?: string;
  trend?: 'up' | 'down' | 'neutral';
}

export const TrendsMetricCard = ({ icon, title, value, subtitle, color, trend }: TrendsMetricCardProps) => {
  const { theme } = useDesignSystemTheme();

  const getTrendIndicator = () => {
    if (!trend || trend === 'neutral') return null;
    return (
      <span
        css={{
          fontSize: theme.typography.fontSizeSm,
          color: trend === 'up' ? theme.colors.textValidationSuccess : theme.colors.textValidationDanger,
          marginLeft: theme.spacing.xs,
        }}
      >
        {trend === 'up' ? '↗' : '↘'}
      </span>
    );
  };

  return (
    <div
      css={{
        padding: theme.spacing.sm,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borders.borderRadiusMd,
        backgroundColor: theme.colors.backgroundPrimary,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        minHeight: 60,
        justifyContent: 'center',
        gap: theme.spacing.xs,
      }}
    >
      {icon && (
        <div
          css={{
            fontSize: theme.typography.fontSizeLg,
            color: color || theme.colors.primary,
          }}
        >
          {icon}
        </div>
      )}

      <div
        css={{
          fontSize: theme.typography.fontSizeXl,
          color: theme.colors.textPrimary,
          display: 'flex',
          alignItems: 'center',
        }}
      >
        {value}
        {getTrendIndicator()}
      </div>

      <div
        css={{
          fontSize: theme.typography.fontSizeSm,
          color: theme.colors.textSecondary,
        }}
      >
        {title}
      </div>

      {subtitle && (
        <div
          css={{
            fontSize: theme.typography.fontSizeSm,
            color: theme.colors.textPlaceholder,
          }}
        >
          {subtitle}
        </div>
      )}
    </div>
  );
};
