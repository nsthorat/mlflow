/**
 * MLflow Trace Insights - Toolbar Component
 * 
 * Top-level toolbar that spans across both LHS and RHS containing time controls and actions
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { InsightsTimeRangeSelector } from './InsightsTimeRangeSelector';

export interface InsightsToolbarProps {
  // Future: Could add more toolbar actions here if needed
}

export const InsightsToolbar: React.FC<InsightsToolbarProps> = () => {
  const { theme } = useDesignSystemTheme();

  return (
    <div
      css={{
        width: '100%',
        height: '60px',
        background: theme.colors.backgroundSecondary,
        borderBottom: `1px solid ${theme.colors.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: `0 ${theme.spacing.lg}px`,
        flexShrink: 0,
      }}
    >
      {/* Left section - could add breadcrumbs or title here */}
      <div css={{ display: 'flex', alignItems: 'center', gap: theme.spacing.md }}>
        <h2
          css={{
            margin: 0,
            fontSize: theme.typography.fontSizeLg,
            fontWeight: 600,
            color: theme.colors.textPrimary,
          }}
        >
          Trace Insights
        </h2>
      </div>

      {/* Right section - time controls (includes built-in refresh button) */}
      <div css={{ display: 'flex', alignItems: 'center', gap: theme.spacing.md }}>
        <InsightsTimeRangeSelector />
      </div>
    </div>
  );
};