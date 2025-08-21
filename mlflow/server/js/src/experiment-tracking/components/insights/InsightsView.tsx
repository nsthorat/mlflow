/**
 * MLflow Trace Insights - Main View Component
 * 
 * Main entry point for insights feature with left sidebar navigation.
 * Matches reference implementation structure.
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { InsightsPageTrafficAndCost } from './TrafficAndCost';
import { InsightsPageQualityMetrics } from './pages/quality-metrics/InsightsPageQualityMetrics';
import { InsightsPageTools } from './pages/tools/InsightsPageTools';
import { InsightsPageTags } from './pages/tags/InsightsPageTags';
import { InsightsPageBaseProps } from './types/insightsTypes';
import { useInsightsPageMode, type InsightsPageMode } from './hooks/useInsightsPageMode';

interface InsightsViewProps extends InsightsPageBaseProps {
  // Additional props can be added here
}

interface NavigationItem {
  id: InsightsPageMode;
  label: string;
  icon?: string;
  implemented: boolean;
}

const navigationItems: NavigationItem[] = [
  { id: 'traffic', label: 'Traffic & Cost', icon: '📊', implemented: true },
  { id: 'quality', label: 'Quality Metrics', icon: '✅', implemented: true },
  { id: 'tools', label: 'Tools', icon: '🔧', implemented: true },
  { id: 'tags', label: 'Tags', icon: '🏷️', implemented: true },
  { id: 'topics', label: 'Topics', icon: '💬', implemented: false },
  { id: 'create', label: 'Create View', icon: '➕', implemented: false },
];

export const InsightsView: React.FC<InsightsViewProps> = ({
  experimentId
}) => {
  const { theme } = useDesignSystemTheme();
  const [activePage, setActivePage] = useInsightsPageMode();

  const renderActivePage = () => {
    switch (activePage) {
      case 'traffic':
        return (
          <InsightsPageTrafficAndCost
            experimentId={experimentId}
          />
        );
      case 'quality':
        return (
          <InsightsPageQualityMetrics
            experimentId={experimentId}
          />
        );
      case 'tools':
        return (
          <InsightsPageTools
            experimentId={experimentId}
          />
        );
      case 'tags':
        return (
          <InsightsPageTags
            experimentId={experimentId}
          />
        );
      case 'topics':
        return (
          <div style={{ padding: theme.spacing.lg }}>
            <h2>Topics</h2>
            <p style={{ color: theme.colors.textSecondary }}>
              Topic clustering and analysis placeholder...
            </p>
          </div>
        );
      case 'create':
        return (
          <div style={{ padding: theme.spacing.lg }}>
            <h2>Create View</h2>
            <p style={{ color: theme.colors.textSecondary }}>
              Custom view creation placeholder...
            </p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div
      css={{
        height: '100%',
        width: '100%',
        display: 'flex',
        flexDirection: 'row',
        background: theme.colors.backgroundPrimary,
      }}
    >
      {/* Left Sidebar Navigation */}
      <div
        css={{
          width: '240px',
          borderRight: `1px solid ${theme.colors.border}`,
          background: theme.colors.backgroundSecondary,
          display: 'flex',
          flexDirection: 'column',
          padding: theme.spacing.sm,
        }}
      >
        <div
          css={{
            padding: `${theme.spacing.sm}px ${theme.spacing.md}px`,
            marginBottom: theme.spacing.sm,
            borderBottom: `1px solid ${theme.colors.border}`,
          }}
        >
          <h3
            css={{
              margin: 0,
              fontSize: theme.typography.fontSizeLg,
              fontWeight: 600,
              color: theme.colors.textPrimary,
            }}
          >
            Trace Insights
          </h3>
        </div>

        {/* Navigation Items */}
        <nav css={{ flex: 1 }}>
          {navigationItems.map((item) => (
            <button
              key={item.id}
              css={{
                width: '100%',
                padding: `${theme.spacing.sm}px ${theme.spacing.md}px`,
                border: 'none',
                background: activePage === item.id 
                  ? theme.colors.actionDefaultBackgroundPress 
                  : 'transparent',
                color: activePage === item.id 
                  ? theme.colors.textPrimary 
                  : item.implemented 
                    ? theme.colors.textSecondary 
                    : theme.colors.textPlaceholder,
                borderRadius: theme.general.borderRadiusBase,
                cursor: item.implemented ? 'pointer' : 'not-allowed',
                fontSize: theme.typography.fontSizeBase,
                fontWeight: activePage === item.id ? 600 : 400,
                textAlign: 'left',
                display: 'flex',
                alignItems: 'center',
                gap: theme.spacing.xs,
                marginBottom: theme.spacing.xs,
                transition: 'all 0.2s ease',
                '&:hover': item.implemented ? {
                  background: activePage !== item.id 
                    ? theme.colors.actionDefaultBackgroundHover 
                    : undefined,
                } : {},
              }}
              onClick={() => item.implemented && setActivePage(item.id)}
              disabled={!item.implemented}
            >
              {item.icon && <span>{item.icon}</span>}
              <span>{item.label}</span>
              {!item.implemented && (
                <span
                  css={{
                    marginLeft: 'auto',
                    fontSize: theme.typography.fontSizeSm,
                    color: theme.colors.textPlaceholder,
                    fontStyle: 'italic',
                  }}
                >
                  Soon
                </span>
              )}
            </button>
          ))}
        </nav>

        {/* Footer Info */}
        <div
          css={{
            padding: `${theme.spacing.sm}px ${theme.spacing.md}px`,
            borderTop: `1px solid ${theme.colors.border}`,
            fontSize: theme.typography.fontSizeSm,
            color: theme.colors.textSecondary,
          }}
        >
          <div>Experiment: {experimentId || 'None'}</div>
          <div>Backend: SQLAlchemy</div>
        </div>
      </div>

      {/* Main Content Area */}
      <div
        css={{
          flex: 1,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {renderActivePage()}
      </div>
    </div>
  );
};