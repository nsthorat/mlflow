/**
 * MLflow Trace Insights - Toolbar Component
 * 
 * Top-level toolbar that spans across both LHS and RHS containing time controls and actions
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { InsightsTimeRangeSelector } from './InsightsTimeRangeSelector';

export type InsightsToolbarProps = Record<string, never>;

export const InsightsToolbar: React.FC<InsightsToolbarProps> = () => {
  const { theme } = useDesignSystemTheme();

  return (
    <div
      css={{
        width: '100%',
        height: '60px',
        background: theme.colors.backgroundPrimary,
        borderBottom: `1px solid ${theme.colors.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: `0 ${theme.spacing.lg}px 0 ${theme.spacing.sm}px`,
        flexShrink: 0,
      }}
    >
      {/* Left section - time controls (includes built-in refresh button) */}
      <div css={{ display: 'flex', alignItems: 'center', gap: theme.spacing.md }}>
        <InsightsTimeRangeSelector />
      </div>

      {/* Right section - empty for now */}
      <div css={{ display: 'flex', alignItems: 'center', gap: theme.spacing.md }}>
      </div>
    </div>
  );
};