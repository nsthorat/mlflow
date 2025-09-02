/**
 * Reusable Latency Value Selector Component
 * 
 * Displays P50, P90, P99 latency values in a consistent format
 * Used across Tools and Traffic & Cost pages
 */

import React from 'react';
import { useDesignSystemTheme } from '@databricks/design-system';
import { PERCENTILE_COLORS } from '../constants/percentileColors';

interface LatencyValues {
  p50?: number | null;
  p90?: number | null;
  p99?: number | null;
}

interface LatencyValueSelectorProps {
  latencies: LatencyValues;
}

const formatLatency = (latencyMs: number | null | undefined): string => {
  if (latencyMs === null || latencyMs === undefined) return 'N/A';
  if (latencyMs === 0) return '<1ms';
  return latencyMs > 1000 
    ? `${(latencyMs / 1000).toFixed(2)}s` 
    : `${latencyMs.toFixed(0)}ms`;
};

export const LatencyValueSelector: React.FC<LatencyValueSelectorProps> = ({ latencies }) => {
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
            fontSize: '20px', 
            fontWeight: 300,
            color: '#000',
          }}>
            {formatLatency(latencies.p50)}
          </span>
          <span css={{ 
            fontSize: '12px', 
            color: PERCENTILE_COLORS.P50,
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
            fontSize: '20px', 
            fontWeight: 300,
            color: '#000',
          }}>
            {formatLatency(latencies.p90)}
          </span>
          <span css={{ 
            fontSize: '12px', 
            color: PERCENTILE_COLORS.P90,
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
            fontSize: '20px', 
            fontWeight: 300,
            color: '#000',
          }}>
            {formatLatency(latencies.p99)}
          </span>
          <span css={{ 
            fontSize: '12px', 
            color: PERCENTILE_COLORS.P99,
            fontWeight: 500,
          }}>
            P99
          </span>
        </div>
      </div>
    </div>
  );
};