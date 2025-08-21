# MLflow Insights Backend Implementation Outline

## Executive Summary

This document outlines the backend implementation approach for MLflow Insights, bridging the REST API specification with SQLAlchemy store implementation. It focuses on the critical path from API endpoints to database queries.

**Related Documentation:**
- **For API specifications, see:** `insights_rest_api.md`
- **For UI requirements, see:** `insights_ui_prd.md`
- **For frontend implementation, see:** `insights_ui_technical.md`

## Testing Database

**Test Database Path**: `/Users/nikhil.thorat/Code/mlflow-agent/mlflow_data/mlflow.db`

Use this database when testing and verifying functionality.

## Implementation Overview

### Core Architecture Principles

1. **FOLLOW EXISTING PATTERNS**: **EXTREMELY IMPORTANT** - All code MUST follow existing MLflow patterns, conventions, and styles. Study existing endpoints, handlers, and store methods. Our code should be indistinguishable from existing MLflow code.
2. **NO LIMITS**: NEVER add artificial limits (e.g., max_results). Follow MLflow's pattern of returning all data unless pagination is explicitly requested
3. **NO Store Modifications**: We will NOT modify AbstractStore or SqlAlchemyStore
4. **New Database Interface**: Create a new insights database interface that lives alongside REST handlers
5. **Pydantic Models for Everything**: ALL request/response data MUST use Pydantic models for type safety and validation
6. **SQLAlchemy Only**: All queries MUST use SQLAlchemy ORM/Core (NEVER raw SQL strings)
7. **Leverage Existing Store Methods**: The new interface will call existing store methods where possible (e.g., search_traces, calculate_trace_filter_correlation)
8. **Mirror REST API Structure**: Database interface methods exactly match REST API endpoints
9. **Consistent Response Format**: All methods return Pydantic models with `summary` and `time_series` fields
10. **Study Existing Code First**: Before implementing ANY method, find and study similar existing implementations in the codebase

## Core Principles for Dimensions Discovery

### 1. Dynamic Discovery Over Hardcoding
- Dimensions are discovered from actual data in the database
- No hardcoded lists - everything comes from querying existing traces, spans, tags, assessments
- Discovery respects time/experiment filters to show only relevant dimensions

### 2. Dimensions as Parameterized Keys
- Each dimension has a `name` that acts as a key (e.g., "status", "tools.nikhil_tool", "tags.persona")
- Each dimension defines required `parameters` with types and validation
- Parameters vary by dimension type (value, threshold+operator, name+value, etc.)

### 3. Parameter Structure by Type
- **Simple enums**: status, span.type → just need `value` parameter
- **Discovered tools**: tools.{tool_name} → `value` parameter (used/error/success)
- **Discovered tags**: tags.{key} → `value` parameter (string)
- **Thresholds**: latency → `threshold` + `operator` parameters
- **Assessments**: assessment.{name} → varies (boolean: value, numeric: threshold+operator)

### 4. Registry Pattern
- Backend maintains mapping from dimension names to parameter requirements
- Frontend queries discovery endpoint to understand what parameters each dimension needs
- NPMI calculation accepts dimension name + dynamic parameters object

### 5. Filter String Generation
- `_dimension_to_filter_string()` converts dimension name + parameters into existing filter syntax
- This bridges the new parameterized system with existing `search_traces()` and `calculate_trace_filter_correlation()` APIs

The key insight is that dimension names become dynamic keys discovered from data, and each dimension type has its own parameter requirements that the frontend needs to understand through the discovery API.

## 🚨 CRITICAL: Testing Requirement

**MANDATORY REQUIREMENT**: Whenever you change these REST APIs, you MUST always curl against that endpoint to make sure they're working. This is EXTREMELY important - anytime you touch an API endpoint, you MUST test it.

### Testing Protocol
1. **After ANY API change**: Immediately test with curl
2. **Before declaring done**: Test all modified endpoints
3. **Document test commands**: Include working curl examples
4. **Verify response format**: Ensure JSON matches expected Pydantic models

Example test pattern:
```bash
# ALWAYS use dev/run-server-dev for testing (port 5000)
# Test volume endpoint
curl -X POST http://localhost:5000/api/3.0/mlflow/traces/insights/traffic-cost/volume \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["0"], "start_time": 1640995200000, "end_time": 1640998800000}'

# Verify response structure matches VolumeResponse model
```

**NO EXCEPTIONS**: Every API change must be tested immediately.

### Implementation Completeness

**IMPORTANT**: This document shows the core structure and approach. When implementing, you MUST stay true to the REST API specifications in `insights_rest_api.md`. All response models and endpoints must match exactly what the REST API promises to return. Even though we didn't outline every single method implementation here, you must follow the REST API specification completely.

## New Insights Database Interface

### File Structure

```
mlflow/server/trace_insights/
├── __init__.py
├── insights_store.py              # Central store with all SQLAlchemy implementations
├── dimensions.py                  # Dimension discovery, NPMI calculation, filter generation
├── models.py                      # Pydantic models for requests/responses
└── handlers.py                    # Flask handlers that call insights_store and dimensions
```

### Core Pydantic Models

```python
# mlflow/server/trace_insights/models.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Base response model for all insights endpoints
class InsightsResponse(BaseModel):
    """Standard response format with summary and time_series data."""
    summary: Dict[str, Any]
    time_series: List[Dict[str, Any]]

# Specific response models for type safety
class VolumeSummary(BaseModel):
    count: int
    ok_count: int
    error_count: int

class VolumeTimeSeries(BaseModel):
    time_bucket: int  # Unix timestamp in milliseconds
    count: int
    ok_count: int
    error_count: int

class VolumeResponse(BaseModel):
    summary: VolumeSummary
    time_series: List[VolumeTimeSeries]

# Request models
class TrafficCostRequest(BaseModel):
    experiment_ids: List[str]
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    time_bucket: Optional[str] = "hour"  # "hour", "day", "week"

# Dimensions models
class DimensionParameter(BaseModel):
    name: str
    type: str  # "string", "number", "enum"
    required: bool = True
    description: Optional[str] = None
    enum_values: Optional[List[str]] = None  # For enum types

class Dimension(BaseModel):
    name: str
    display_name: str
    description: str
    parameters: List[DimensionParameter]

class DimensionsDiscoveryResponse(BaseModel):
    data: List[Dimension]

class DimensionValue(BaseModel):
    name: str
    parameters: Dict[str, str]  # Dynamic parameters based on dimension type

class DimensionRequest(BaseModel):
    experiment_ids: List[str]
    dimension1: DimensionValue
    dimension2: DimensionValue
    start_time: Optional[int] = None
    end_time: Optional[int] = None

class DimensionCount(BaseModel):
    name: str
    value: str
    count: int

class IntersectionCount(BaseModel):
    count: int

class CorrelationScore(BaseModel):
    npmi_score: float
    strength: str  # "Strong", "Moderate", "Weak"

class NPMICalculationResponse(BaseModel):
    dimension1: DimensionCount
    dimension2: DimensionCount
    intersection: IntersectionCount
    correlation: CorrelationScore
```

### InsightsStore Implementation

The central `insights_store.py` contains all SQLAlchemy implementations with methods mirroring REST endpoints.

**CRITICAL**: Before implementing, study these existing patterns:
- How `search_traces()` handles filtering and returns data
- How `calculate_trace_filter_correlation()` processes results
- How existing handlers structure request/response
- How existing store methods handle sessions and errors

```python
# mlflow/server/trace_insights/insights_store.py

from typing import List, Optional
from sqlalchemy import func, select, case
from mlflow.store.tracking import get_tracking_store
from mlflow.store.db.models import SqlTraceInfo, SqlSpan, SqlTraceTag
from mlflow.server.trace_insights.models import (
    VolumeResponse, VolumeSummary, VolumeTimeSeries,
    LatencyResponse, LatencySummary, LatencyTimeSeries,
    ErrorResponse, ErrorSummary, ErrorTimeSeries,
    AssessmentDiscoveryResponse, AssessmentMetricsResponse,
    ToolDiscoveryResponse, ToolMetricsResponse,
    TagDiscoveryResponse, TagMetricsResponse
)

class InsightsStore:
    """
    Central store for all insights-related database operations.
    Methods mirror the REST API structure exactly.
    """
    
    def __init__(self):
        self.store = get_tracking_store()
    
    # Traffic & Cost Methods
    def get_traffic_cost_volume(
        self,
        experiment_ids: List[str],
        start_time: Optional[int],
        end_time: Optional[int],
        time_bucket: Optional[str]
    ) -> VolumeResponse:
        """Get trace volume counts with both summary and time-series data."""
        # Implementation leverages search_traces() for summary + custom SQLAlchemy for time series
        pass
    
    def _get_volume_time_series(
        self,
        experiment_ids: List[str],
        start_time: Optional[int],
        end_time: Optional[int],
        time_bucket: Optional[str]
    ) -> List[VolumeTimeSeries]:
        """Helper to get time-bucketed volume data using SQLAlchemy."""
        # Implementation uses SQLAlchemy time bucketing with GROUP BY
        pass
    
    def get_traffic_cost_latency(
        self,
        experiment_ids: List[str],
        start_time: Optional[int],
        end_time: Optional[int],
        time_bucket: Optional[str]
    ) -> LatencyResponse:
        """Get latency percentiles with both summary and time-series data."""
        # Implementation calculates percentiles from search_traces() + SQLAlchemy percentile functions
        pass
    
    def _get_latency_time_series(
        self,
        experiment_ids: List[str],
        start_time: Optional[int],
        end_time: Optional[int],
        time_bucket: Optional[str]
    ) -> List[LatencyTimeSeries]:
        """Helper to get time-bucketed latency data using SQLAlchemy."""
        # Implementation uses SQLAlchemy percentile_cont() with time bucketing
        pass
    
    def get_traffic_cost_errors(
        self,
        experiment_ids: List[str],
        start_time: Optional[int],
        end_time: Optional[int],
        time_bucket: Optional[str]
    ) -> ErrorResponse:
        """Get error rates with both summary and time-series data."""
        # Implementation calculates error rates from search_traces() + SQLAlchemy aggregation
        pass
    
    def _get_error_rate_time_series(
        self,
        experiment_ids: List[str],
        start_time: Optional[int],
        end_time: Optional[int],
        time_bucket: Optional[str]
    ) -> List[ErrorTimeSeries]:
        """Helper to get time-bucketed error rate data using SQLAlchemy."""
        # Implementation uses SQLAlchemy with CASE statements for error rate calculation
        pass
    
    # Assessment Methods
    def get_assessments_discovery(
        self,
        experiment_ids: List[str],
        start_time: Optional[int],
        end_time: Optional[int]
    ) -> AssessmentDiscoveryResponse:
        """Discover all assessments with their types."""
        # Implementation to detect assessment types
        pass
    
    def get_assessments_metrics(
        self,
        experiment_ids: List[str],
        assessment_name: str,
        start_time: Optional[int],
        end_time: Optional[int],
        time_bucket: Optional[str]
    ) -> AssessmentMetricsResponse:
        """Get metrics for a specific assessment."""
        # Type-aware implementation (boolean vs numeric vs string)
        pass
    
    # Tool Methods
    def get_tools_discovery(
        self,
        experiment_ids: List[str],
        start_time: Optional[int],
        end_time: Optional[int]
    ) -> ToolDiscoveryResponse:
        """Discover all tools used in traces."""
        # Query spans with type='TOOL'
        pass
    
    def get_tools_metrics(
        self,
        experiment_ids: List[str],
        tool_name: str,
        start_time: Optional[int],
        end_time: Optional[int],
        time_bucket: Optional[str]
    ) -> ToolMetricsResponse:
        """Get metrics for a specific tool."""
        # Implementation for tool-specific metrics
        pass
    
    # Tag Methods
    def get_tags_discovery(
        self,
        experiment_ids: List[str],
        start_time: Optional[int],
        end_time: Optional[int]
    ) -> TagDiscoveryResponse:
        """Discover all tag keys."""
        # Query unique tag keys
        pass
    
    def get_tags_metrics(
        self,
        experiment_ids: List[str],
        tag_key: str,
        start_time: Optional[int],
        end_time: Optional[int],
        limit: int = 10
    ) -> TagMetricsResponse:
        """Get value distribution for a specific tag."""
        # Implementation for tag value distribution
        pass
    

    # Correlations
    def get_trace_correlations(
        self,
        experiment_ids: List[str],
        filter_string: str,
        correlation_dimensions: List[str],
        start_time: Optional[int],
        end_time: Optional[int],
        limit: int = 5
    ) -> CorrelationsResponse:
        """Get NPMI correlations for a filter."""
        # Can leverage existing calculate_trace_filter_correlation
        pass

# Global instance
insights_store = InsightsStore()
```

## Dimensions Module

### Separate Dimensions Logic

The dimensions functionality lives in a separate `dimensions.py` module since it doesn't belong in the store:

```python
# mlflow/server/trace_insights/dimensions.py

from typing import List, Optional
from mlflow.store.tracking import get_tracking_store
from mlflow.server.trace_insights.models import (
    DimensionsDiscoveryResponse, DimensionValue, NPMICalculationResponse
)

def get_dimensions_discovery(
    experiment_ids: List[str],
    start_time: Optional[int],
    end_time: Optional[int]
) -> DimensionsDiscoveryResponse:
    """Get all available dimensions for correlation analysis by discovering from actual data."""
    # Implementation discovers dimensions from database:
    # - Basic dimensions (status, span.type, latency) with parameter definitions
    # - Tool dimensions from spans table (tools.{tool_name})
    # - Tag dimensions from trace_tags table (tags.{key})
    # - Assessment dimensions from assessments table (assessment.{name})
    # Each dimension includes parameter requirements (value, threshold+operator, etc.)
    pass

def calculate_dimensions_npmi(
    experiment_ids: List[str],
    dimension1: DimensionValue,
    dimension2: DimensionValue,
    start_time: Optional[int],
    end_time: Optional[int]
) -> NPMICalculationResponse:
    """Calculate NPMI between two dimensions using existing store method."""
    
    # Convert dimensions to filter strings for existing calculate_trace_filter_correlation
    filter_string1 = dimension_to_filter_string(dimension1)
    filter_string2 = dimension_to_filter_string(dimension2)
    
    # Use existing store method (NOT a new one!)
    store = get_tracking_store()
    correlation_result = store.calculate_trace_filter_correlation(
        experiment_ids=experiment_ids,
        filter_string1=filter_string1,
        filter_string2=filter_string2
    )
    
    # Convert result to NPMICalculationResponse format
    pass

def dimension_to_filter_string(dimension: DimensionValue) -> str:
    """Convert dimension name/parameters to filter string for existing store method."""
    # Implementation maps dimension types to filter syntax:
    # - status: "status = 'ERROR'"
    # - tools.{name}: "span.name = '{name}' AND span.type = 'TOOL'"
    # - tags.{key}: "tags.{key} = '{value}'"
    # - assessment.{name}: "assessment.name = '{name}' AND assessment.feedback.value = '{value}'"
    # - latency: "execution_time_ms {operator} {threshold}"
    pass

def classify_npmi_strength(npmi_score: float) -> str:
    """Classify NPMI score strength."""
    # Implementation: Strong (>0.7), Moderate (0.4-0.7), Weak (<0.4)
    pass

# Dimension type constants and mappings
DIMENSION_PARAMETER_DEFINITIONS = {
    "status": [...],
    "span.type": [...],
    "latency": [...],
    # etc.
}
```

## Flask Handler Layer

### Handlers Call InsightsStore and Dimensions

The Flask handlers call both insights_store methods and dimensions functions:

```python
# mlflow/server/handlers.py (or mlflow/server/trace_insights/handlers.py)

from typing import Dict, Any
from flask import Response
from mlflow.server.trace_insights.insights_store import insights_store
from mlflow.server.trace_insights import dimensions
from mlflow.server.trace_insights.models import TrafficCostRequest

# Traffic & Cost Handlers (use insights_store)
def _get_traffic_cost_volume_handler() -> Response:
    """Handler for /insights/traffic-cost/volume endpoint."""
    # Extract request data and call insights_store.get_traffic_cost_volume()
    pass

def _get_traffic_cost_latency_handler():
    # Call insights_store.get_traffic_cost_latency()
    pass

def _get_traffic_cost_errors_handler():
    # Call insights_store.get_traffic_cost_errors()
    pass

# Assessment Handlers (use insights_store)
def _get_assessments_discovery_handler():
    # Call insights_store.get_assessments_discovery()
    pass

def _get_assessments_metrics_handler():
    # Call insights_store.get_assessments_metrics()
    pass

# Tool Handlers (use insights_store)
def _get_tools_discovery_handler():
    # Call insights_store.get_tools_discovery()
    pass

def _get_tools_metrics_handler():
    # Call insights_store.get_tools_metrics()
    pass

# Tag Handlers (use insights_store)
def _get_tags_discovery_handler():
    # Call insights_store.get_tags_discovery()
    pass

def _get_tags_metrics_handler():
    # Call insights_store.get_tags_metrics()
    pass

# Dimensions Handlers (use dimensions module)
def _get_dimensions_discovery_handler():
    """Handler for /insights/dimensions/discovery endpoint."""
    # Extract request data and call dimensions.get_dimensions_discovery()
    pass

def _calculate_dimensions_npmi_handler():
    """Handler for /insights/dimensions/calculate-npmi endpoint."""
    # Extract request data and call dimensions.calculate_dimensions_npmi()
    pass

# Correlations Handlers (use insights_store)
def _get_trace_correlations_handler():
    # Call insights_store.get_trace_correlations()
    pass
```

### Route Registration

```python
# Register each endpoint with its specific handler
_add_route("/api/3.0/mlflow/traces/insights/traffic-cost/volume", 
           _get_traffic_cost_volume_handler, methods=["POST"])
           
_add_route("/api/3.0/mlflow/traces/insights/traffic-cost/latency",
           _get_traffic_cost_latency_handler, methods=["POST"])
           
_add_route("/api/3.0/mlflow/traces/insights/traffic-cost/errors",
           _get_traffic_cost_errors_handler, methods=["POST"])

_add_route("/api/3.0/mlflow/traces/insights/assessments/discovery",
           _get_assessments_discovery_handler, methods=["POST"])
           
_add_route("/api/3.0/mlflow/traces/insights/assessments/metrics",
           _get_assessments_metrics_handler, methods=["POST"])

# ... etc for all endpoints
```


## Error Handling

### Standard Error Responses

- `INVALID_PARAMETER_VALUE`: Invalid experiment IDs, time ranges
- `RESOURCE_NOT_FOUND`: Experiment doesn't exist
- `INTERNAL_ERROR`: Database query failures
- Always use `MlflowException` with appropriate error codes

## Testing Strategy

### Unit Tests

- Test each analytics method with mock data
- Verify type detection for assessments
- Test time bucketing logic
- Validate percentile calculations

### Integration Tests

- End-to-end API tests for each endpoint
- Test with different database backends (PostgreSQL, MySQL, SQLite)
- Performance tests with large datasets
- Verify response format consistency


## Critical Success Factors

1. **No FileStore Support**: SQLAlchemy only - FileStore returns NotImplementedError
2. **Consistent Response Format**: All endpoints follow summary + time_series pattern
3. **Type-Aware Processing**: Correctly handle different assessment types
4. **Performance**: Sub-500ms response time for standard queries
5. **Database Agnostic**: Works across PostgreSQL, MySQL, SQLite

---

**Document Version**: 1.0  
**Status**: Implementation Outline  
**Next Steps**: Begin Phase 1 implementation with core infrastructure