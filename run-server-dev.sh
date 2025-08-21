#!/bin/bash
# MLflow Development Server Script
# Starts both backend (port 5000) and frontend (port 3000)

BACKEND_PORT=5000
FRONTEND_PORT=3000
DB_PATH="/Users/nikhil.thorat/Code/mlflow-agent/mlflow_data/mlflow.db"

# Use the local development version of MLflow
export PYTHONPATH="/Users/nikhil.thorat/Code/mlflow-corey:$PYTHONPATH"

echo "=== MLflow Development Environment ==="
echo ""

# Kill any existing servers
echo "Killing any existing servers..."
lsof -ti:$BACKEND_PORT | xargs kill 2>/dev/null
lsof -ti:$FRONTEND_PORT | xargs kill 2>/dev/null
sleep 2

# Start backend server
echo "Starting backend server on port $BACKEND_PORT..."
echo "  Database: $DB_PATH"
echo "  PYTHONPATH: $PYTHONPATH"

/opt/homebrew/anaconda3/bin/python -m mlflow server \
  --host 127.0.0.1 \
  --port $BACKEND_PORT \
  --backend-store-uri sqlite:///$DB_PATH \
  > server.log 2>&1 &

BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# Wait for backend to start
echo "Waiting for backend to start..."
for i in {1..10}; do
  if curl -s http://localhost:$BACKEND_PORT/health > /dev/null; then
    echo "  ✓ Backend is ready!"
    break
  fi
  sleep 1
done

# Start frontend dev server
echo ""
echo "Starting frontend dev server on port $FRONTEND_PORT..."
cd mlflow/server/js
yarn start > ../../../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"
cd ../../..

# Summary
echo ""
echo "=== Development Servers Running ==="
echo "  Backend:  http://localhost:$BACKEND_PORT"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo ""
echo "Logs:"
echo "  Backend:  tail -f server.log"
echo "  Frontend: tail -f frontend.log"
echo ""
echo "To stop both servers: kill $BACKEND_PID $FRONTEND_PID"
echo "Or press Ctrl+C to stop this script"

# Wait for Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait