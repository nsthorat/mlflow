import React from 'react';
import { useDesignSystemTheme, Tag, WrenchIcon } from '@databricks/design-system';
import { TRENDS_MODAL_CORRELATION_TAG_COMPONENT_ID } from '../constants/insightsLogging';

interface TrendsToolChipProps {
  label: string;
  componentId?: string;
  size?: 'small' | 'normal';
}

export const TrendsToolChip = ({
  label,
  componentId = TRENDS_MODAL_CORRELATION_TAG_COMPONENT_ID,
  size = 'normal',
}: TrendsToolChipProps) => {
  const { theme } = useDesignSystemTheme();

  const fontSize = size === 'small' ? theme.typography.fontSizeSm : theme.typography.fontSizeBase;

  return (
    <Tag
      componentId={componentId}
      css={{
        backgroundColor: theme.colors.grey050,
        border: 'none',
        fontSize,
        fontWeight: size === 'small' ? 'normal' : 500,
      }}
    >
      <span
        css={{
          display: 'flex',
          alignItems: 'center',
          gap: theme.spacing.sm,
          fontSize,
          lineHeight: theme.typography.lineHeightBase,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          maxWidth: '100%',
        }}
      >
        <WrenchIcon
          css={{
            width: 12,
            height: 12,
            color: theme.colors.textSecondary,
            flexShrink: 0,
          }}
        />
        <span css={{ color: theme.colors.textPrimary }}>{label}</span>
      </span>
    </Tag>
  );
};
