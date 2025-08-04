"""
Analysis utilities for MLflow tracing.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TraceFilterCorrelationResult:
    """
    Result of calculating correlation between two trace filter conditions.

    This class represents the correlation analysis between two trace filters,
    using Normalized Pointwise Mutual Information (NPMI) as the correlation metric.

    Attributes:
        npmi: Normalized Pointwise Mutual Information score (-1 to 1).
              -1 indicates filters never co-occur, 0 indicates independence,
              1 indicates filters always co-occur together.
        confidence_lower: Lower bound of the confidence interval for NPMI.
        confidence_upper: Upper bound of the confidence interval for NPMI.
        filter_string1_count: Number of traces matching the first filter.
        filter_string2_count: Number of traces matching the second filter.
        joint_count: Number of traces matching both filters.
        total_count: Total number of traces in the experiment(s).
    """

    npmi: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    filter_string1_count: int = 0
    filter_string2_count: int = 0
    joint_count: int = 0
    total_count: int = 0
