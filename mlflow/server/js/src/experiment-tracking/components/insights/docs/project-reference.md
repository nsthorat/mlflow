# MLflow Traces Trends Analytics - Technical Reference

## Detailed Project Structure

```
src/trends/
├── components/          # Reusable UI components
│   ├── TrendsSliceCard.tsx       # Main card layout component
│   ├── TrendsCardTitle.tsx       # Consistent title styling
│   ├── TrendsLineChart.tsx       # Time-series line charts
│   ├── TrendsCategoricalBarChart.tsx  # Bar charts for categorical data
│   └── TrendsCorrelationMatrix.tsx    # NPMI correlation display
├── pages/               # Feature-specific analytics pages
│   ├── traffic-and-cost/        # Volume, latency, error analytics
│   ├── tools/                   # Tool usage and performance
│   ├── quality-metrics/         # Assessment results and trends
│   ├── topics/                  # Topic analysis (placeholder)
│   └── user-feedback/           # User feedback analytics (planned)
├── hooks/               # Custom React hooks & SQL queries
│   ├── useTrafficAndCostQueries.ts    # Traffic/performance data
│   ├── useToolDiscoveryQueries.ts     # Tool usage patterns
│   ├── useQualityMetricsQueries.ts    # Assessment data
│   └── sql/                           # SQL query definitions
├── utils/               # Data processing utilities
│   ├── dataProcessing.ts        # Time-series aggregation
│   ├── correlationAnalysis.ts   # NPMI calculations
│   └── chartHelpers.ts          # Chart data formatting
├── constants/           # Configuration and constants
│   ├── chartConfig.ts           # Chart dimensions, colors, offsets
│   ├── percentileColors.ts      # Color schemes for percentiles
│   ├── trendsLogging.ts         # Analytics component tracking
│   └── cardStyles.ts            # Reusable styling constants
├── types/               # TypeScript definitions
│   ├── trendsTypes.ts           # Core data types
│   ├── chartTypes.ts            # Chart-specific types
│   └── apiTypes.ts              # API response types
└── docs/                # Documentation and workflow
    ├── todos.md                 # Active todo list
    ├── workflow-core.md         # Core workflow process
    ├── workflow-troubleshooting.md  # Issue resolution
    ├── project-description.md   # Project overview
    ├── USER-GUIDE.md           # User interaction guide
    ├── work/                   # Active work folders
    └── done/                   # Completed tasks
```

## Test Data Environment

### Databricks Configuration
- **Workspace**: e2-dogfood (dogfood workspace)
- **SQL Warehouse ID**: `dd43ee29fedd958d`
- **Test Table**: `ml.2025_03_12_external_agent_monitoring.trace_logs_996116264211929`

### Table Schema Details
```sql
trace_id (string)                    -- Unique identifier for the trace
client_request_id (string)           -- Client request identifier
request_time (timestamp)             -- When the request was made
state (string)                       -- State of the trace (e.g., 'OK', 'ERROR')
execution_duration_ms (bigint)       -- Duration of execution in milliseconds
request (string)                     -- Request data
response (string)                    -- Response data
trace_metadata (map<string,string>)  -- Metadata for the trace
tags (map<string,string>)           -- Tags associated with the trace
trace_location (struct)              -- Location information for the trace
assessments (array<struct>)          -- Array of assessment results:
  ├── name (string)                  -- Assessment name
  └── feedback (struct)              -- Feedback structure:
      ├── value (string)             -- Assessment value
      └── error (struct)             -- Error information
spans (array<struct>)                -- Array of span data
```

## Development Test URLs

### Simple Data Environment (Recommended for Development)
- **URL**: https://dev.local:22090/ml/experiments/996116264211929/traces?o=6051921418418893&startTimeLabel=CUSTOM&viewState=logs&sqlWarehouseId=133a3448445430ad&conf_enable=databricks.fe.mlflow.enableTraceInsights&startTime=2025-06-10T19%3A33%3A49.061Z&endTime=2025-07-10T19%3A33%3A49.061Z&tracesNavigation=traffic-cost
- **Features**: Includes assessments, faster loading, good for testing basic functionality

### Complex Data Environment (Full Feature Testing)
- **URL**: https://dev.local:22090/ml/experiments/2665190525370131/traces?o=6051921418418893&startTimeLabel=LAST_7_DAYS&viewState=logs&sqlWarehouseId=133a3448445430ad&conf_enable=databricks.fe.mlflow.enableTraceInsights&tracesNavigation=traffic-cost&startTime=2025-06-10T19%3A33%3A49.061Z&endTime=2025-07-10T19%3A33%3A49.061Z
- **Features**: More complex data, slower loading, comprehensive feature testing

## Analytics Framework

### Correlation Analysis
- **Method**: Normalized Pointwise Mutual Information (NPMI)
- **Implementation**: `utils/correlationAnalysis.ts`
- **Visualization**: `TrendsCorrelationMatrix.tsx`

### Time-Series Processing
- **Bucketing**: Hour, day, week, month aggregations
- **Implementation**: `utils/dataProcessing.ts`
- **Chart Types**: Line charts for continuous metrics, bar charts for categorical data

### Component Tracking
- **File**: `constants/trendsLogging.ts` (NOT componentIds.ts)
- **Pattern**: `TRENDS_[COMPONENT]_[ACTION]` (e.g., `TRENDS_LATENCY_CARD_VIEW`)
- **Implementation**: `useRecordComponentView` hook in each component

## Design System Integration

### Theme Usage Patterns
```typescript
import { useDesignSystemTheme } from '@databricks/design-system';

const theme = useDesignSystemTheme();

// Spacing (never use pixels directly)
padding: theme.spacing.sm    // 8px
margin: theme.spacing.md     // 16px
gap: theme.spacing.lg        // 24px

// Colors
color: theme.colors.textPrimary
backgroundColor: theme.colors.backgroundPrimary

// Typography
fontSize: theme.typography.fontSizeSm
fontWeight: theme.typography.fontWeightBold
```

### Available Design System Components
Reference: https://ui-infra.dev.databricks.com/storybook/js/packages/du-bois/index.html

Common components used in trends:
- `Card` - Base card layouts
- `Button` - Interactive elements
- `Select` - Dropdown selections
- `Tooltip` - Contextual information
- `Skeleton` - Loading states
- `Grid` and `Flex` - Layout systems