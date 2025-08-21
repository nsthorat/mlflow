# Add trace insights navigation scaffold with URL parameter support

**Status:** Done
**Completed:** 2025-07-09
**Commit:** a3428d0cdd100

## Description
Add navigation scaffold for Trends feature with URL parameter support and placeholder components.

## Implementation
- Added safex flag `databricks.fe.mlflow.enableTraceInsights` for left navigation pane
- Implemented Tree component navigation with collapsible Trends section
- Added URL parameter `tracesNavigation` for navigation state persistence
- Created placeholder trend components: TrafficAndCost, QualityMetrics, Tools, Topics, CreateView
- Updated TracesV3Logs to conditionally render navigation pane and trend components
- Show navigation even in empty state when feature flag is enabled

## Files Changed
- `js/packages/web-shared/src/flags/__generated__/SAFEXTypes.ts`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/TraceInsightsNavigation.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/TracesV3Logs.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/TracesV3View.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/CreateView.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/QualityMetrics.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/Tools.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/Topics.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/TrafficAndCost.tsx`
- `mlflow/web/js/src/experiment-tracking/pages/experiment-evaluation-monitoring/hooks/useTraceInsightsNavState.tsx`

## Testing
- Verified navigation appears with safex flag enabled
- Confirmed URL parameter persistence works correctly
- Tested all navigation items route to "All traces" as specified
- Tested empty state navigation behavior

## Notes
This established the foundation for the Trends feature with proper navigation structure and URL state management.