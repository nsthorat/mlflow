# MLflow Server with PostgreSQL

This directory contains Docker configurations for running MLflow server with PostgreSQL backend, including the `pg_trgm` extension required for efficient span content search.

## Prerequisites

- Docker and Docker Compose installed
- Port 5001 (MLflow) and 5432 (PostgreSQL) available

## Quick Start

1. Navigate to the insights directory:

   ```bash
   cd insights
   ```

2. Build and start the services:

   ```bash
   docker-compose up -d --build
   ```

3. Verify services are running:

   ```bash
   docker-compose ps
   ```

4. Access MLflow UI at http://localhost:5001

## Architecture

- **PostgreSQL 15**: Database backend with `pg_trgm` extension pre-installed
- **MLflow Server**: Running from source with PostgreSQL backend store
- **Automatic Migrations**: MLflow will run database migrations on startup

## Configuration

### PostgreSQL

- Database: `mlflow`
- User: `mlflow`
- Password: `mlflow123`
- Port: `5432`
- Extension: `pg_trgm` (installed via init-db.sql)

### MLflow Server

- Port: `5001` (mapped from container port 5000)
- Backend Store: PostgreSQL
- Artifact Store: `/mlruns` (local volume)

## Testing the Setup

1. Check PostgreSQL connection and pg_trgm extension:

   ```bash
   docker exec mlflow-postgres psql -U mlflow -d mlflow -c "SELECT * FROM pg_extension WHERE extname = 'pg_trgm';"
   ```

2. Create a test experiment:

   ```bash
   curl -X POST http://localhost:5001/api/2.0/mlflow/experiments/create \
     -H "Content-Type: application/json" \
     -d '{"name": "test-experiment"}'
   ```

3. Verify database tables were created:
   ```bash
   docker exec -it mlflow-postgres psql -U mlflow -d mlflow -c "\dt"
   ```

## Docker CLI Commands

### Build the image:

```bash
docker build -f insights/Dockerfile -t mlflow-postgres:latest .
```

### Run PostgreSQL container:

```bash
docker run -d \
  --name mlflow-postgres \
  -e POSTGRES_DB=mlflow \
  -e POSTGRES_USER=mlflow \
  -e POSTGRES_PASSWORD=mlflow123 \
  -p 5432:5432 \
  -v $(pwd)/insights/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql \
  postgres:15-alpine
```

### Run MLflow container:

```bash
docker run -d \
  --name mlflow-server \
  --link mlflow-postgres:postgres \
  -p 5001:5000 \
  -e MLFLOW_BACKEND_STORE_URI=postgresql://mlflow:mlflow123@postgres:5432/mlflow \
  mlflow-postgres:latest
```

## Stopping Services

```bash
docker-compose down
```

To also remove volumes:

```bash
docker-compose down -v
```

## Troubleshooting

1. **Check logs**:

   ```bash
   docker-compose logs mlflow
   docker-compose logs postgres
   ```

2. **Verify pg_trgm extension**:

   ```bash
   docker exec -it mlflow-postgres psql -U mlflow -d mlflow -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
   ```

3. **Check MLflow health**:
   ```bash
   curl http://localhost:5001/health
   ```

## Using the Trace Filter Correlation API

The trace filter correlation API allows you to analyze relationships between different trace characteristics using Normalized Pointwise Mutual Information (NPMI). This is useful for understanding patterns in your ML system behavior.

### API Overview

```python
from mlflow.tracing.client import TracingClient

client = TracingClient()
result = client.calculate_trace_filter_correlation(
    experiment_ids=["experiment_id"],
    filter_string1="first_condition",
    filter_string2="second_condition",
)

# Result contains:
# - npmi: Correlation score (-1 to 1)
# - filter_string1_count: Number of traces matching filter 1
# - filter_string2_count: Number of traces matching filter 2
# - joint_count: Number of traces matching both filters
# - total_count: Total traces searched
```

### Filter Syntax Examples

#### 1. Span Type Filters

```python
# Find correlation between LLM spans and TOOL spans
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="span.type = 'LLM'",
    filter_string2="span.type = 'TOOL'",
)

# Check if RETRIEVER spans correlate with CHAIN spans
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="span.type = 'RETRIEVER'",
    filter_string2="span.type = 'CHAIN'",
)
```

#### 2. Span Attribute Filters

```python
# Correlate model usage with response quality
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="span.attributes['model_name'] = 'gpt-4'",
    filter_string2="span.attributes['response_quality'] = 'high'",
)

# Check if certain prompts correlate with errors
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="span.attributes['prompt_template'] = 'complex_reasoning'",
    filter_string2="span.status = 'ERROR'",
)
```

#### 3. Count Expression Filters

Count expressions allow you to filter traces based on the number of spans matching certain criteria. Currently, count expressions support filtering by:

- `span.type`: The span type (e.g., 'LLM', 'TOOL', 'RETRIEVER')
- `span.name`: The span name (supports LIKE patterns)
- `span.status`: The span status ('OK', 'ERROR', etc.)

```python
# Traces with multiple LLM calls vs high latency
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="count(span.type = 'LLM') > 3",
    filter_string2="trace.execution_time_ms > 5000",
)

# Traces with errors vs traces with many retries
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="count(span.status = 'ERROR') > 0",
    filter_string2="count(span.name LIKE '%retry%') > 2",
)

# Complex reasoning chains vs successful outcomes
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="count(span.type = 'CHAIN') >= 5",
    filter_string2="trace.status = 'OK'",
)

# Multiple retrieval operations vs tool usage
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="count(span.type = 'RETRIEVER') > 2",
    filter_string2="count(span.type = 'TOOL') > 0",
)
```

#### 4. Feedback and Assessment Filters

```python
# High quality feedback vs model type
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="feedback.quality >= 0.8",
    filter_string2="span.attributes['model'] = 'claude-3'",
)

# User satisfaction vs response time
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="feedback.user_rating > 4",
    filter_string2="trace.execution_time_ms < 2000",
)

# Accuracy assessments vs retrieval usage
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="assessment.accuracy = 'correct'",
    filter_string2="count(span.type = 'RETRIEVER') > 0",
)
```

#### 5. Latency and Performance Filters

```python
# Slow traces vs database operations
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="trace.execution_time_ms > 10000",
    filter_string2="span.name LIKE '%database%'",
)

# Fast responses vs cached results
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="trace.execution_time_ms < 500",
    filter_string2="span.attributes['cache_hit'] = 'true'",
)

# Timeout errors vs external API calls
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="span.attributes['error_type'] = 'timeout'",
    filter_string2="span.attributes['service'] = 'external_api'",
)
```

#### 6. Tag-based Filters

```python
# Production errors vs deployment version
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="tags.environment = 'production' AND trace.status = 'ERROR'",
    filter_string2="tags.version = 'v2.0.1'",
)

# Customer type vs feature usage
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="tags.customer_tier = 'enterprise'",
    filter_string2="count(span.name = 'advanced_analysis') > 0",
)
```

#### 7. Complex Combined Filters

```python
# Multi-condition analysis: Complex queries with errors
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="""
        count(span.type = 'LLM') > 2 AND
        trace.execution_time_ms > 5000 AND
        tags.query_type = 'complex'
    """,
    filter_string2="trace.status = 'ERROR'",
)

# Resource usage patterns
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="""
        count(span.type = 'EMBEDDING') > 5 OR
        count(span.name LIKE '%embed%') > 3
    """,
    filter_string2="tags.resource_alert = 'high_usage'",
)
```

### Interpreting Results

The NPMI score ranges from -1 to 1:

- **NPMI ≈ 1**: Strong positive correlation (conditions often occur together)
- **NPMI ≈ 0**: No correlation (conditions are independent)
- **NPMI ≈ -1**: Strong negative correlation (conditions rarely occur together)

Example interpretation:

```python
result = client.calculate_trace_filter_correlation(
    experiment_ids=["exp1"],
    filter_string1="count(span.type = 'RETRIEVER') > 0",
    filter_string2="feedback.accuracy = 'high'",
)

print(f"NPMI: {result.npmi:.3f}")
print(f"Traces with retrieval: {result.filter_string1_count}")
print(f"Traces with high accuracy: {result.filter_string2_count}")
print(f"Traces with both: {result.joint_count}")
print(f"Total traces: {result.total_count}")

# If NPMI is 0.7, this suggests retrieval usage is strongly correlated
# with high accuracy responses
```

### REST API Usage

You can also use the REST API directly:

```bash
curl -X POST http://localhost:5001/api/2.0/mlflow/traces/calculate-filter-correlation \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_ids": ["experiment_id"],
    "filter_string1": "span.type = '\''LLM'\''",
    "filter_string2": "trace.execution_time_ms > 3000"
  }'
```

### Common Use Cases

1. **Performance Analysis**: Identify what trace characteristics correlate with slow performance
2. **Error Analysis**: Find patterns in traces that result in errors
3. **Model Comparison**: Compare behavior patterns between different models
4. **Feature Impact**: Understand how feature usage correlates with outcomes
5. **Quality Assurance**: Identify factors that correlate with high-quality responses
6. **Resource Optimization**: Find patterns in resource-intensive operations
