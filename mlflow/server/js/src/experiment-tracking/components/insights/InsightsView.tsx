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
import { InsightsTimeConfigProvider } from './hooks/useInsightsTimeContext';
import { InsightsToolbar } from './components/InsightsToolbar';

interface InsightsViewProps extends InsightsPageBaseProps {
  subpage?: string | null;
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
  { id: 'create', label: 'Create View', icon: '➕', implemented: true },
];

const InsightsViewImpl: React.FC<InsightsViewProps> = ({ experimentId, subpage }) => {
  const { theme } = useDesignSystemTheme();
  const [activePage, setActivePage] = useInsightsPageMode();

  const renderActivePage = () => {
    switch (activePage) {
      case 'traffic':
        return <InsightsPageTrafficAndCost experimentId={experimentId} />;
      case 'quality':
        return <InsightsPageQualityMetrics experimentId={experimentId} />;
      case 'tools':
        return <InsightsPageTools experimentId={experimentId} />;
      case 'tags':
        return <InsightsPageTags experimentId={experimentId} />;
      case 'create':
        return (
          <div style={{ padding: theme.spacing.lg }}>
            <h2>Create Custom View</h2>
            <div style={{ marginTop: theme.spacing.md }}>
              <p style={{ color: theme.colors.textSecondary, marginBottom: theme.spacing.md }}>
                Create custom views to analyze your traces with personalized metrics and visualizations.
              </p>
              <div style={{ 
                padding: theme.spacing.lg, 
                border: `2px dashed ${theme.colors.border}`,
                borderRadius: theme.general.borderRadiusBase,
                textAlign: 'center',
                background: theme.colors.backgroundSecondary
              }}>
                <p style={{ color: theme.colors.textPlaceholder, fontSize: theme.typography.fontSizeLg }}>
                  Drag and drop components here to build your custom view
                </p>
                <button style={{
                  marginTop: theme.spacing.md,
                  padding: `${theme.spacing.sm}px ${theme.spacing.md}px`,
                  background: theme.colors.actionPrimaryBackgroundDefault,
                  color: theme.colors.white,
                  border: 'none',
                  borderRadius: theme.general.borderRadiusBase,
                  cursor: 'pointer',
                  fontSize: theme.typography.fontSizeBase
                }}>
                  + Add Component
                </button>
              </div>
            </div>
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
        flexDirection: 'column',
        overflow: 'hidden',
        background: theme.colors.backgroundPrimary,
      }}
    >
      {/* Top Toolbar */}
      <InsightsToolbar />

      {/* Main Content - Sidebar + Main Area */}
      <div
        css={{
          flex: 1,
          display: 'flex',
          flexDirection: 'row',
          overflow: 'hidden',
        }}
      >
        {/* Left Sidebar Navigation */}
        <div
          css={{
            width: '200px',
            borderRight: `1px solid ${theme.colors.border}`,
            background: theme.colors.backgroundSecondary,
            display: 'flex',
            flexDirection: 'column',
            padding: theme.spacing.sm,
          }}
        >
          {/* Navigation Items */}
          <nav css={{ flex: 1 }}>
            {navigationItems.map((item) => (
              <button
                key={item.id}
                css={{
                  width: '100%',
                  padding: `${theme.spacing.sm}px ${theme.spacing.md}px`,
                  border: 'none',
                  background: activePage === item.id ? theme.colors.actionDefaultBackgroundPress : 'transparent',
                  color:
                    activePage === item.id
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
                  '&:hover': item.implemented
                    ? {
                        background: activePage !== item.id ? theme.colors.actionDefaultBackgroundHover : undefined,
                      }
                    : {},
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
        </div>

        {/* Main Content Area */}
        <div
          css={{
            flex: 1,
            overflow: 'auto',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {renderActivePage()}
        </div>
      </div>
    </div>
  );
};

export const InsightsView: React.FC<InsightsViewProps> = (props) => (
  <InsightsTimeConfigProvider>
    <InsightsViewImpl {...props} />
  </InsightsTimeConfigProvider>
);
