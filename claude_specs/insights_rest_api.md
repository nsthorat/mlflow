# MLflow Insights REST API Specification

## Executive Summary

This document defines the REST API endpoints and request/response formats for the MLflow Insights feature. These APIs provide trace analytics data to the frontend UI.

**Related Documentation:**
- **For product requirements, see:** `insights_ui_prd.md`
- **For frontend implementation, see:** `insights_ui_technical.md`

## Testing Database

**Test Database Path**: `/Users/nikhil.thorat/Code/mlflow-agent/mlflow_data/mlflow.db`

Use this database when testing and verifying functionality.

## REST API Endpoints

### Base Path
All endpoints are under: `/api/3.0/mlflow/traces/insights/`

### Endpoint Organization

The API is organized into logical namespaces matching the UI sections:

```
/api/3.0/mlflow/traces/insights/
├── traffic-cost/
│   ├── volume
│   ├── latency  
│   └── errors
├── assessments/
│   ├── discovery
│   └── metrics
├── tools/
│   ├── discovery
│   └── metrics
├── tags/
│   ├── discovery
│   └── metrics
├── dimensions/
│   ├── discovery
│   └── calculate-npmi
└── correlations
```

### Complete Endpoint List

#### Traffic & Cost Analytics
- `POST /api/3.0/mlflow/traces/insights/traffic-cost/volume`
- `POST /api/3.0/mlflow/traces/insights/traffic-cost/latency`
- `POST /api/3.0/mlflow/traces/insights/traffic-cost/errors`

#### Assessments Analytics
- `POST /api/3.0/mlflow/traces/insights/assessments/discovery`
- `POST /api/3.0/mlflow/traces/insights/assessments/metrics`

#### Tools Analytics
- `POST /api/3.0/mlflow/traces/insights/tools/discovery`
- `POST /api/3.0/mlflow/traces/insights/tools/metrics`

#### Tags Analytics
- `POST /api/3.0/mlflow/traces/insights/tags/discovery`
- `POST /api/3.0/mlflow/traces/insights/tags/metrics`

#### Dimensions
- `POST /api/3.0/mlflow/traces/insights/dimensions/discovery`
- `POST /api/3.0/mlflow/traces/insights/dimensions/calculate-npmi`

#### Correlations (Cross-cutting)
- `POST /api/3.0/mlflow/traces/insights/correlations`

## Common Request/Response Format

### Standard Request Structure

```json
{
    "experiment_ids": ["123", "456"],    // Required: List of experiment IDs
    "start_time": 1640995200000,         // Optional: Unix timestamp in milliseconds
    "end_time": 1640998800000,           // Optional: Unix timestamp in milliseconds
    "time_bucket": "hour"                // Optional: "hour", "day", "week" (default: "hour")
}
```

### Standard Response Structure

All endpoints return both summary totals and time-series data:

```json
{
    "summary": {
        // Aggregated totals for the entire time range
    },
    "time_series": [
        // Array of time-bucketed data points
    ]
}
```

## Endpoint Specifications

### Traffic & Cost Endpoints

#### 1. Volume

**Endpoint**: `POST /api/3.0/mlflow/traces/insights/traffic-cost/volume`

**Purpose**: Returns trace volume counts with both global totals and time-series data

**Request**:
```json
{
    "experiment_ids": ["123"],
    "start_time": 1640995200000,
    "end_time": 1640998800000,
    "time_bucket": "hour"
}
```

**Response**:
```json
{
    "summary": {
        "count": 557,
        "ok_count": 480,
        "error_count": 77
    },
    "time_series": [
        {
            "time_bucket": 1704110400000,  // 2024-01-01 12:00:00 in ms
            "count": 245,
            "ok_count": 200,
            "error_count": 45
        },
        {
            "time_bucket": 1704114000000,  // 2024-01-01 13:00:00 in ms
            "count": 312,
            "ok_count": 280,
            "error_count": 32
        }
    ]
}
```

#### 2. Latency

**Endpoint**: `POST /api/3.0/mlflow/traces/insights/traffic-cost/latency`

**Purpose**: Returns latency metrics with both global percentiles and time-series data

**Request**:
```json
{
    "experiment_ids": ["123"],
    "start_time": 1640995200000,
    "end_time": 1640998800000,
    "time_bucket": "hour"
}
```

**Response**:
```json
{
    "summary": {
        "p50_latency": 4920,      // milliseconds
        "p90_latency": 29770,
        "p99_latency": 41720,
        "avg_latency": 8500,
        "min_latency": 100,
        "max_latency": 50000
    },
    "time_series": [
        {
            "time_bucket": 1704110400000,  // 2024-01-01 12:00:00 in ms
            "p50_latency": 4920,
            "p90_latency": 29770,
            "p99_latency": 41720,
            "avg_latency": 8500
        },
        {
            "time_bucket": 1704114000000,  // 2024-01-01 13:00:00 in ms
            "p50_latency": 5100,
            "p90_latency": 30200,
            "p99_latency": 42000,
            "avg_latency": 8700
        }
    ]
}
```

#### 3. Errors

**Endpoint**: `POST /api/3.0/mlflow/traces/insights/traffic-cost/errors`

**Purpose**: Returns error statistics with both global totals and time-series data

**Request**:
```json
{
    "experiment_ids": ["123"],
    "start_time": 1640995200000,
    "end_time": 1640998800000,
    "time_bucket": "hour"
}
```

**Response**:
```json
{
    "summary": {
        "total_count": 557,
        "error_count": 77,
        "error_rate": 13.82    // percentage
    },
    "time_series": [
        {
            "time_bucket": 1704110400000,  // 2024-01-01 12:00:00 in ms
            "total_count": 245,
            "error_count": 45,
            "error_rate": 18.37    // percentage
        },
        {
            "time_bucket": 1704114000000,  // 2024-01-01 13:00:00 in ms
            "total_count": 312,
            "error_count": 32,
            "error_rate": 10.26    // percentage
        }
    ]
}
```

### Assessments Analytics Endpoints

#### 1. Assessment Discovery

**Endpoint**: `POST /api/3.0/mlflow/traces/insights/assessments/discovery`

**Purpose**: Returns all assessments with their data types and basic statistics

**Request**:
```json
{
    "experiment_ids": ["123"],
    "start_time": 1640995200000,
    "end_time": 1640998800000
}
```

**Response**:
```json
{
    "data": [
        {
            "assessment_name": "professional",
            "assessment_type": "boolean",
            "sources": ["LLM_JUDGE"],
            "trace_count": 1500
        },
        {
            "assessment_name": "reading-ease-score",
            "assessment_type": "numeric",
            "sources": ["CODE"],
            "trace_count": 1200
        },
        {
            "assessment_name": "sentiment",
            "assessment_type": "string",
            "sources": ["LLM_JUDGE"],
            "trace_count": 800
        }
    ]
}
```

#### 2. Assessment Metrics

**Endpoint**: `POST /api/3.0/mlflow/traces/insights/assessments/metrics`

**Purpose**: Returns detailed metrics for a specific assessment including time series

**Request**:
```json
{
    "experiment_ids": ["123"],
    "assessment_name": "professional",
    "start_time": 1640995200000,
    "end_time": 1640998800000,
    "time_bucket": "hour"
}
```

**Response (Boolean Assessment)**:
```json
{
    "assessment_name": "professional",
    "assessment_type": "boolean",
    "sources": ["LLM_JUDGE"],
    "summary": {
        "total_count": 1500,
        "failure_count": 25,
        "failure_rate": 1.67  // percentage
    },
    "time_series": [
        {
            "time_bucket": 1704110400000,  // 2024-01-01 12:00:00 in ms
            "total_count": 245,
            "failure_count": 4,
            "failure_rate": 1.63
        },
        {
            "time_bucket": 1704114000000,  // 2024-01-01 13:00:00 in ms
            "total_count": 312,
            "failure_count": 5,
            "failure_rate": 1.60
        }
    ]
}
```

**Response (Numeric Assessment)**:
```json
{
    "assessment_name": "reading-ease-score",
    "assessment_type": "numeric",
    "sources": ["CODE"],
    "summary": {
        "total_count": 1200,
        "p50_value": 25.36,
        "p90_value": 43.48,
        "p99_value": 56.61,
        "min_value": 5.2,
        "max_value": 89.7,
        "below_p50_count": 600
    },
    "time_series": [
        {
            "time_bucket": 1704110400000,
            "p50_value": 24.5,
            "p90_value": 42.0,
            "p99_value": 55.0,
            "count": 120
        },
        {
            "time_bucket": 1704114000000,
            "p50_value": 26.1,
            "p90_value": 44.5,
            "p99_value": 58.2,
            "count": 135
        }
    ]
}
```

**Response (String Assessment - Limited Support)**:
```json
{
    "assessment_name": "sentiment",
    "assessment_type": "string",
    "sources": ["LLM_JUDGE"],
    "summary": {
        "total_count": 800,
        "unique_values": 5,
        "top_values": [
            {"value": "positive", "count": 450, "percentage": 56.25},
            {"value": "neutral", "count": 200, "percentage": 25.0},
            {"value": "negative", "count": 150, "percentage": 18.75}
        ]
    },
    "time_series": null  // Not supported for string types yet
}
```

### Tools Analytics Endpoints

#### 1. Tool Discovery

**Endpoint**: `POST /api/3.0/mlflow/traces/insights/tools/discovery`

**Purpose**: Returns all tools with usage and performance statistics

**Request**:
```json
{
    "experiment_ids": ["123"],
    "start_time": 1640995200000,
    "end_time": 1640998800000
}
```

**Response**:
```json
{
    "data": [
        {
            "tool_name": "nikhil_tool",
            "trace_count": 30540,
            "invocation_count": 30540,
            "error_count": 0,
            "error_rate": 0.0,
            "p50_latency": 27200,
            "p90_latency": 33950,
            "p99_latency": 153820,
            "time_series": {
                "volume": [
                    {
                        "time_bucket": 1704110400000,  // 2024-01-01 12:00:00 in ms
                        "trace_count": 1234,
                        "invocation_count": 1234
                    }
                ],
                "latency": [
                    {
                        "time_bucket": 1704110400000,  // 2024-01-01 12:00:00 in ms
                        "p50_latency": 25000,
                        "p90_latency": 32000,
                        "p99_latency": 150000
                    }
                ],
                "errors": [
                    {
                        "time_bucket": 1704110400000,  // 2024-01-01 12:00:00 in ms
                        "error_rate": 0.0
                    }
                ]
            }
        },
        {
            "tool_name": "samraj_tool",
            "trace_count": 28607,
            "invocation_count": 28607,
            "error_count": 28607,
            "error_rate": 100.0,
            "p50_latency": 2,
            "p90_latency": 5,
            "p99_latency": 10,
            "time_series": {
                // Similar structure
            }
        }
    ]
}
```

#### 2. Tool Metrics

**Endpoint**: `POST /api/3.0/mlflow/traces/insights/tools/metrics`

**Purpose**: Returns detailed metrics for a specific tool

**Request**:
```json
{
    "experiment_ids": ["123"],
    "tool_name": "nikhil_tool",
    "start_time": 1640995200000,
    "end_time": 1640998800000,
    "time_bucket": "hour"
}
```

**Response**:
```json
{
    "data": {
        "tool_name": "nikhil_tool",
        "trace_count": 30540,
        "invocation_count": 30540,
        "error_count": 0,
        "error_rate": 0.0,
        "p50_latency": 27200,
        "p90_latency": 33950,
        "p99_latency": 153820,
        "time_series": {
            "volume": [...],
            "latency": [...],
            "errors": [...]
        }
    }
}
```

### Tags Analytics Endpoints

#### 1. Tag Discovery

**Endpoint**: `POST /api/3.0/mlflow/traces/insights/tags/discovery`

**Purpose**: Returns all tag keys with usage statistics

**Request**:
```json
{
    "experiment_ids": ["123"],
    "start_time": 1640995200000,
    "end_time": 1640998800000,
    "limit": 10  // Top N values per tag
}
```

**Response**:
```json
{
    "data": [
        {
            "tag_key": "persona",
            "trace_count": 186641,
            "unique_values": 23057
        },
        {
            "tag_key": "topic",
            "trace_count": 186641,
            "unique_values": 6100
        },
        {
            "tag_key": "style",
            "trace_count": 145000,
            "unique_values": 250
        }
    ]
}
```

#### 2. Tag Metrics

**Endpoint**: `POST /api/3.0/mlflow/traces/insights/tags/metrics`

**Purpose**: Returns detailed metrics for a specific tag key including value distribution

**Request**:
```json
{
    "experiment_ids": ["123"],
    "tag_key": "persona",
    "start_time": 1640995200000,
    "end_time": 1640998800000,
    "limit": 10  // Top N values to return
}
```

**Response**:
```json
{
    "data": {
        "tag_key": "persona",
        "trace_count": 186641,
        "unique_values": 23057,
        "top_values": [
            {
                "value": "Curious high school student",
                "count": 5339,
                "percentage": 2.86
            },
            {
                "value": "Software engineer specializing in machine learning",
                "count": 5126,
                "percentage": 2.75
            },
            {
                "value": "Layperson curious about new technology",
                "count": 4967,
                "percentage": 2.66
            }
        ]
    }
}
```

### Dimensions Endpoints

#### 1. Dimensions Discovery

**Endpoint**: `POST /api/3.0/mlflow/traces/insights/dimensions/discovery`

**Purpose**: Returns all available dimensions for correlation analysis with their types

**Request**:
```json
{
    "experiment_ids": ["123"],
    "start_time": 1640995200000,
    "end_time": 1640998800000
}
```

**Response**:
```json
{
    "data": [
        {
            "name": "status",
            "display_name": "Trace Status",
            "description": "Status of the trace execution",
            "parameters": [
                {
                    "name": "value",
                    "type": "enum",
                    "required": true,
                    "description": "Trace status value",
                    "enum_values": ["OK", "ERROR"]
                }
            ]
        },
        {
            "name": "span.type",
            "display_name": "Span Type", 
            "description": "Type of span in the trace",
            "parameters": [
                {
                    "name": "value",
                    "type": "enum",
                    "required": true,
                    "description": "Span type value",
                    "enum_values": ["TOOL", "LLM", "CHAIN", "RETRIEVER"]
                }
            ]
        },
        {
            "name": "latency",
            "display_name": "Execution Latency",
            "description": "Execution time threshold for trace filtering",
            "parameters": [
                {
                    "name": "threshold",
                    "type": "number",
                    "required": true,
                    "description": "Latency threshold in milliseconds"
                },
                {
                    "name": "operator",
                    "type": "enum",
                    "required": true,
                    "description": "Comparison operator",
                    "enum_values": [">", ">=", "<", "<=", "="]
                }
            ]
        },
        {
            "name": "tools.nikhil_tool",
            "display_name": "Tool: nikhil_tool",
            "description": "Usage of the nikhil_tool tool",
            "parameters": [
                {
                    "name": "value",
                    "type": "enum",
                    "required": true,
                    "description": "Tool usage status",
                    "enum_values": ["used", "error", "success"]
                }
            ]
        },
        {
            "name": "tags.persona",
            "display_name": "Tag: persona",
            "description": "Value of the persona tag",
            "parameters": [
                {
                    "name": "value",
                    "type": "string",
                    "required": true,
                    "description": "Value for the persona tag"
                }
            ]
        },
        {
            "name": "assessment.professional",
            "display_name": "Assessment: Professional",
            "description": "Professional quality assessment",
            "parameters": [
                {
                    "name": "name",
                    "type": "string",
                    "required": true,
                    "description": "Assessment name",
                    "enum_values": ["professional"]
                },
                {
                    "name": "value",
                    "type": "enum",
                    "required": true,
                    "description": "Assessment value",
                    "enum_values": ["true", "false"]
                }
            ]
        }
    ]
}
```

#### 2. Calculate NPMI

**Endpoint**: `POST /api/3.0/mlflow/traces/insights/dimensions/calculate-npmi`

**Purpose**: Calculates NPMI correlation score between two dimensions

**Request**:
```json
{
    "experiment_ids": ["123"],
    "dimension1": {
        "name": "status",
        "parameters": {
            "value": "ERROR"
        }
    },
    "dimension2": {
        "name": "tools.samraj_tool",
        "parameters": {
            "value": "used"
        }
    },
    "start_time": 1640995200000,
    "end_time": 1640998800000
}
```

**Response**:
```json
{
    "dimension1": {
        "name": "status",
        "value": "ERROR",
        "count": 6356
    },
    "dimension2": {
        "name": "tools.samraj_tool",
        "value": "samraj_tool", 
        "count": 28607
    },
    "intersection": {
        "count": 5678
    },
    "correlation": {
        "npmi_score": 0.89,
        "strength": "Strong"  // Strong/Moderate/Weak based on NPMI
    }
}
```

### Correlations Endpoint

#### 1. NPMI Correlations

**Endpoint**: `POST /api/3.0/mlflow/traces/insights/correlations`

**Purpose**: Returns NPMI correlations for a given filter

**Request**:
```json
{
    "experiment_ids": ["123"],
    "filter_string": "status = 'ERROR'",  // Filter to find correlations for
    "correlation_dimensions": ["tools", "tags", "assessments"],
    "start_time": 1640995200000,
    "end_time": 1640998800000,
    "limit": 5  // Top N correlations
}
```

**Response**:
```json
{
    "data": [
        {
            "dimension": "tool",
            "value": "samraj_tool",
            "npmi_score": 0.89,
            "trace_count": 5678,
            "percentage_of_slice": 89.2,
            "percentage_of_total": 3.04,
            "strength": "Strong"  // Strong/Moderate/Weak based on NPMI
        },
        {
            "dimension": "tag",
            "value": "environment=production",
            "npmi_score": 0.67,
            "trace_count": 3456,
            "percentage_of_slice": 54.3,
            "percentage_of_total": 1.85,
            "strength": "Moderate"
        },
        {
            "dimension": "assessment",
            "value": "professional=false",
            "npmi_score": 0.45,
            "trace_count": 234,
            "percentage_of_slice": 3.7,
            "percentage_of_total": 0.13,
            "strength": "Moderate"
        }
    ]
}
```

## Error Handling

### Standard Error Response

```json
{
    "error": {
        "code": "INVALID_PARAMETER_VALUE",
        "message": "Invalid experiment_ids: Experiment '999' does not exist",
        "details": {
            "invalid_experiments": ["999"],
            "valid_experiments": ["123", "456"]
        }
    }
}
```

### Error Codes

- `INVALID_PARAMETER_VALUE`: Invalid request parameters
- `RESOURCE_NOT_FOUND`: Experiment or data not found
- `PERMISSION_DENIED`: User lacks access to experiments
- `INTERNAL_ERROR`: Server error during processing
- `TIMEOUT`: Query execution timeout
- `RATE_LIMITED`: Too many requests

## Performance Requirements

- **Response Time**: < 500ms for standard queries
- **Timeout**: 30 seconds maximum query execution
- **Rate Limiting**: 100 requests per minute per user

## NPMI Correlation Strength Classification

- **Strong**: NPMI > 0.7
- **Moderate**: 0.4 <= NPMI <= 0.7
- **Weak**: NPMI < 0.4

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Status**: Ready for Implementation