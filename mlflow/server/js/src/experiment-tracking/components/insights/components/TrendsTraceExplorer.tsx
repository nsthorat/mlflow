import React, { useMemo } from 'react';
import { useDesignSystemTheme, Spinner, Typography } from '@databricks/design-system';
import { ModelTraceExplorer } from '@databricks/web-shared/model-trace-explorer';
import { TraceEntry, TraceData } from '../types/insightsTypes';

interface TrendsTraceExplorerProps {
  trace: TraceEntry | undefined;
  traceData: TraceData | null;
  isLoading: boolean;
}

export const TrendsTraceExplorer = ({ trace, traceData, isLoading }: TrendsTraceExplorerProps) => {
  const { theme } = useDesignSystemTheme();

  // Transform the trace data to match the expected format for ModelTrace - memoized for performance
  // This must be called before any conditional returns to maintain hook order
  const transformedTraceData = useMemo(() => {
    return traceData && traceData.info
      ? {
          info: traceData.info.trace?.trace_info || traceData.info,
          data: traceData.data,
        }
      : null;
  }, [traceData]);

  if (isLoading) {
    return (
      <div
        css={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          flexDirection: 'column',
          gap: theme.spacing.md,
        }}
      >
        <Spinner size="large" />
        <Typography.Text color="secondary">Loading trace data...</Typography.Text>
      </div>
    );
  }

  if (!trace) {
    return (
      <div
        css={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          flexDirection: 'column',
          gap: theme.spacing.md,
        }}
      >
        <Typography.Text color="secondary">Select a trace to view details</Typography.Text>
      </div>
    );
  }

  if (!traceData) {
    return (
      <div
        css={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          flexDirection: 'column',
          gap: theme.spacing.md,
        }}
      >
        <Typography.Text color="secondary">Failed to load trace data</Typography.Text>
      </div>
    );
  }

  return (
    <div
      css={{
        height: '100%',
        width: '100%',
        overflow: 'auto',
        padding: theme.spacing.md,
      }}
    >
      {/* Model trace explorer */}
      <div
        css={{
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.general.borderRadiusBase,
          overflow: 'hidden',
          height: '100%',
        }}
      >
        {transformedTraceData ? (
          <ModelTraceExplorer
            modelTrace={transformedTraceData as any}
            css={{
              height: '100%',
              '& .model-trace-container': {
                height: '100%',
              },
            }}
          />
        ) : (
          <div
            css={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
            }}
          >
            <Typography.Text color="secondary">Unable to load trace data</Typography.Text>
          </div>
        )}
      </div>
    </div>
  );
};
