import type { ReactNode } from 'react';
import React from 'react';
import { useInsightsTimeRange } from './useInsightsTimeRange';

// Simplified wrapper that provides compatibility with the MonitoringConfig pattern
// but delegates all state management to URL-based useInsightsTimeRange hook

export interface InsightsTimeConfig {
  dateNow: Date;
  setDateNow: (date: Date) => void;
}

interface InsightsTimeConfigProviderProps {
  children: ReactNode;
}

export const InsightsTimeConfigProvider: React.FC<InsightsTimeConfigProviderProps> = ({ children }) => {
  // All state management is handled by URL-based hook
  return <>{children}</>;
};

export const useInsightsTimeConfig = (): InsightsTimeConfig => {
  const [timeRangeFilters, , refreshDateNow] = useInsightsTimeRange();

  return {
    dateNow: timeRangeFilters.dateNow || new Date(),
    setDateNow: refreshDateNow,
  };
};