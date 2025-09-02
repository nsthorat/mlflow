/**
 * Data Type Tag Component
 * 
 * Small tag component for displaying assessment data types
 * Used inline with titles in Quality Metrics
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';

interface DataTypeTagProps {
  dataType: 'boolean' | 'pass-fail' | 'numeric' | 'string';
}

export const DataTypeTag: React.FC<DataTypeTagProps> = ({ dataType }) => {
  const { theme } = useDesignSystemTheme();

  const getTagColor = (type: string) => {
    switch (type) {
      case 'boolean':
        return theme.colors.tagDefault;
      case 'pass-fail':
        return theme.colors.green400 || theme.colors.tagDefault;
      case 'numeric':
        return theme.colors.blue400 || theme.colors.tagDefault;
      case 'string':
        return theme.colors.grey400 || theme.colors.tagDefault;
      default:
        return theme.colors.tagDefault;
    }
  };

  const getDisplayText = (type: string) => {
    return type === 'pass-fail' ? 'PASS/FAIL' : type.toUpperCase();
  };

  return (
    <span css={{
      fontSize: '10px',
      fontWeight: 600,
      padding: `${theme.spacing.xs / 2}px ${theme.spacing.xs}px`,
      backgroundColor: getTagColor(dataType),
      color: theme.colors.textPrimary,
      borderRadius: theme.borders.borderRadiusMd,
      border: `1px solid ${theme.colors.border}`,
      textTransform: 'uppercase',
      letterSpacing: '0.025em',
      marginLeft: theme.spacing.sm,
    }}>
      {getDisplayText(dataType)}
    </span>
  );
};