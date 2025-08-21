// Custom percentile colors for latency trends
export const PERCENTILE_COLORS = {
  P50: '#8BCAE7',
  P90: '#077A9D',
  P99: '#FFAB00',
} as const;

export type PercentileThreshold = 'P50' | 'P90' | 'P99';
