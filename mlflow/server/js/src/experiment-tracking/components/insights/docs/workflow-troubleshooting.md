# Todo Workflow System - Troubleshooting

Common issues and solutions for the todo workflow system.

## Dev Server Issues

### Server Crashes
**Symptoms**: Dev server stops responding, port errors, build failures

**Solutions**:
1. Check status: `ps aux | grep "yarn start --projects mlflow" | grep -v grep`
2. Kill process: `pkill -f "yarn start --projects mlflow"`
3. Check logs: `tail -f /tmp/mlflow_dev_server.log`
4. Restart: `nohup yarn start --projects mlflow > /tmp/mlflow_dev_server.log 2>&1 &`
5. Wait for: "dev-proxy for monolith,url-proxy started at [URL] 🚀"

## Authentication Issues

### Playwright Authentication
**Symptoms**: Login screen appears, authentication failures

**Solutions**:
1. Login in Chrome: `open https://dev.local:22090/?o=6051921418418893`
2. Complete login/signup in browser
3. Refresh setup: `yarn playwright-jsessionid-cookie refresh` (from mlflow/web/js)
4. Restart Claude Code
5. Verify with simple Playwright navigation

## Code Quality Issues

### Theme/Styling Problems
**Symptoms**: Hardcoded pixels, inconsistent spacing, missing theme imports

**Solutions**:
1. Check hardcoded values: `grep -r "px\|rem\|em" src/trends/ --include="*.tsx" --include="*.ts" | grep -v node_modules`
2. Use theme values: Replace with `theme.spacing.sm/md/lg`
3. Import theme: `import { useDesignSystemTheme } from '@databricks/design-system'`
4. Common patterns:
   - Spacing: `theme.spacing.sm` (8px), `theme.spacing.md` (16px), `theme.spacing.lg` (24px)
   - Colors: `theme.colors.textPrimary`, `theme.colors.textSecondary`
   - Typography: `theme.typography.fontSizeSm`, `theme.typography.fontSizeBase`

### Analytics Tracking Issues
**Symptoms**: Missing component tracking, incorrect componentIds

**Solutions**:
1. Add componentIds to `trendsLogging.ts` (not componentIds.ts)
2. Use hierarchical naming: `TRENDS_[COMPONENT]_[ACTION]`
3. Import from `../constants/trendsLogging`
4. Verify useRecordComponentView usage in components

## SQL and Data Issues

### Query Validation Problems
**Symptoms**: SQL errors, performance issues, incorrect results

**Solutions**:
1. Use `execute_databricks_sql.py` during planning phase
2. Test against real data before implementation
3. Check table schema matches expectations
4. Verify SQL warehouse connectivity

### Test Data Access
**Test Environment**:
- Workspace: e2-dogfood
- SQL Warehouse: `dd43ee29fedd958d`
- Table: `ml.2025_03_12_external_agent_monitoring.trace_logs_996116264211929`

## Orphaned Task Recovery

### Resume Orphaned Task
1. Get task name from orphaned list
2. Read task.md, check Status field
3. Update Agent PID: `echo $PPID`
4. Continue from appropriate phase based on status

### Reset Orphaned Task
1. Read `docs/work/[task-name]/task.md`
2. Add content back to `docs/todos.md`
3. Delete `docs/work/[task-name]/`
4. Continue to Phase 1

## Component Development Issues

### Missing Design System Components
**Symptoms**: Unknown component names, import errors

**Solutions**:
1. Check `js/packages/du-bois/src/primitives`
2. View docs: `https://ui-infra.dev.databricks.com/storybook/js/packages/du-bois/index.html?path=/docs/primitives-<component-name>--docs`
3. Look for similar patterns in existing trends components
4. Ask user for clarification on component requirements

### Component Reuse Problems
**Symptoms**: Duplicating existing functionality

**Solutions**:
1. Check `trends/components/` before creating new components
2. Review existing page layouts: `trends/pages/traffic-and-cost/`, `trends/pages/tools/`
3. Follow data hook patterns: `useTrafficAndCostQueries`, `useToolDiscoveryQueries`
4. Use `TrendsSliceCard` architecture for consistency