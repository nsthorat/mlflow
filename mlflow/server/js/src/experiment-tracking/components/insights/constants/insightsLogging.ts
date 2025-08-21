/**
 * Analytics constants for insights pages component views
 * Used with useRecordComponentView to track user engagement with different insights features
 * Also contains all component IDs for consistent identification across the insights feature
 */

// Page views
export const INSIGHTS_TRAFFIC_AND_COST_PAGE_VIEW = 'mlflow.traces.insights.traffic_and_cost_page_view';
export const INSIGHTS_QUALITY_METRICS_PAGE_VIEW = 'mlflow.traces.insights.quality_metrics_page_view';
export const INSIGHTS_TOOLS_PAGE_VIEW = 'mlflow.traces.insights.tools_page_view';
export const INSIGHTS_TAGS_PAGE_VIEW = 'mlflow.traces.insights.tags_page_view';
const INSIGHTS_TOPICS_PAGE_VIEW = 'mlflow.traces.insights.topics_page_view';

// Card views
export const INSIGHTS_VOLUME_CARD_VIEW = 'mlflow.traces.insights.volume_card_view';
export const INSIGHTS_LATENCY_CARD_VIEW = 'mlflow.traces.insights.latency_card_view';
export const INSIGHTS_ERROR_RATE_CARD_VIEW = 'mlflow.traces.insights.error_rate_card_view';
export const INSIGHTS_TOOL_CARD_VIEW = 'mlflow.traces.insights.tool_card_view';
export const INSIGHTS_TOOL_OVERVIEW_CARD_VIEW = 'mlflow.traces.insights.tool_overview_card_view';
export const INSIGHTS_TAG_CARD_VIEW = 'mlflow.traces.insights.tag_card_view';

export const INSIGHTS_ASSESSMENT_CARD_VIEW = 'mlflow.traces.insights.assessment_card_view';

// Legacy TRENDS_ constants for backward compatibility with copied trends components
export const TRENDS_TOOL_CARD_VIEW = INSIGHTS_TOOL_CARD_VIEW;
export const TRENDS_TAG_CARD_VIEW = INSIGHTS_TAG_CARD_VIEW;

// Modal views
// Modal view constants (currently unused but reserved for future use)
const INSIGHTS_TRACE_EXPLORER_MODAL_VIEW = 'mlflow.traces.insights.trace_explorer_modal_view';
const INSIGHTS_CORRELATION_MODAL_VIEW = 'mlflow.traces.insights.correlation_modal_view';

// Component IDs - Cards
export const INSIGHTS_CARD_TITLE_COMPONENT_ID = 'mlflow.traces.insights.card-title';

// Component IDs - Modals
export const INSIGHTS_TRACE_EXPLORER_MODAL_COMPONENT_ID = 'mlflow.traces.insights.trace-explorer-modal';
export const INSIGHTS_MODAL_TITLE_COMPONENT_ID = 'mlflow.traces.insights.modal-title';
export const INSIGHTS_MODAL_CORRELATION_TAG_COMPONENT_ID = 'mlflow.traces.insights.modal-correlation-tag';

// Component IDs - Buttons
export const INSIGHTS_ERROR_RATE_BUTTON_COMPONENT_ID = 'mlflow.traces.insights.error-rate-view-traces-button';
export const INSIGHTS_LATENCY_BUTTON_COMPONENT_ID = 'mlflow.traces.insights.latency-view-traces-button';
export const INSIGHTS_ERROR_RETRY_BUTTON_COMPONENT_ID = 'mlflow.traces.insights.error-retry-button';
export const INSIGHTS_TOOL_BUTTON_COMPONENT_ID = 'mlflow.traces.insights.tool-view-traces-button';
export const INSIGHTS_TAG_BUTTON_COMPONENT_ID = 'mlflow.traces.insights.tag-view-traces-button';

// Component IDs - Trace List
export const INSIGHTS_TRACE_LIST_STATUS_COMPONENT_ID = 'mlflow.traces.insights.trace-list-status';
export const INSIGHTS_TRACE_REQUEST_TOOLTIP_COMPONENT_ID = 'mlflow.traces.insights.trace-request-tooltip';
export const INSIGHTS_TRACE_LIST_HEADER_COMPONENT_ID = 'mlflow.traces.insights.trace-list-header'; // Used with dynamic suffix

// Component IDs - Correlations
export const INSIGHTS_CORRELATION_ITEM_LABEL_COMPONENT_ID = 'mlflow.traces.insights.correlation-item-label';
export const INSIGHTS_CORRELATION_ITEM_STRONG_COMPONENT_ID = 'mlflow.traces.insights.correlation-item-strong';
export const INSIGHTS_CORRELATION_ITEM_MODERATE_COMPONENT_ID = 'mlflow.traces.insights.correlation-item-moderate';
export const INSIGHTS_CORRELATION_ITEM_WEAK_COMPONENT_ID = 'mlflow.traces.insights.correlation-item-weak';

// Component IDs - Selectors
// Component ID constants (currently unused but reserved for future use)
const INSIGHTS_PERCENTILE_SELECTOR_TAG_COMPONENT_ID = 'mlflow.traces.insights.percentile-selector-tag';
export const INSIGHTS_TOOL_VOLUME_SELECTOR_COMPONENT_ID = 'mlflow.traces.insights.tool-volume-selector';

// Legacy TRENDS_ button and selector aliases
export const TRENDS_TOOL_BUTTON_COMPONENT_ID = INSIGHTS_TOOL_BUTTON_COMPONENT_ID;
export const TRENDS_TOOL_VOLUME_SELECTOR_COMPONENT_ID = INSIGHTS_TOOL_VOLUME_SELECTOR_COMPONENT_ID;
export const TRENDS_TAG_BUTTON_COMPONENT_ID = INSIGHTS_TAG_BUTTON_COMPONENT_ID;
export const TRENDS_MODAL_CORRELATION_TAG_COMPONENT_ID = INSIGHTS_MODAL_CORRELATION_TAG_COMPONENT_ID;
export const TRENDS_TRACE_EXPLORER_MODAL_COMPONENT_ID = INSIGHTS_TRACE_EXPLORER_MODAL_COMPONENT_ID;
export const TRENDS_TRACE_LIST_STATUS_COMPONENT_ID = INSIGHTS_TRACE_LIST_STATUS_COMPONENT_ID;
export const TRENDS_TRACE_REQUEST_TOOLTIP_COMPONENT_ID = INSIGHTS_TRACE_REQUEST_TOOLTIP_COMPONENT_ID;
export const TRENDS_TRACE_LIST_HEADER_COMPONENT_ID = INSIGHTS_TRACE_LIST_HEADER_COMPONENT_ID;
export const TRENDS_ASSESSMENT_CARD_VIEW = INSIGHTS_ASSESSMENT_CARD_VIEW;
export const TRENDS_TOOL_OVERVIEW_CARD_VIEW = INSIGHTS_TOOL_OVERVIEW_CARD_VIEW;
export const TRENDS_QUALITY_METRICS_PAGE_VIEW = INSIGHTS_QUALITY_METRICS_PAGE_VIEW;
export const TRENDS_TAGS_PAGE_VIEW = INSIGHTS_TAGS_PAGE_VIEW;
export const TRENDS_TOOLS_PAGE_VIEW = INSIGHTS_TOOLS_PAGE_VIEW;
