#!/bin/bash
set -e

# Usage: 
#   dev/run-dev-server-databricks.sh [profile] [backend-uri] [registry-uri]
# Or use environment variables:
#   BACKEND_STORE_URI=... REGISTRY_STORE_URI=... dev/run-dev-server-databricks.sh

# Allow profile to be passed as argument, default to eng-ml-inference-team-us-west-2
PROFILE="${1:-eng-ml-inference-team-us-west-2}"

# Allow backend and registry URIs to be customized via args or env vars
# For Databricks, the tracking URI should just be "databricks", not "databricks://..."
BACKEND_URI="${2:-${BACKEND_STORE_URI:-databricks}}"
REGISTRY_URI="${3:-${REGISTRY_STORE_URI:-databricks-uc}}"

function wait_server_ready {
  for backoff in 0 1 2 4 8; do
    echo "Waiting for tracking server to be ready..."
    sleep $backoff
    if curl --fail --silent --show-error --output /dev/null $1; then
      echo "Server is ready"
      return 0
    fi
  done
  echo -e "\nFailed to launch tracking server"
  return 1
}

mkdir -p outputs
echo "Running Databricks-connected tracking server in the background (profile: $PROFILE)"

# Check if yarn dependencies are installed
if [ ! -d "mlflow/server/js/node_modules" ]; then
  pushd mlflow/server/js
  yarn install
  popd
fi

# Get OAuth token for the profile if using databricks-cli auth
# This ensures MLflow can authenticate to Databricks APIs
# But prefer environment variables if they're already set
if [ -z "$DATABRICKS_TOKEN" ] && command -v databricks &> /dev/null; then
  echo "Getting auth token for profile: $PROFILE"
  TOKEN_JSON=$(databricks auth token --profile "$PROFILE" 2>/dev/null)
  if [ $? -eq 0 ]; then
    DATABRICKS_TOKEN=$(echo "$TOKEN_JSON" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    DATABRICKS_HOST=$(databricks auth profiles | grep "^$PROFILE" | awk '{print $2}')
    echo "  Using OAuth token from databricks-cli"
    echo "  Host: $DATABRICKS_HOST"
  fi
fi

# Use environment variables if they're set
if [ -n "$DATABRICKS_HOST" ] && [ -n "$DATABRICKS_TOKEN" ]; then
  echo "Using provided DATABRICKS_HOST and DATABRICKS_TOKEN"
fi

# Using uvicorn directly with environment variables 
# The mlflow CLI has validation issues with databricks URIs
echo "Starting MLflow server in Databricks proxy mode"
echo "  Profile: $PROFILE"
echo "  Backend Store URI: $BACKEND_URI"
echo "  Registry Store URI: $REGISTRY_URI"
DATABRICKS_CONFIG_PROFILE="$PROFILE" \
DATABRICKS_HOST="$DATABRICKS_HOST" \
DATABRICKS_TOKEN="$DATABRICKS_TOKEN" \
_MLFLOW_SERVER_FILE_STORE="$BACKEND_URI" \
_MLFLOW_SERVER_REGISTRY_STORE="$REGISTRY_URI" \
uv run python -m uvicorn mlflow.server.fastapi_app:app --host localhost --port 5001 --reload &

wait_server_ready localhost:5001/health

echo "Starting frontend dev server on port 3001..."
PORT=3001 MLFLOW_PROXY=http://localhost:5001/ yarn --cwd mlflow/server/js start