/**
 * MLflow Trace Insights - No Data Found Message Component
 * 
 * Reusable message for when there's no data in a time range
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';

interface NoDataFoundMessageProps {
  message?: string;
  hint?: string;
  minHeight?: number;
}

export const NoDataFoundMessage: React.FC<NoDataFoundMessageProps> = ({
  message = 'No data found for this time range',
  hint = 'Try adjusting the time range or ensure traces are being logged',
  minHeight = 200,
}) => {
  const { theme } = useDesignSystemTheme();

  return (
    <div
      css={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: `${theme.spacing.lg * 2}px ${theme.spacing.lg}px`,
        minHeight,
      }}
    >
      <div css={{ 
        fontSize: '14px', 
        color: theme.colors.textSecondary, 
        marginBottom: theme.spacing.xs,
        textAlign: 'center',
      }}>
        {message}
      </div>
      {hint && (
        <div css={{ 
          fontSize: '13px', 
          color: theme.colors.textPlaceholder,
          textAlign: 'center',
        }}>
          {hint}
        </div>
      )}
    </div>
  );
};