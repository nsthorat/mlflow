"""
Parser for MLflow trace search filter DSL to parameterized SQL.

This module converts MLflow filter expressions like:
    "status = 'OK' AND name LIKE '%test%'"
Into parameterized SQL WHERE clauses with parameter bindings.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from mlflow.exceptions import MlflowException
from mlflow.protos.databricks_pb2 import INVALID_PARAMETER_VALUE


class FilterOperator(str, Enum):
    """Supported filter operators."""
    EQ = "="
    NEQ = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    LIKE = "LIKE"
    ILIKE = "ILIKE"
    IN = "IN"
    NOT_IN = "NOT IN"


@dataclass
class FilterCondition:
    """Represents a single filter condition."""
    field: str
    operator: FilterOperator
    value: Any
    is_count_expr: bool = False
    count_condition: Optional["FilterCondition"] = None
    

class TraceFilterParser:
    """
    Parser for converting MLflow trace filter DSL to parameterized SQL.
    
    This parser handles:
    - Direct attribute filters (status, timestamp, etc.)
    - Tag filters (tags.*, name)
    - Metadata filters (metadata.*, run_id)
    - Feedback filters (feedback.*)
    - Span filters (span.*)
    - Count expressions (count(span.type = 'LLM') > 2)
    """
    
    # Valid searchable attribute keys
    VALID_ATTRIBUTE_KEYS = {
        "request_id", "timestamp", "timestamp_ms", 
        "execution_time", "execution_time_ms", "status",
        "name", "run_id"
    }
    
    # Field mappings
    SEARCH_KEY_TO_TAG = {
        "name": "mlflow.traceName",
    }
    
    SEARCH_KEY_TO_METADATA = {
        "run_id": "mlflow.sourceRun",
    }
    
    SEARCH_KEY_TO_ATTRIBUTE = {
        "timestamp": "timestamp_ms",
        "execution_time": "execution_time_ms",
    }
    
    # Valid operators by field type
    NUMERIC_OPERATORS = {FilterOperator.EQ, FilterOperator.NEQ, FilterOperator.GT, 
                        FilterOperator.GTE, FilterOperator.LT, FilterOperator.LTE}
    
    STRING_OPERATORS = {FilterOperator.EQ, FilterOperator.NEQ, FilterOperator.LIKE, 
                       FilterOperator.ILIKE, FilterOperator.IN, FilterOperator.NOT_IN}
    
    TAG_OPERATORS = {FilterOperator.EQ, FilterOperator.NEQ}  # Limited for performance
    
    # Special fields that support full string operations even when mapped to tags
    STRING_MAPPED_FIELDS = {"name"}  # These support LIKE even though they map to tags
    
    def __init__(self, table_name: str):
        """
        Initialize the parser with a table name.
        
        Args:
            table_name: The name of the trace table to query
        """
        self.table_name = table_name
        self.param_counter = 0
        
    def parse(self, filter_string: Optional[str]) -> Tuple[List[str], Dict[str, Any]]:
        """
        Parse a filter string into SQL WHERE conditions and parameters.
        
        Args:
            filter_string: The MLflow filter DSL string
            
        Returns:
            Tuple of (list of WHERE conditions, parameter dictionary)
            
        Example:
            >>> parser = TraceFilterParser("traces")
            >>> conditions, params = parser.parse("status = 'OK' AND name LIKE '%test%'")
            >>> conditions
            ['state = :param_0', "tags.value LIKE :param_1"]
            >>> params
            {'param_0': 'OK', 'param_1': '%test%'}
        """
        if not filter_string:
            return [], {}
            
        conditions = []
        params = {}
        
        # Split by AND (MLflow only supports AND, not OR)
        # This is a simplified parser - production would use proper tokenization
        filter_parts = self._split_by_and(filter_string)
        
        for part in filter_parts:
            condition, part_params = self._parse_condition(part.strip())
            if condition:
                conditions.append(condition)
                params.update(part_params)
                
        return conditions, params
    
    def _split_by_and(self, filter_string: str) -> List[str]:
        """Split filter string by AND, respecting parentheses and quotes."""
        # Simplified implementation - production would use sqlparse
        parts = []
        current = []
        depth = 0
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(filter_string):
            char = filter_string[i]
            
            # Handle quotes
            if char in ('"', "'") and (i == 0 or filter_string[i-1] != '\\'):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
            
            # Handle parentheses
            elif not in_quotes:
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                # Check for AND
                elif depth == 0 and filter_string[i:i+4].upper() == ' AND':
                    parts.append(''.join(current).strip())
                    current = []
                    i += 4
                    continue
                    
            current.append(char)
            i += 1
            
        if current:
            parts.append(''.join(current).strip())
            
        return parts
    
    def _parse_condition(self, condition_str: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Parse a single condition into SQL and parameters."""
        condition_str = condition_str.strip()
        
        # Handle empty condition
        if not condition_str:
            return None, {}
        
        # Check for count expression
        if condition_str.startswith("count("):
            return self._parse_count_expression(condition_str)
            
        # Parse regular condition
        # Match patterns like: field operator value
        # This regex handles quoted strings, numbers, and IN expressions
        pattern = r'([^\s]+)\s*(!=|>=|<=|>|<|=|LIKE|ILIKE|NOT IN|IN)\s*(.+)'
        match = re.match(pattern, condition_str, re.IGNORECASE)
        
        if not match:
            raise MlflowException(
                f"Invalid filter condition: {condition_str}",
                error_code=INVALID_PARAMETER_VALUE
            )
            
        field = match.group(1).strip('`"')
        operator = FilterOperator(match.group(2).upper())
        value_str = match.group(3).strip()
        
        # Parse the value
        value = self._parse_value(value_str, operator)
        
        # Generate SQL based on field type
        if field.startswith("tags."):
            return self._generate_tag_condition(field[5:], operator, value)
        elif field.startswith("metadata."):
            return self._generate_metadata_condition(field[9:], operator, value)
        elif field.startswith("feedback."):
            return self._generate_feedback_condition(field[9:], operator, value)
        elif field.startswith("span."):
            return self._generate_span_condition(field[5:], operator, value)
        elif field in self.SEARCH_KEY_TO_TAG:
            # Map to tag
            tag_key = self.SEARCH_KEY_TO_TAG[field]
            # Check if this field supports full string operations
            if field in self.STRING_MAPPED_FIELDS:
                # Allow full string operations for special fields like 'name'
                return self._generate_tag_condition(tag_key, operator, value, use_key=True, 
                                                   allow_string_ops=True)
            else:
                return self._generate_tag_condition(tag_key, operator, value, use_key=True)
        elif field in self.SEARCH_KEY_TO_METADATA:
            # Map to metadata
            metadata_key = self.SEARCH_KEY_TO_METADATA[field]
            return self._generate_metadata_condition(metadata_key, operator, value, use_key=True)
        else:
            # Direct attribute
            return self._generate_attribute_condition(field, operator, value)
    
    def _parse_value(self, value_str: str, operator: FilterOperator) -> Any:
        """Parse a value string into appropriate Python type."""
        value_str = value_str.strip()
        
        # Handle IN/NOT IN lists
        if operator in (FilterOperator.IN, FilterOperator.NOT_IN):
            # Parse tuple like ('a', 'b', 'c')
            if value_str.startswith('(') and value_str.endswith(')'):
                value_str = value_str[1:-1]
            values = []
            for item in value_str.split(','):
                item = item.strip()
                values.append(self._parse_single_value(item))
            return values
        
        return self._parse_single_value(value_str)
    
    def _parse_single_value(self, value_str: str) -> Any:
        """Parse a single value string."""
        value_str = value_str.strip()
        
        # String with quotes
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]
        
        # Boolean
        if value_str.lower() == 'true':
            return True
        elif value_str.lower() == 'false':
            return False
        
        # Number
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            # Treat as string if no quotes (shouldn't happen in valid DSL)
            return value_str
    
    def _get_param_name(self) -> str:
        """Generate a unique parameter name."""
        name = f"param_{self.param_counter}"
        self.param_counter += 1
        return name
    
    def _generate_attribute_condition(self, field: str, operator: FilterOperator, 
                                     value: Any) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL for direct attribute condition."""
        # Map field aliases
        if field in self.SEARCH_KEY_TO_ATTRIBUTE:
            field = self.SEARCH_KEY_TO_ATTRIBUTE[field]
            
        # Map MLflow field names to SQL column names
        column_map = {
            "request_id": "trace_id",
            "timestamp_ms": "request_time",
            "execution_time_ms": "execution_duration_ms",
            "status": "state",
        }
        
        column = column_map.get(field, field)
        
        # Validate operator for field type
        if field in ("timestamp_ms", "execution_time_ms"):
            if operator not in self.NUMERIC_OPERATORS:
                raise MlflowException(
                    f"Invalid operator {operator} for numeric field {field}",
                    error_code=INVALID_PARAMETER_VALUE
                )
        
        param_name = self._get_param_name()
        
        if operator == FilterOperator.IN:
            # Build IN clause with multiple parameters
            param_names = []
            params = {}
            for val in value:
                pname = self._get_param_name()
                param_names.append(f":{pname}")
                params[pname] = val
            sql = f"{column} IN ({', '.join(param_names)})"
            return sql, params
        elif operator == FilterOperator.NOT_IN:
            param_names = []
            params = {}
            for val in value:
                pname = self._get_param_name()
                param_names.append(f":{pname}")
                params[pname] = val
            sql = f"{column} NOT IN ({', '.join(param_names)})"
            return sql, params
        else:
            sql = f"{column} {operator.value} :{param_name}"
            return sql, {param_name: value}
    
    def _generate_tag_condition(self, tag_key: str, operator: FilterOperator, 
                               value: Any, use_key: bool = False, 
                               allow_string_ops: bool = False) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL for tag condition (requires subquery)."""
        # Determine which operators are allowed
        allowed_operators = self.STRING_OPERATORS if allow_string_ops else self.TAG_OPERATORS
        
        if operator not in allowed_operators:
            raise MlflowException(
                f"Operator {operator} not supported for tags",
                error_code=INVALID_PARAMETER_VALUE
            )
        
        param_name = self._get_param_name()
        
        # For now, return a placeholder - actual implementation would generate subquery
        # This is where you'd generate EXISTS subquery for tag matching
        if use_key:
            # Using predefined key mapping
            condition = f"tags['{tag_key}'] {operator.value} :{param_name}"
        else:
            # Direct tag key
            condition = f"tags['{tag_key}'] {operator.value} :{param_name}"
            
        return condition, {param_name: value}
    
    def _generate_metadata_condition(self, metadata_key: str, operator: FilterOperator,
                                    value: Any, use_key: bool = False) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL for metadata condition."""
        param_name = self._get_param_name()
        condition = f"trace_metadata['{metadata_key}'] {operator.value} :{param_name}"
        return condition, {param_name: value}
    
    def _generate_feedback_condition(self, feedback_name: str, operator: FilterOperator,
                                    value: Any) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL for feedback condition (complex JSON extraction)."""
        # This would generate EXISTS subquery with JSON extraction
        # Simplified for now
        param_name = self._get_param_name()
        condition = f"feedback.{feedback_name} {operator.value} :{param_name}"
        return condition, {param_name: value}
    
    def _generate_span_condition(self, span_field: str, operator: FilterOperator,
                                value: Any) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL for span condition."""
        # Map span fields
        valid_span_fields = {"type", "name", "status", "content"}
        if span_field not in valid_span_fields:
            raise MlflowException(
                f"Invalid span field: {span_field}",
                error_code=INVALID_PARAMETER_VALUE
            )
        
        # Special handling for content (only LIKE/ILIKE)
        if span_field == "content" and operator not in {FilterOperator.LIKE, FilterOperator.ILIKE}:
            raise MlflowException(
                f"span.content only supports LIKE/ILIKE operators",
                error_code=INVALID_PARAMETER_VALUE
            )
        
        param_name = self._get_param_name()
        # This would generate EXISTS subquery for span matching
        condition = f"span_{span_field} {operator.value} :{param_name}"
        return condition, {param_name: value}
    
    def _parse_count_expression(self, expr: str) -> Tuple[str, Dict[str, Any]]:
        """Parse count expression like count(span.type = 'LLM') > 2."""
        # Extract the count condition and comparison
        pattern = r'count\((.*?)\)\s*(>=|<=|!=|>|<|=)\s*(.+)'
        match = re.match(pattern, expr, re.IGNORECASE)
        
        if not match:
            raise MlflowException(
                f"Invalid count expression: {expr}",
                error_code=INVALID_PARAMETER_VALUE
            )
        
        inner_condition = match.group(1)
        count_operator = FilterOperator(match.group(2))
        count_value = self._parse_single_value(match.group(3))
        
        # Parse the inner condition
        inner_sql, inner_params = self._parse_condition(inner_condition)
        
        # Generate count SQL (simplified - would need aggregation subquery)
        param_name = self._get_param_name()
        sql = f"COUNT({inner_sql}) {count_operator.value} :{param_name}"
        
        params = inner_params.copy()
        params[param_name] = count_value
        
        return sql, params