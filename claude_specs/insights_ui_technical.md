# MLflow Insights UI - Technical Specification

## Executive Summary

This document defines the technical implementation details for the MLflow Insights UI. It covers the frontend architecture, API integration patterns, component structure, and implementation guidelines for building the analytics platform.

**Related Documentation:**
- **For product requirements and UI specifications, see:** `insights_ui_prd.md`
- **For REST API specifications, see:** `insights_rest_api.md`

## Testing Database

**Test Database Path**: `/Users/nikhil.thorat/Code/mlflow-agent/mlflow_data/mlflow.db`

Use this database when testing and verifying functionality.

## Technical Implementation

### Frontend Architecture Philosophy

1. **React Query for ALL Data Fetching**: MUST use React Query for all API calls - no direct fetch calls, no useEffect for data fetching
2. **High-Resolution Functional Naming**: Name hooks/endpoints/components after the exact data they handle (e.g., `useErrorRateOverTime`, `useToolDiscovery`, `useAssessmentFailureRate`) - NEVER generic names like `useInsights` or `getData`
3. **1:1 Mapping Principle**: Each API endpoint → one React Query hook → one component
4. **Strict Component Reuse**: 
   - MUST check existing codebase for similar components before creating new ones
   - MUST use existing design system components from `@databricks/design-system`
   - MUST follow existing patterns in `trends/` and other established features
   - NEVER add new dependencies if existing ones can solve the problem
   - NEVER create custom UI components if they already exist in the codebase
5. **Incremental Testing**: Test each component in isolation before integration
6. **Derived State Over Effects**: Always use React Query derived state; avoid useEffect unless absolutely necessary
7. **No Unnecessary Re-renders**: Leverage React Query's built-in caching and memoization
8. **Exact TypeScript Interfaces**: For ALL backend response models, MUST have corresponding TypeScript interfaces that exactly mirror the field names and structure - no exceptions

### 🚨 CRITICAL: TypeScript Interface Requirements

**MANDATORY REQUIREMENT**: For ALL backend response models, MUST have corresponding TypeScript interfaces that exactly mirror the field names and structure - no exceptions.

#### TypeScript Type Structure

All backend Pydantic models MUST have exact TypeScript equivalents:

- **Field Names**: Exactly match backend field names (no camelCase conversion)
- **Field Types**: Exactly match backend types (string → string, int → number, List[X] → X[], etc.)
- **Nested Objects**: All nested Pydantic models must have corresponding TypeScript interfaces
- **Location**: All types live in `types/insights.ts` within the insights folder

#### Type Organization

```typescript
// types/insights.ts - MUST mirror all backend Pydantic models exactly

// Response models
export interface VolumeResponse {
  summary: VolumeSummary;
  time_series: VolumeTimeSeries[];
}

export interface VolumeSummary {
  count: number;
  ok_count: number;
  error_count: number;
}

export interface VolumeTimeSeries {
  time_bucket: number;
  count: number;
  ok_count: number;
  error_count: number;
}

// Dimension models
export interface Dimension {
  name: string;
  display_name: string;
  description: string;
  parameters: DimensionParameter[];
}

export interface DimensionParameter {
  name: string;
  type: string;
  required: boolean;
  description?: string;
  enum_values?: string[];
}

// ... etc for ALL backend models
```

### 🚨 CRITICAL: React Query is MANDATORY

**MANDATORY REQUIREMENT**: ALL data fetching MUST use React Query. This is NON-NEGOTIABLE.

#### Why React Query is Required

1. **NO Direct Fetch Calls**: Never use fetch() directly in components
2. **NO useEffect for Data**: Never use useEffect to fetch data
3. **Automatic Caching**: React Query handles all caching automatically
4. **Background Refetching**: Keeps data fresh without manual intervention
5. **Loading/Error States**: Built-in handling for all async states
6. **Optimistic Updates**: Support for immediate UI feedback
7. **Request Deduplication**: Prevents redundant API calls

#### React Query Pattern (MUST FOLLOW)

```typescript
// ✅ CORRECT - Using React Query with functional naming
export const useVolumeOverTime = (experimentIds, startTime, endTime) => {
  return useQuery({
    queryKey: ['volume-over-time', experimentIds, startTime, endTime],
    queryFn: () => fetchVolumeOverTime({ experimentIds, startTime, endTime }),
    staleTime: 30000,
    cacheTime: 300000,
  });
};

// ❌ WRONG - Direct fetch in component
const fetchData = async () => {
  const response = await fetch('/api/3.0/mlflow/traces/insights/volume-over-time');
  setData(await response.json());
};

// ❌ WRONG - useEffect for data fetching
useEffect(() => {
  fetchVolumeData();
}, []);
```

### Correlation Implementation Requirements

**Frontend Requirements**:
- MUST include correlation section in EVERY card component
- MUST use consistent correlation component across all cards
- MUST update correlations when filters change
- MUST show loading state during correlation computation
- MUST handle API errors gracefully with retry logic

**For complete REST API specifications, see:** `insights_rest_api.md`

### Frontend Implementation

#### Directory Structure

```
mlflow/server/js/src/experiment-tracking/components/insights/
├── hooks/
│   ├── useVolumeOverTime.ts
│   ├── useLatencyPercentiles.ts
│   ├── useErrorRateOverTime.ts
│   ├── useAssessmentAnalysis.ts
│   ├── useToolDiscovery.ts
│   └── useTagDistribution.ts
├── components/
│   ├── InsightsPage.tsx           # Main container
│   ├── TrafficInsights.tsx        # Traffic dashboard
│   ├── QualityInsights.tsx        # Quality metrics
│   ├── ToolInsights.tsx          # Tool analytics
│   ├── TagInsights.tsx           # Tag analytics
│   └── cards/
│       ├── VolumeCard.tsx
│       ├── LatencyCard.tsx
│       ├── ErrorRateCard.tsx
│       └── BaseInsightCard.tsx
├── types/
│   └── insights.ts               # ALL backend Pydantic models as TypeScript interfaces
├── utils/
│   ├── api.ts
│   └── formatters.ts
└── index.tsx
```

**CRITICAL**: The `types/insights.ts` file MUST contain TypeScript interfaces for EVERY backend Pydantic model with exact field name and type matching.

### Complete Type Coverage Requirement

**MANDATORY**: You MUST follow the REST API specification in `insights_rest_api.md` exactly. Create TypeScript interfaces for EVERY SINGLE response model, request model, and nested object that appears in the REST API. No exceptions.

This includes:
- All traffic response models (VolumeResponse, LatencyResponse, ErrorResponse)
- All assessment response models (AssessmentDiscoveryResponse, AssessmentMetricsResponse) 
- All tool response models (ToolDiscoveryResponse, ToolMetricsResponse)
- All tag response models (TagDiscoveryResponse, TagMetricsResponse)
- All dimension models (Dimension, DimensionParameter, DimensionValue)
- All correlation models (CorrelationsResponse, NPMICalculationResponse)
- Every nested object within these responses

**Location**: ALL types live in the shared `types/insights.ts` file - no scattered type definitions.

## 🚨 CRITICAL: UI Testing Requirement

**MANDATORY REQUIREMENT**: Whenever you change the UI, you MUST always open the UI with Playwright to check that you actually did what you meant to do. This is EXTREMELY important - anytime you touch the UI, you MUST test it.

### UI Testing Protocol
1. **After ANY UI change**: Immediately test with Playwright
2. **Verify against PRD**: Always check that the UI stays faithful to the PRD specifications
3. **Visual verification**: Ensure components match the PRD layout and design
4. **Functional testing**: Verify data loads correctly and interactions work
5. **Cross-check PRD**: Compare the running UI against `insights_ui_prd.md` requirements

### Testing Steps
```bash
# ALWAYS use dev/run-server-dev for testing
# Start MLflow server with insights (port 5000 for API, port 3000 for MCP Playwright)

# Use Playwright MCP on port 3000 to navigate to insights page
# Open browser to http://localhost:5000/experiments/{experiment_id}/insights

# Verify against PRD:
# - Check navigation structure matches PRD
# - Verify card layouts match PRD specifications  
# - Ensure correlations appear on EVERY card
# - Test time range selector functionality
# - Validate chart types and data display
```

**NO EXCEPTIONS**: Every UI change must be tested immediately against the PRD requirements.

#### React Hook Pattern

```typescript
// hooks/useVolumeOverTime.ts
export const useVolumeOverTime = (
  experimentIds: string[],
  startTime: number,
  endTime: number,
  timeBucket: 'hour' | 'day' | 'week' = 'hour'
) => {
  return useQuery({
    queryKey: ['insights', 'volume-over-time', experimentIds, startTime, endTime, timeBucket],
    queryFn: () => fetchVolumeOverTime({
      experiment_ids: experimentIds,
      start_time: startTime,
      end_time: endTime,
      time_bucket: timeBucket
    }),
    staleTime: 30000,  // 30 seconds
    refetchInterval: 60000  // 1 minute
  });
};
```

#### Component Structure

```tsx
// components/TrafficInsights.tsx
export const TrafficInsights = ({ experimentIds, timeRange }) => {
  const volumeQuery = useVolumeOverTime(experimentIds, timeRange.start, timeRange.end);
  const latencyQuery = useLatencyPercentiles(experimentIds, timeRange.start, timeRange.end);
  const errorQuery = useErrorRateOverTime(experimentIds, timeRange.start, timeRange.end);

  return (
    <div className="insights-grid">
      <VolumeCard data={volumeQuery.data} loading={volumeQuery.isLoading} />
      <LatencyCard data={latencyQuery.data} loading={latencyQuery.isLoading} />
      <ErrorRateCard data={errorQuery.data} loading={errorQuery.isLoading} />
    </div>
  );
};
```

### API Integration Pattern

#### Fetch Wrapper Utility (ONLY for React Query)

```typescript
// utils/api.ts
// NOTE: This function is ONLY used inside React Query hooks, NEVER called directly in components
export const fetchInsightsData = async <T>(
  endpoint: string,
  payload: Record<string, any>
): Promise<T> => {
  const response = await fetch(`/api/3.0/mlflow/traces/insights/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }
  
  return response.json();
};

// ✅ CORRECT USAGE - Inside React Query hook with functional naming
export const useVolumeOverTime = (experimentIds, startTime, endTime) => {
  return useQuery({
    queryKey: ['volume-over-time', experimentIds, startTime, endTime],
    queryFn: () => fetchInsightsData('volume-over-time', { 
      experiment_ids: experimentIds, 
      start_time: startTime, 
      end_time: endTime 
    }), // Used within React Query
  });
};

// ❌ WRONG USAGE - Direct call in component
const MyComponent = () => {
  // NEVER DO THIS
  const data = await fetchInsightsData('volume-over-time', params);
};
```

#### Performance Optimizations

- React Query for automatic caching and background refetching
- Debounced API calls for user interactions
- Optimistic UI updates where appropriate
- Lazy loading for large datasets

### Implementation Phases

#### Phase 1: Core Traffic Analytics (Weeks 1-2)

- [ ] Create frontend insights directory structure
- [ ] Implement API integration hooks
- [ ] Create TrafficInsights component
- [ ] Add time range selector
- [ ] Implement volume, latency, and error charts
- [ ] Add correlation components

**Deliverable**: Working traffic dashboard with volume, latency, and error metrics

#### Phase 2: Tool & Assessment Analytics (Weeks 3-4)

- [ ] Build ToolInsights component with discovery charts
- [ ] Add QualityInsights component with assessment cards
- [ ] Implement tool performance visualizations
- [ ] Add assessment type detection UI
- [ ] Create drill-down navigation
- [ ] Integrate correlations for each card

**Deliverable**: Complete tool discovery and quality assessment analytics

#### Phase 3: Advanced Features (Weeks 5-6)

- [ ] Build TagInsights component with distribution charts
- [ ] Add tag value visualization with horizontal bars
- [ ] Implement interactive tag selection
- [ ] Enhance correlation visualizations
- [ ] Add advanced filtering UI
- [ ] Create custom view builder

**Deliverable**: Tag analytics and correlation analysis features

#### Phase 4: Polish & Performance (Weeks 7-8)

- [ ] Add comprehensive error handling with retry logic
- [ ] Implement React Query caching strategies
- [ ] Optimize component rendering performance
- [ ] Add loading skeletons for all cards
- [ ] Write component tests with React Testing Library
- [ ] Performance profiling with React DevTools
- [ ] Documentation and code cleanup

**Deliverable**: Production-ready insights platform

### Testing Strategy

#### Unit Tests

- Test React components with mock API responses
- Verify hook behavior with React Testing Library
- Test error handling and retry logic
- Validate chart rendering with mock data

#### Integration Tests

- End-to-end UI testing with Cypress
- API integration tests with real endpoints
- Component interaction tests
- Data visualization accuracy validation

#### Manual Testing Checklist

- [ ] Verify all charts render correctly
- [ ] Test time range selection
- [ ] Validate experiment filtering
- [ ] Check error states
- [ ] Test with large datasets
- [ ] Verify auto-refresh functionality

### Success Metrics

#### Technical Metrics

- API response time < 500ms for standard requests
- Frontend initial load time < 2 seconds
- Zero critical bugs in production
- 90% code coverage for React components

#### User Metrics

- 80% of ML engineers use insights weekly
- 50% reduction in time to identify trace issues
- 90% user satisfaction score
- 30% reduction in debugging time

### Migration Strategy

1. **Parallel Development**: Build alongside existing trends/ implementation
2. **Feature Flag**: Enable insights via environment variable
3. **Gradual Rollout**: Start with select experiments/teams
4. **Data Validation**: Compare results with existing implementation
5. **Full Migration**: Switch all users after validation period

### Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Performance issues with large datasets | Implement pagination and caching |
| Complex component state management | Use React Query for server state |
| Frontend bundle size increase | Code splitting and lazy loading |
| Browser compatibility | Test across major browsers |
| User adoption | Provide migration guides and training |

### Frontend Dependencies

- React >= 18.0
- TypeScript >= 5.0
- @tanstack/react-query >= 5.0
- @databricks/design-system (existing)
- D3.js (for advanced visualizations)

### Appendix: Existing Frontend Infrastructure

Based on codebase analysis, the following infrastructure already exists:

- `insights/` directory with basic component structure
- Navigation and routing configured
- Design system components available
- Chart components from trends/ can be reused

This existing infrastructure accelerates development and ensures consistency with MLflow patterns.

## Related Documentation

**For product requirements and UI specifications, see:** `insights_ui_prd.md`

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Status**: Ready for Implementation