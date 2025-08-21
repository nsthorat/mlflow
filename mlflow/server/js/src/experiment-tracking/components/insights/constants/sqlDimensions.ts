/**
 * SQL Dimensions for MLflow Traces
 *
 * This file contains centralized SQL dimension definitions as UDF-style functions.
 * These dimensions can be used for filtering, correlation analysis, and future assessment integration.
 */

import { SQL_FIELDS, SQL_VALUES } from './sqlConstants';
import { AssessmentInfo } from '../types/insightsTypes';

/**
 * Dimension metadata interface
 */
export interface SqlDimension {
  id: string;
  name: string;
  description: string;
  type: 'boolean' | 'categorical' | 'numerical';
  generateSql: (params?: DimensionParams) => string;
  generateCorrelationSql?: (params?: DimensionParams) => string;
}

/**
 * Parameters for dimension functions
 */
export interface DimensionParams {
  latencyThreshold?: number;
  tagKey?: string;
  tagValue?: string;
  toolName?: string;
  assessmentName?: string;
}

/**
 * Core dimension implementations
 */

/**
 * Is Error Dimension
 * Returns SQL expression to identify error traces
 */
export const isErrorDimension = (): string => {
  return `${SQL_FIELDS.STATE} = '${SQL_VALUES.ERROR_STATE}'`;
};

/**
 * Is Slow Trace Dimension
 * Returns SQL expression to identify traces slower than the given threshold
 */
export const isSlowTraceDimension = (latencyThreshold: number): string => {
  if (typeof latencyThreshold !== 'number' || latencyThreshold <= 0) {
    throw new Error('latencyThreshold must be a positive number');
  }
  return `${SQL_FIELDS.EXECUTION_DURATION} > ${latencyThreshold}`;
};

/**
 * Has Tag Value Dimension
 * Returns SQL expression to identify traces with specific tag key-value pairs
 */
export const hasTagValueDimension = (tagKey: string, tagValue: string): string => {
  if (!tagKey || !tagValue) {
    throw new Error('Both tagKey and tagValue are required');
  }
  return `${SQL_FIELDS.TAGS}['${tagKey}'] = '${tagValue}'`;
};

/**
 * Has Tag Key Dimension
 * Returns SQL expression to identify traces with specific tag key (regardless of value)
 */
export const hasTagKeyDimension = (tagKey: string): string => {
  if (!tagKey) {
    throw new Error('tagKey is required');
  }
  return `${SQL_FIELDS.TAGS}['${tagKey}'] IS NOT NULL`;
};

/**
 * Has Tool Dimension
 * Returns SQL expression to identify traces that use a specific tool
 * TODO: REMOVE THIS REGEX WORKAROUND ONCE MLFLOW ADDS A METADATA FIELD FOR BASE TOOL NAME
 * MLflow currently adds numeric suffixes to tool names when there are multiple calls
 * of the same tool in a trace (e.g., execute_sql_query_1, execute_sql_query_2).
 * This regex removes the suffix to group tools by their base functionality.
 * This should be replaced with a proper metadata field once MLflow provides one.
 */
export const hasToolDimension = (toolName: string): string => {
  if (!toolName) {
    throw new Error('toolName is required');
  }
  return `EXISTS(spans, s -> s.attributes['mlflow.spanType'] = '"TOOL"' AND (
    CASE 
      WHEN s.name RLIKE '_[0-9]+$' THEN 
        REGEXP_REPLACE(s.name, '_[0-9]+$', '')
      ELSE 
        s.name
    END = '${toolName}'
  ))`;
};

/**
 * Has Assessment Failure Dimension
 * Returns SQL expression to identify traces with failed assessments (LLM judge pass/fail = "no")
 */
export const hasAssessmentFailureDimension = (assessmentName?: string): string => {
  const baseCondition = `EXISTS(assessments, a -> a.feedback.value = '"no"' OR a.feedback.value = 'false')`;

  if (assessmentName) {
    return `EXISTS(assessments, a -> a.name = '${assessmentName}' AND (a.feedback.value = '"no"' OR a.feedback.value = 'false'))`;
  }

  return baseCondition;
};

/**
 * Has Assessment Failure Dimension with Type Awareness
 * Returns SQL expression to identify traces with failed assessments using AssessmentInfo for accurate type detection
 */
const hasAssessmentFailureDimensionTyped = (assessmentName: string, assessmentInfo?: AssessmentInfo): string => {
  if (!assessmentInfo) {
    // Fallback to original function if no type info available
    return hasAssessmentFailureDimension(assessmentName);
  }

  // Generate type-specific failure conditions based on AssessmentInfo
  let failureCondition: string;

  switch (assessmentInfo.dtype) {
    case 'boolean':
      failureCondition = `a.feedback.value = 'false'`;
      break;
    case 'pass-fail':
      failureCondition = `a.feedback.value = '"no"'`;
      break;
    case 'numeric':
      // For numeric assessments, we could define failure as below a threshold
      // For now, we'll use a generic approach or require explicit configuration
      if (assessmentInfo.valueRange) {
        const midpoint = (assessmentInfo.valueRange.min + assessmentInfo.valueRange.max) / 2;
        failureCondition = `CAST(a.feedback.value AS DOUBLE) < ${midpoint}`;
      } else {
        // Fallback to checking for explicitly low values
        failureCondition = `CAST(a.feedback.value AS DOUBLE) < 0.5`;
      }
      break;
    case 'string':
    default:
      // For string assessments, use the unique values to determine failure patterns
      if (assessmentInfo.uniqueValues) {
        const potentialFailureValues = assessmentInfo.uniqueValues.filter(
          (val) =>
            val.toLowerCase().includes('fail') ||
            val.toLowerCase().includes('no') ||
            val.toLowerCase().includes('error') ||
            val.toLowerCase().includes('bad'),
        );
        if (potentialFailureValues.length > 0) {
          const quotedValues = potentialFailureValues.map((val) => `'${val}'`).join(', ');
          failureCondition = `a.feedback.value IN (${quotedValues})`;
        } else {
          // Fallback to generic string failure patterns
          failureCondition = `(a.feedback.value = '"no"' OR a.feedback.value = 'false' OR a.feedback.value LIKE '%fail%')`;
        }
      } else {
        failureCondition = `(a.feedback.value = '"no"' OR a.feedback.value = 'false' OR a.feedback.value LIKE '%fail%')`;
      }
      break;
  }

  return `EXISTS(assessments, a -> a.name = '${assessmentName}' AND (${failureCondition}))`;
};

/**
 * Dimension registry - maps dimension IDs to their implementations
 */
const SQL_DIMENSIONS: Record<string, SqlDimension> = {
  isError: {
    id: 'isError',
    name: 'Is Error',
    description: 'Identifies traces that resulted in an error state',
    type: 'boolean',
    generateSql: () => isErrorDimension(),
  },
  isSlowTrace: {
    id: 'isSlowTrace',
    name: 'Is Slow Trace',
    description: 'Identifies traces that exceed a specified latency threshold',
    type: 'boolean',
    generateSql: (params?: DimensionParams) => {
      if (!params?.latencyThreshold) {
        throw new Error('latencyThreshold parameter is required for isSlowTrace dimension');
      }
      return isSlowTraceDimension(params.latencyThreshold);
    },
  },
  hasTagValue: {
    id: 'hasTagValue',
    name: 'Has Tag Value',
    description: 'Identifies traces with a specific tag key-value pair',
    type: 'boolean',
    generateSql: (params?: DimensionParams) => {
      if (!params?.tagKey || !params?.tagValue) {
        throw new Error('tagKey and tagValue parameters are required for hasTagValue dimension');
      }
      return hasTagValueDimension(params.tagKey, params.tagValue);
    },
  },
  hasTagKey: {
    id: 'hasTagKey',
    name: 'Has Tag Key',
    description: 'Identifies traces with a specific tag key (regardless of value)',
    type: 'boolean',
    generateSql: (params?: DimensionParams) => {
      if (!params?.tagKey) {
        throw new Error('tagKey parameter is required for hasTagKey dimension');
      }
      return hasTagKeyDimension(params.tagKey);
    },
  },
  hasTool: {
    id: 'hasTool',
    name: 'Has Tool',
    description: 'Identifies traces that use a specific tool',
    type: 'boolean',
    generateSql: (params?: DimensionParams) => {
      if (!params?.toolName) {
        throw new Error('toolName parameter is required for hasTool dimension');
      }
      return hasToolDimension(params.toolName);
    },
  },
  hasAssessmentFailure: {
    id: 'hasAssessmentFailure',
    name: 'Has Assessment Failure',
    description: 'Identifies traces with failed assessments (pass/fail = "no" or boolean = false)',
    type: 'boolean',
    generateSql: (params?: DimensionParams) => {
      return hasAssessmentFailureDimension(params?.assessmentName);
    },
  },
};

/**
 * Utility function to get dimension by ID
 */
const getDimension = (dimensionId: string): SqlDimension | undefined => {
  return SQL_DIMENSIONS[dimensionId];
};

/**
 * Utility function to get all available dimensions
 */
const getAllDimensions = (): SqlDimension[] => {
  return Object.values(SQL_DIMENSIONS);
};

/**
 * Utility function to generate SQL for a dimension with parameters
 */
const generateDimensionSql = (dimensionId: string, params?: DimensionParams): string => {
  const dimension = getDimension(dimensionId);
  if (!dimension) {
    throw new Error(`Unknown dimension: ${dimensionId}`);
  }
  return dimension.generateSql(params);
};

/**
 * Utility function to combine multiple dimensions with AND logic
 */
export const combineDimensionsAnd = (dimensionExpressions: string[]): string => {
  if (dimensionExpressions.length === 0) {
    throw new Error('At least one dimension expression is required');
  }
  if (dimensionExpressions.length === 1) {
    return dimensionExpressions[0];
  }
  return `(${dimensionExpressions.join(' AND ')})`;
};

/**
 * Utility function to combine multiple dimensions with OR logic
 */
const combineDimensionsOr = (dimensionExpressions: string[]): string => {
  if (dimensionExpressions.length === 0) {
    throw new Error('At least one dimension expression is required');
  }
  if (dimensionExpressions.length === 1) {
    return dimensionExpressions[0];
  }
  return `(${dimensionExpressions.join(' OR ')})`;
};

/**
 * Helper function to create multi-dimensional filter expression for tool and error analysis
 * TODO: REMOVE THIS REGEX WORKAROUND ONCE MLFLOW ADDS A METADATA FIELD FOR BASE TOOL NAME
 * MLflow currently adds numeric suffixes to tool names when there are multiple calls
 * of the same tool in a trace (e.g., execute_sql_query_1, execute_sql_query_2).
 * This regex removes the suffix to group tools by their base functionality.
 * This should be replaced with a proper metadata field once MLflow provides one.
 */
export const createToolErrorDimensionExpression = (toolName: string): string => {
  if (!toolName) {
    throw new Error('toolName is required');
  }

  const toolDimension = hasToolDimension(toolName);
  const errorDimension = isErrorDimension();

  return combineDimensionsAnd([toolDimension, errorDimension]);
};
