/**
 * MLflow Trace Insights - Card Wrapper Component
 * 
 * Provides a consistent card layout for all insights components
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';

interface InsightsCardProps {
  title: string;
  subtitle?: string;
  headerContent?: React.ReactNode;
  children: React.ReactNode;
  error?: any;
}

export const InsightsCard = ({ 
  title, 
  subtitle, 
  headerContent,
  children,
  error 
}: InsightsCardProps) => {
  const { theme } = useDesignSystemTheme();

  if (error) {
    return (
      <div
        css={{
          padding: theme.spacing.lg,
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.borders.borderRadiusMd,
          backgroundColor: theme.colors.backgroundPrimary,
          marginBottom: theme.spacing.md,
        }}
      >
        <h3 css={{ 
          margin: `0 0 ${theme.spacing.sm}px 0`,
          fontSize: theme.typography.fontSizeLg,
          fontWeight: 600,
        }}>
          {title}
        </h3>
        <div css={{ color: theme.colors.textValidationDanger }}>
          Error: {error instanceof Error ? error.message : String(error)}
        </div>
      </div>
    );
  }

  return (
    <div
      css={{
        padding: theme.spacing.lg,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borders.borderRadiusMd,
        backgroundColor: theme.colors.backgroundPrimary,
        marginBottom: theme.spacing.md,
      }}
    >
      <div css={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: theme.spacing.md,
      }}>
        <div>
          <h3 css={{ 
            margin: 0,
            fontSize: theme.typography.fontSizeLg,
            fontWeight: 600,
          }}>
            {title}
          </h3>
          {subtitle && (
            <div css={{
              fontSize: theme.typography.fontSizeSm,
              color: theme.colors.textSecondary,
              marginTop: theme.spacing.xs,
            }}>
              {subtitle}
            </div>
          )}
        </div>
        {headerContent && (
          <div>
            {headerContent}
          </div>
        )}
      </div>
      
      <div>
        {children}
      </div>
    </div>
  );
};