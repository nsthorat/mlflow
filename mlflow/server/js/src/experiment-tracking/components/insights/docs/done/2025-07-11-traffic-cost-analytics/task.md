# Add Trends (insights) for Traffic & cost

**Status:** Done
**Completed:** 2025-07-11
**Commit:** 45b5c8b6fea57

## Description
Implemented comprehensive Traffic & Cost analytics with enhanced modal system, TraceInfoV3 integration, and NPMI correlation optimizations.

## Implementation
- **Enhanced Modal Title System**: Created sophisticated modal titles with proper separation between slice type (error/latency) and optional filters (tag/tool)
- **TraceInfoV3 Migration**: Replaced custom TraceEntry interface with shared TraceInfoV3 type from @databricks/web-shared/genai-traces-table
- **NPMI Threshold Optimization**: Fixed correlation queries to only show HIGH correlations (NPMI ≥ 0.7) instead of moderate correlations (≥ 0.3)
- **Latency Button Enhancement**: Added trace count display to latency "View Traces" button
- **React Hooks Compliance**: Fixed React Hooks order warnings by properly sequencing useMemo calls

## Key Features
- **Volume Card**: Total trace count and traffic volume trends over time
- **Latency Card**: P50, P90, P99 latency percentiles with time-series charts
- **Error Rate Card**: Error rate trends and error count visualization
- **Interactive Charts**: Time-series data exploration with drill-down capabilities
- **Modal System**: TrendsModalTitle component with conditional styling
- **Correlation Analysis**: NPMI-based correlation discovery with proper thresholds

## Files Changed
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/TracesV3Logs.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/TracesV3View.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/insights/TraceInsights.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/insights/TraceInsightsOpinionatedCards.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/TrafficAndCost.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/components/TrendsModalTitle.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/components/TrendsSliceCard.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/pages/traffic-and-cost/TrendsErrorRateCard.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/pages/traffic-and-cost/TrendsLatencyCard.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/pages/traffic-and-cost/TrendsVolumeCard.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/constants/npmiThresholds.ts`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/hooks/useTrafficAndCostQueries.ts`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/utils/dataProcessingUtils.ts`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/utils/dataTransformations.ts`

## Testing
- Unit tests for data transformation utilities and hook validation logic
- Manual testing with modal title rendering across different slice types
- Integration testing for complete flow from SQL queries through UI components
- Performance testing with NPMI threshold filtering

## Notes
This implementation established the core analytics patterns and UI components that would be reused across all other trends pages. The NPMI threshold optimization significantly improved query performance by filtering at the SQL level.