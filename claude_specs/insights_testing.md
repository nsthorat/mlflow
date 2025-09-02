# MLflow Insights - Testing Guide

## Setup Servers

### OSS Version Testing
```bash
# Start dev server (runs on ports 3000 for UI and 5000 for backend)
MLFLOW_TRACKING_URI=/Users/nikhil.thorat/Code/mlflow-agent/mlflow_data/mlflow.db \
nohup uv run bash dev/run-dev-server.sh > /tmp/mlflow-dev-server.log 2>&1 &

# Monitor logs
tail -f /tmp/mlflow-dev-server.log
```

### Databricks Version Testing

**IMPORTANT**: Databricks credentials should be stored in `.env` file for security:
```bash
# First, check if .env file exists and load credentials
if [ -f .env ]; then
    source .env
    echo "Loaded DATABRICKS_HOST and DATABRICKS_TOKEN from .env"
fi

# The dev/run-dev-server-databricks.sh script will automatically use these environment variables
# Start Databricks dev server (runs on ports 3001 for UI and 5001 for backend)
nohup uv run bash dev/run-dev-server-databricks.sh > /tmp/mlflow-databricks-server.log 2>&1 &

# Monitor logs
tail -f /tmp/mlflow-databricks-server.log
```

**`.env` file format**:
```bash
DATABRICKS_HOST=https://your-databricks-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-databricks-token
```

## REST Testing

### OSS Server (port 5000)
```bash
# Test volume endpoint
curl -X POST http://localhost:5000/ajax-api/2.0/mlflow/traces/insights/traffic-cost/volume \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["1"], "time_bucket": "hour"}'

# Test latency endpoint
curl -X POST http://localhost:5000/ajax-api/2.0/mlflow/traces/insights/traffic-cost/latency \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["1"], "time_bucket": "hour"}'

# Test errors endpoint
curl -X POST http://localhost:5000/ajax-api/2.0/mlflow/traces/insights/traffic-cost/errors \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["1"], "time_bucket": "hour"}'

# Test assessments discovery
curl -X POST http://localhost:5000/ajax-api/2.0/mlflow/traces/insights/quality/assessments/discovery \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["1"]}'

# Test tools discovery
curl -X POST http://localhost:5000/ajax-api/2.0/mlflow/traces/insights/tools/discovery \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["1"]}'

# Test tags discovery
curl -X POST http://localhost:5000/ajax-api/2.0/mlflow/traces/insights/tags/discovery \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["1"]}'
```

### Databricks Server (port 5001)

**Debugging SQL Queries**: When debugging Databricks SQL queries, use the script in `claude_scripts/query_databricks.py` to query the `rag.nst.trace_logs_2178582188830602` table directly. This helps debug and test SQL queries before implementing them in the store.

```bash
# Example: Query the trace logs table directly
python claude_scripts/query_databricks.py "SELECT COUNT(*) FROM rag.nst.trace_logs_2178582188830602"
```

### Databricks Server (port 5001)
```bash
# Test volume endpoint
curl -X POST http://localhost:5001/ajax-api/2.0/mlflow/traces/insights/traffic-cost/volume \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["2178582188830602"], "time_bucket": "hour"}'

# Test latency endpoint
curl -X POST http://localhost:5001/ajax-api/2.0/mlflow/traces/insights/traffic-cost/latency \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["2178582188830602"], "time_bucket": "hour"}'

# Test errors endpoint
curl -X POST http://localhost:5001/ajax-api/2.0/mlflow/traces/insights/traffic-cost/errors \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["2178582188830602"], "time_bucket": "hour"}'

# Test assessments discovery
curl -X POST http://localhost:5001/ajax-api/2.0/mlflow/traces/insights/quality/assessments/discovery \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["2178582188830602"]}'

# Test tools discovery
curl -X POST http://localhost:5001/ajax-api/2.0/mlflow/traces/insights/tools/discovery \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["2178582188830602"]}'

# Test tags discovery
curl -X POST http://localhost:5001/ajax-api/2.0/mlflow/traces/insights/tags/discovery \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["2178582188830602"]}'
```

## TypeScript Compilation & Linting Check

**IMPORTANT**: Whenever making TypeScript/JavaScript changes, always run these checks to ensure no errors were introduced:

```bash
# Run TypeScript compiler to check for type errors
yarn --cwd mlflow/server/js type-check

# Run ESLint to check for code quality issues
yarn --cwd mlflow/server/js lint

# If errors are found, fix them before proceeding with UI testing
```

## UI Testing

**Note**: Playwright MCP must be available. If Playwright MCP is not available, ask the user to restart it and stop.

### OSS UI Testing (port 3000)
```javascript
// Navigate to insights page
mcp__playwright__browser_navigate({url: "http://localhost:3000/experiments/1/insights"})

// Take snapshot of the page
mcp__playwright__browser_snapshot()
// Check for issues: empty charts, missing data, loading errors

// Test Traffic & Cost tab
mcp__playwright__browser_click({element: "Traffic & Cost tab", ref: "[data-testid='traffic-cost-tab']"})
mcp__playwright__browser_snapshot()
// Check for: empty bar charts, missing volume/latency/error data, blank correlations

// Test Quality tab
mcp__playwright__browser_click({element: "Quality tab", ref: "[data-testid='quality-tab']"})
mcp__playwright__browser_snapshot()
// Check for: empty assessment names, missing pass/fail rates, blank charts

// Test Tools tab
mcp__playwright__browser_click({element: "Tools tab", ref: "[data-testid='tools-tab']"})
mcp__playwright__browser_snapshot()
// Check for: empty tool names, missing usage metrics, blank performance charts

// Test Tags tab
mcp__playwright__browser_click({element: "Tags tab", ref: "[data-testid='tags-tab']"})
mcp__playwright__browser_snapshot()
// Check for: empty tag keys/values, missing distribution charts, blank correlations
```

### Databricks UI Testing (port 3001)
```javascript
// Navigate to insights page
mcp__playwright__browser_navigate({url: "http://localhost:3001/experiments/2178582188830602/insights"})

// Take snapshot of the page
mcp__playwright__browser_snapshot()
// Check for issues: empty charts, missing data, loading errors

// Test Traffic & Cost tab
mcp__playwright__browser_click({element: "Traffic & Cost tab", ref: "[data-testid='traffic-cost-tab']"})
mcp__playwright__browser_snapshot()
// Check for: empty bar charts, missing volume/latency/error data, blank correlations

// Test Quality tab
mcp__playwright__browser_click({element: "Quality tab", ref: "[data-testid='quality-tab']"})
mcp__playwright__browser_snapshot()
// Check for: empty assessment names, missing pass/fail rates, blank charts

// Test Tools tab
mcp__playwright__browser_click({element: "Tools tab", ref: "[data-testid='tools-tab']"})
mcp__playwright__browser_snapshot()
// Check for: empty tool names, missing usage metrics, blank performance charts

// Test Tags tab
mcp__playwright__browser_click({element: "Tags tab", ref: "[data-testid='tags-tab']"})
mcp__playwright__browser_snapshot()
// Check for: empty tag keys/values, missing distribution charts, blank correlations
```