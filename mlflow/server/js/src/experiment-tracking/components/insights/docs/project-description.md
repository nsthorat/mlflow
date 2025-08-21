# MLflow Traces Trends Analytics

Time-series analytics and correlation analysis platform for MLflow traces using dimensions-based data slicing.

## Core Concept: Dimensions
Data slicing system that enables users to filter traces by criteria (errors, tools, assessments) and analyze correlations between different data cuts to discover patterns.

## Current Status

### Phase 1: Hard-coded Analytics (In Progress)
- ✅ **Traffic & Cost**: Volume, latency, error rate analytics
- ✅ **Tools**: Discovery, usage, performance analysis  
- ✅ **NPMI Correlations**: Pre-defined dimension analysis
- ⚠️ **Quality Metrics**: Assessment analytics (partially implemented)
- ❌ **User Feedback**: Satisfaction and sentiment analysis
- ❌ **Tags**: Tag-based exploration and trends
- ❌ **Topics**: Content and topic discovery

### Future Phases
- **Phase 2**: User-defined dimensions with natural language SQL generation
- **Phase 3**: LLM-powered automatic insights and pattern recognition

## Commands
- **Test**: `yarn test`
- **Type Check**: `yarn type-check` 
- **Lint**: `yarn lint:fix`
- **Format**: `yarn prettier:fix`
- **Fix All**: `yarn fix-all`
- **Dev Server**: `nohup yarn start --projects mlflow > /tmp/mlflow_dev_server.log 2>&1 &` (from universe root)

## Key Patterns
- **Component Reuse**: Check trends/components/ before creating new components
- **SQL Validation**: Use execute_databricks_sql.py during planning
- **Theme Usage**: Use theme.spacing/colors (no hardcoded pixels)
- **Analytics**: Add componentIds to trendsLogging.ts
- **Card Architecture**: Use TrendsSliceCard for consistent layouts

## Documentation
- **workflow-core.md**: Core todo workflow (Phase 0-4)
- **workflow-troubleshooting.md**: Issue resolution guide
- **project-reference.md**: Detailed technical reference
- **USER-GUIDE.md**: User interaction patterns

