import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { useRecordComponentView } from './utils/analyticsUtils';
import { InsightsVolumeCard } from './pages/traffic-and-cost/InsightsVolumeCard';
import { InsightsLatencyCard } from './pages/traffic-and-cost/InsightsLatencyCard';
import { InsightsErrorRateCard } from './pages/traffic-and-cost/InsightsErrorRateCard';
import { InsightsPageBaseProps } from './types/insightsTypes';
import { INSIGHTS_TRAFFIC_AND_COST_PAGE_VIEW } from './constants/insightsLogging';

interface InsightsPageTrafficAndCostProps extends InsightsPageBaseProps {}

export const InsightsPageTrafficAndCost = ({
  experimentId = '',
}: InsightsPageTrafficAndCostProps) => {
  const { theme } = useDesignSystemTheme();
  const { elementRef: trafficAndCostViewRef } = useRecordComponentView<HTMLDivElement>(
    'div',
    INSIGHTS_TRAFFIC_AND_COST_PAGE_VIEW,
  );

  return (
    <div
      ref={trafficAndCostViewRef}
      css={{
        padding: `${theme.spacing.xs}px ${theme.spacing.sm}px`,
        height: '100%',
        width: '100%',
        overflowY: 'auto',
        boxSizing: 'border-box',
      }}
    >
      {/* Volume Card - Full Width */}
      <div css={{ marginBottom: theme.spacing.md }}>
        <InsightsVolumeCard experimentId={experimentId} />
      </div>

      {/* Latency and Error Rate Cards - Side by Side */}
      <div css={{ display: 'flex', gap: theme.spacing.md, width: '100%' }}>
        <div css={{ flex: '1 1 0%', minWidth: 0 }}>
          <InsightsLatencyCard experimentId={experimentId} />
        </div>
        <div css={{ flex: '1 1 0%', minWidth: 0 }}>
          <InsightsErrorRateCard experimentId={experimentId} />
        </div>
      </div>
    </div>
  );
};
