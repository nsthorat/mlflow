# Trends Analytics Implementation

## Overview

This document describes the analytics tracking implementation for the MLflow Traces Trends feature using `useRecordComponentView`.

## Analytics Constants

All analytics event names are defined in `trendsLogging.ts`:

```typescript
// Main page views
export const TRENDS_TRAFFIC_AND_COST_PAGE_VIEW = 'mlflow.traces.trends.traffic_and_cost_page_view';

// Individual card views
export const TRENDS_VOLUME_CARD_VIEW = 'mlflow.traces.trends.volume_card_view';
export const TRENDS_LATENCY_CARD_VIEW = 'mlflow.traces.trends.latency_card_view';
export const TRENDS_ERROR_RATE_CARD_VIEW = 'mlflow.traces.trends.error_rate_card_view';

// Future page views (when implemented)
export const TRENDS_QUALITY_METRICS_PAGE_VIEW = 'mlflow.traces.trends.quality_metrics_page_view';
export const TRENDS_TOOLS_PAGE_VIEW = 'mlflow.traces.trends.tools_page_view';
export const TRENDS_TOPICS_PAGE_VIEW = 'mlflow.traces.trends.topics_page_view';

// Modal views
export const TRENDS_TRACE_EXPLORER_MODAL_VIEW = 'mlflow.traces.trends.trace_explorer_modal_view';
export const TRENDS_CORRELATION_MODAL_VIEW = 'mlflow.traces.trends.correlation_modal_view';
```

## Implementation Pattern

Each component follows this pattern:

1. **Import the hook and constants:**
   ```typescript
   import { useRecordComponentView } from '@databricks/web-shared/observability';
   import { TRENDS_[COMPONENT]_VIEW } from '../../constants/trendsLogging';
   ```

2. **Create the ref in the component:**
   ```typescript
   const { elementRef: componentViewRef } = useRecordComponentView<HTMLDivElement>('div', TRENDS_[COMPONENT]_VIEW);
   ```

3. **Attach the ref to the root element:**
   ```typescript
   return (
     <div ref={componentViewRef}>
       {/* component content */}
     </div>
   );
   ```

## Tracked Components

### Main Pages
- **TrendsPageTrafficAndCost**: Tracks overall traffic and cost page views
  - Ref: `trafficAndCostViewRef`
  - Event: `mlflow.traces.trends.traffic_and_cost_page_view`

### Individual Cards
- **TrendsVolumeCard**: Tracks volume card interactions
  - Ref: `volumeCardViewRef`
  - Event: `mlflow.traces.trends.volume_card_view`

- **TrendsLatencyCard**: Tracks latency card interactions
  - Ref: `latencyCardViewRef`
  - Event: `mlflow.traces.trends.latency_card_view`

- **TrendsErrorRateCard**: Tracks error rate card interactions
  - Ref: `errorRateCardViewRef`
  - Event: `mlflow.traces.trends.error_rate_card_view`

## Purpose

This analytics implementation allows the MLflow team to:

1. **Track Feature Adoption**: Understand how often users visit trends pages
2. **Measure Engagement**: See which cards/metrics users interact with most
3. **Identify Usage Patterns**: Analyze user behavior across different trend analytics
4. **Guide Product Decisions**: Make data-driven decisions about future improvements

## Future Expansion

When implementing additional trends pages (quality metrics, tools, topics), follow the same pattern:

1. Add constants to `trendsLogging.ts`
2. Import and use `useRecordComponentView` in the component
3. Add the ref to the root element

This consistent approach ensures comprehensive analytics coverage across the entire trends feature.