# MLflow Traces Trends - Todo List

## High Priority

### Complete Quality Metrics Implementation
- Quality Metrics page is currently partially implemented
- Need to complete assessment analytics with full support for all assessment types
- Should reuse existing TrendsSliceCard and chart components
- Add boolean dtype support

### Implement Topics Analysis Feature
- Topics page is currently just a placeholder component
- Need to implement topic discovery and analysis over time
- Should follow existing Tools and Traffic & Cost patterns
- Requires research into topic extraction from trace data

### Performance Optimization
- Optimize SQL queries for large datasets
- Add query caching strategies where appropriate
- Ensure all queries perform well with 100k+ traces
- Test time bucketing performance with different time ranges

## Medium Priority

### Complete Create View Feature
- Create View page is currently just a placeholder
- Need to implement custom dashboard/view creation functionality
- Should allow users to create custom combinations of analytics
- Requires understanding of all other features first

### Enhanced Testing Coverage
- Add comprehensive unit tests for all utility functions
- Add integration tests for SQL queries using execute_databricks_sql.py
- Add visual regression tests for chart components
- Test cross-browser compatibility with dev.local

### ✅ Clean Up Console Logs, Spam, Errors, and Warnings - COMPLETED
- ✅ Fixed React.forwardRef() warnings in GenAI traces table components by restructuring conditional rendering
- ✅ Fixed duplicate React keys warning in TabSelectorBar by using unique keys for tab components
- ✅ Removed unnecessary div wrappers that were incorrectly added to other Tooltip components
- ✅ Dramatically reduced console noise from 54,000+ tokens to manageable levels
- ✅ Successfully enabled Playwright MCP to read console output properly for UI testing
- ✅ Comprehensive documentation created in docs/work/2025-07-14-console-cleanup/
- ✅ Completed PR: Fix React warnings and console errors to enable Playwright MCP

### Documentation Updates
- Update trends/CLAUDE.md with new patterns discovered during development
- Add component usage guidelines for future development
- Document SQL query patterns and performance considerations
- Create troubleshooting guide for common development issues

## Low Priority


### Chart Component Enhancements
- Add more chart types if needed (scatter plots, heatmaps)
- Improve chart accessibility and keyboard navigation
- Add chart export functionality
- Optimize chart rendering performance for large datasets

### UI/UX Improvements
- Add loading skeletons for better perceived performance
- Improve error states and empty states
- Add tooltips and help text for complex features
- Implement responsive design for mobile/tablet viewing

### Analytics and Monitoring
- Add more detailed component tracking to trendsLogging.ts
- Implement performance monitoring for slow queries
- Add user behavior analytics for feature adoption
- Create dashboards for monitoring trends feature usage