/**
 * Reusable Numeric Value Selector Component
 * 
 * Displays P50, P90, P99 numeric assessment values in a consistent format
 * Used for numeric assessments on Quality Metrics page
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';

interface NumericValues {
  p50?: number | null;
  p90?: number | null;
  p99?: number | null;
}

interface NumericValueSelectorProps {
  values: NumericValues;
}

const formatValue = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return 'N/A';
  return value.toFixed(2);
};

export const NumericValueSelector: React.FC<NumericValueSelectorProps> = ({ values }) => {
  const { theme } = useDesignSystemTheme();

  return (
    <div css={{
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: theme.spacing.md,
    }}>
      <div>
        <div css={{ 
          display: 'flex',
          alignItems: 'baseline',
          gap: theme.spacing.xs,
        }}>
          <span css={{ 
            fontSize: '18px', 
            fontWeight: 300,
            color: '#000',
          }}>
            {formatValue(values.p50)}
          </span>
          <span css={{ 
            fontSize: '11px', 
            color: theme.colors.textSecondary,
            fontWeight: 500,
          }}>
            P50
          </span>
        </div>
      </div>
      <div>
        <div css={{ 
          display: 'flex',
          alignItems: 'baseline',
          gap: theme.spacing.xs,
        }}>
          <span css={{ 
            fontSize: '18px', 
            fontWeight: 300,
            color: '#000',
          }}>
            {formatValue(values.p90)}
          </span>
          <span css={{ 
            fontSize: '11px', 
            color: theme.colors.textSecondary,
            fontWeight: 500,
          }}>
            P90
          </span>
        </div>
      </div>
      <div>
        <div css={{ 
          display: 'flex',
          alignItems: 'baseline',
          gap: theme.spacing.xs,
        }}>
          <span css={{ 
            fontSize: '18px', 
            fontWeight: 300,
            color: '#000',
          }}>
            {formatValue(values.p99)}
          </span>
          <span css={{ 
            fontSize: '11px', 
            color: theme.colors.textSecondary,
            fontWeight: 500,
          }}>
            P99
          </span>
        </div>
      </div>
    </div>
  );
};