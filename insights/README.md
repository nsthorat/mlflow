# MLflow Insights Prototype

This directory contains a prototype for advanced trace analysis capabilities in MLflow, including correlation analysis and powerful search functionality. The prototype runs on a PostgreSQL-backed MLflow server with enhanced querying capabilities.

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Port 5001 (MLflow) and 5432 (PostgreSQL) available

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

## Server Architecture

### PostgreSQL Backend

- **PostgreSQL 15**: Database backend with `pg_trgm` extension pre-installed
- **MLflow Server**: Running from source with PostgreSQL backend store
- **Automatic Migrations**: MLflow will run database migrations on startup

### Configuration

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

## Logging Traces to the Server

Once your server is running, you can start logging traces from your ML applications. Here's how to configure your client and log traces:

### Basic Setup

```python
import mlflow
from mlflow import MlflowClient

# Point to your insights server
mlflow.set_tracking_uri("http://localhost:5001")

# Create an experiment
client = MlflowClient()
experiment_id = client.create_experiment("my-ml-app")
mlflow.set_experiment("my-ml-app")
```

### Logging Traces with the Fluent API

```python
import mlflow.tracing.fluent as fluent


# Simple trace with automatic instrumentation
@fluent.trace(name="chat_completion")
def process_query(query: str) -> str:
    # Your ML logic here
    with fluent.start_span("retrieve_context") as span:
        span.set_attributes({"query_length": len(query)})
        context = retrieve_documents(query)
        span.set_outputs({"num_docs": len(context)})

    with fluent.start_span("generate_response", span_type="LLM") as span:
        span.set_attributes({"model": "gpt-4", "temperature": 0.7, "max_tokens": 500})
        response = llm.generate(query, context)
        span.set_outputs({"response_length": len(response)})

    return response


# Call your traced function
result = process_query("What is MLflow?")

# Add trace-level tags
trace_id = fluent.get_last_active_trace_id()
client.set_trace_tag(trace_id, "environment", "production")
client.set_trace_tag(trace_id, "version", "v1.2.0")
```

### Logging Feedback and Assessments

```python
# Log user feedback
from mlflow.tracing.client import TracingClient

# Get the most recent trace
tracing_client = TracingClient()
traces = tracing_client.search_traces(experiment_ids=[experiment_id], max_results=1)
if traces:
    trace_id = traces[0].info.trace_id

    # Log feedback scores
    client.log_feedback(
        trace_id=trace_id,
        feedback={"quality": 0.9, "user_rating": 5, "relevance": 0.85},
    )

    # Log assessments
    client.log_assessment(
        trace_id=trace_id,
        assessment={
            "accuracy": "correct",
            "safety": "safe",
            "helpfulness": "very_helpful",
        },
    )
```

### Advanced Trace Logging

```python
# Manual trace construction for more control
trace = mlflow.start_trace(name="rag_pipeline")

# Root span for the entire pipeline
with mlflow.start_span(name="rag_process", span_type="CHAIN") as root:
    root.set_inputs({"query": "Explain transformers"})

    # Retrieval phase
    with mlflow.start_span(name="retrieval", span_type="RETRIEVER") as ret_span:
        ret_span.set_attributes(
            {"index": "documentation", "top_k": 5, "similarity_threshold": 0.7}
        )
        docs = retriever.search(query)
        ret_span.set_outputs({"documents": [d.id for d in docs]})

    # Multiple LLM calls for different purposes
    with mlflow.start_span(name="summarize_context", span_type="LLM") as sum_span:
        sum_span.set_attributes({"model": "gpt-3.5-turbo"})
        summary = llm.summarize(docs)

    with mlflow.start_span(name="generate_answer", span_type="LLM") as gen_span:
        gen_span.set_attributes({"model": "gpt-4", "temperature": 0.3})
        answer = llm.generate(query, summary)
        gen_span.set_outputs({"answer": answer})

    root.set_outputs({"final_answer": answer})

# End the trace
mlflow.end_trace(trace.info.trace_id)

# Add metadata
client.set_trace_tag(trace.info.trace_id, "pipeline_type", "rag")
client.set_trace_tag(trace.info.trace_id, "customer_id", "12345")
```

### Logging Error Traces

```python
@fluent.trace(name="error_prone_operation")
def risky_operation(data):
    try:
        with fluent.start_span("validation") as span:
            if not validate_input(data):
                span.set_status("ERROR")
                span.set_attributes({"error_type": "validation_failed"})
                raise ValueError("Invalid input data")

        with fluent.start_span("processing") as span:
            result = process_data(data)
            span.set_outputs({"result": result})
            return result

    except Exception as e:
        # The trace will capture the error
        fluent.get_current_active_span().set_status("ERROR")
        fluent.get_current_active_span().set_attributes(
            {"error_message": str(e), "error_type": type(e).__name__}
        )
        raise
```

## Searching Traces

The insights server provides powerful search capabilities for finding and analyzing traces. Here's how to use the search functionality:

### Basic Search

```python
from mlflow.tracing.client import TracingClient

client = TracingClient(tracking_uri="http://localhost:5001")

# Search all traces in an experiment
traces = client.search_traces(experiment_ids=[experiment_id], max_results=100)

# Search with basic filters
traces = client.search_traces(
    experiment_ids=[experiment_id],
    filter_string="trace.status = 'OK'",
    order_by=["trace.timestamp_ms DESC"],
)
```

### Filtering by Trace Properties

```python
# Filter by execution time
fast_traces = client.search_traces(
    experiment_ids=[experiment_id], filter_string="trace.execution_time_ms < 1000"
)

# Filter by status
error_traces = client.search_traces(
    experiment_ids=[experiment_id], filter_string="trace.status = 'ERROR'"
)

# Filter by timestamp (last 24 hours)
import time

yesterday = int((time.time() - 86400) * 1000)
recent_traces = client.search_traces(
    experiment_ids=[experiment_id], filter_string=f"trace.timestamp_ms > {yesterday}"
)
```

### Filtering by Span Characteristics

```python
# Find traces containing specific span types
llm_traces = client.search_traces(
    experiment_ids=[experiment_id], filter_string="span.type = 'LLM'"
)

# Find traces with specific span names
database_traces = client.search_traces(
    experiment_ids=[experiment_id], filter_string="span.name LIKE '%database%'"
)

# Find traces with span errors
span_error_traces = client.search_traces(
    experiment_ids=[experiment_id], filter_string="span.status = 'ERROR'"
)

# Find traces with specific span attributes
gpt4_traces = client.search_traces(
    experiment_ids=[experiment_id], filter_string="span.attributes['model'] = 'gpt-4'"
)
```

### Using Count Expressions

```python
# Find traces with multiple LLM calls
multi_llm_traces = client.search_traces(
    experiment_ids=[experiment_id], filter_string="count(span.type = 'LLM') > 3"
)

# Find traces with at least one error span
error_span_traces = client.search_traces(
    experiment_ids=[experiment_id], filter_string="count(span.status = 'ERROR') > 0"
)

# Find complex pipelines
complex_traces = client.search_traces(
    experiment_ids=[experiment_id],
    filter_string="count(span.type = 'CHAIN') >= 2 AND count(span.type = 'RETRIEVER') > 0",
)
```

### Filtering by Tags

```python
# Filter by environment
prod_traces = client.search_traces(
    experiment_ids=[experiment_id], filter_string="tags.environment = 'production'"
)

# Filter by multiple tags
enterprise_v2_traces = client.search_traces(
    experiment_ids=[experiment_id],
    filter_string="tags.customer_tier = 'enterprise' AND tags.version = 'v2.0'",
)
```

### Filtering by Feedback and Assessments

```python
# High-quality traces
quality_traces = client.search_traces(
    experiment_ids=[experiment_id], filter_string="feedback.quality > 0.8"
)

# Traces with positive user ratings
happy_users = client.search_traces(
    experiment_ids=[experiment_id], filter_string="feedback.user_rating >= 4"
)

# Correct and safe traces
good_traces = client.search_traces(
    experiment_ids=[experiment_id],
    filter_string="assessment.accuracy = 'correct' AND assessment.safety = 'safe'",
)
```

### Complex Search Queries

```python
# Combine multiple conditions
complex_search = client.search_traces(
    experiment_ids=[experiment_id],
    filter_string="""
        trace.status = 'OK' AND
        trace.execution_time_ms < 5000 AND
        count(span.type = 'LLM') > 1 AND
        feedback.quality > 0.7 AND
        tags.environment = 'production'
    """,
    order_by=["trace.timestamp_ms DESC"],
    max_results=50,
)

# Search for performance issues
perf_issues = client.search_traces(
    experiment_ids=[experiment_id],
    filter_string="""
        (trace.execution_time_ms > 10000 OR count(span.status = 'ERROR') > 0) AND
        tags.environment = 'production'
    """,
    order_by=["trace.execution_time_ms DESC"],
)
```

### Analyzing Search Results

```python
# Get search results and analyze
traces = client.search_traces(
    experiment_ids=[experiment_id],
    filter_string="span.type = 'LLM' AND trace.execution_time_ms > 3000",
)

print(f"Found {len(traces)} slow LLM traces")

# Analyze patterns
for trace in traces[:10]:
    print(f"Trace ID: {trace.info.trace_id}")
    print(f"Execution time: {trace.info.execution_time_ms}ms")
    print(f"Status: {trace.info.status}")

    # Count LLM spans
    llm_spans = [s for s in trace.data.spans if s.type == "LLM"]
    print(f"Number of LLM calls: {len(llm_spans)}")

    # Get tags
    if trace.info.tags:
        print(f"Tags: {trace.info.tags}")
    print("---")
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
