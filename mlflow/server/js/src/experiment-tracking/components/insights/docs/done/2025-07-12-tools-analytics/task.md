# Add the tools trends page

**Status:** Done
**Completed:** 2025-07-12
**Commit:** 31903b6ff4915

## Description
Implemented comprehensive Tools Analytics feature for MLflow Traces v3, providing operational insights into tool usage, performance metrics, and correlations within trace data through time-series visualization and statistical analysis.

## Implementation
- **SQL-based Tool Discovery**: Automatic extraction and analysis of tools used in trace spans with regex-based name normalization
- **Tool Performance Metrics**: Volume tracking (traces and invocations), latency percentiles (P50/P90/P99), and error rate monitoring per tool
- **Time-Series Analysis**: Dynamic time bucketing (hour/day/week) based on selected time ranges
- **Individual Tool Cards**: Three-column layout with separate sections for Volume, Latency, and Errors
- **Tool Overview Dashboard**: Modular card architecture with aggregated metrics across all tools
- **SQL Dimensions System**: Unified framework for generating SQL filter expressions across all analytics
- **Advanced Data Processing**: NPMI correlation analysis, data transformation pipeline, responsive chart components

## Key Features
- **Tools Discovery & Analytics System**: Automatic tool extraction with regex-based normalization
- **Individual Tool Cards**: Volume, latency, and error analysis per tool
- **Tool Overview Dashboard**: High-level summary statistics and top tools visualization
- **SQL Dimensions Framework**: Centralized system for multi-dimensional analysis
- **NPMI Correlation Analysis**: Statistical correlation detection between tools and trace metadata

## Files Changed
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/Tools.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/QualityMetrics.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/components/TrendsToolCard.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/components/TrendsCategoricalBarChart.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/components/TrendsLatencyPercentileSelector.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/pages/tools/TrendsToolErrorCard.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/pages/tools/TrendsToolLatencyCard.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/pages/tools/TrendsToolOverviewCard.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/pages/tools/TrendsToolVolumeCard.tsx`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/constants/sqlDimensions.ts`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/hooks/useToolDiscoveryQueries.ts`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/hooks/useToolSpecificCorrelations.ts`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/hooks/useAssessmentInfos.ts`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/hooks/useAssessmentQualityQueries.ts`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/hooks/useNpmiQueries.ts`
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends/constants/trendsLogging.ts`

## Testing
- SQL query validation using execute_databricks_sql.py script against real trace data
- Unit tests for data transformation and time processing utilities
- Integration testing with production-like data from e2-dogfood workspace
- Component testing for proper data handling and error states
- Performance testing with large trace datasets

## Notes
This implementation established the SQL dimensions framework that serves as the foundation for all analytics pages. The tool discovery system with regex normalization handles MLflow's numeric suffix patterns effectively. The modular architecture (TrendsSliceCard, categorical charts, etc.) was designed for reuse across other analytics pages.