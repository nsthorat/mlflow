import React from 'react';
import { Tag, useDesignSystemTheme } from '@databricks/design-system';
import { INSIGHTS_CARD_TITLE_COMPONENT_ID } from '../constants/insightsLogging';

interface TrendsCardTitleProps {
  icon: React.ReactNode;
  title: string;
}

export const TrendsCardTitle = ({ icon, title }: TrendsCardTitleProps) => {
  const { theme } = useDesignSystemTheme();

  return (
    <div css={{ display: 'flex' }}>
      <Tag
        componentId={INSIGHTS_CARD_TITLE_COMPONENT_ID}
        css={{
          backgroundColor: theme.colors.grey050,
          border: 'none',
          fontSize: theme.typography.fontSizeBase,
          fontWeight: 500,
          padding: `${theme.spacing.xs / 2}px ${theme.spacing.xs / 2}px`,
        }}
      >
        <div css={{ display: 'flex', alignItems: 'center', gap: theme.spacing.xs }}>
          <span css={{ color: theme.colors.textSecondary, display: 'flex', alignItems: 'center' }}>{icon}</span>
          <span css={{ color: theme.colors.textPrimary }}>{title}</span>
        </div>
      </Tag>
    </div>
  );
};
