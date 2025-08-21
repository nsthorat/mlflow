# MLflow Insights UI - Product Requirements Document (PRD)

## Executive Summary

This document defines the product requirements for MLflow Insights UI - a comprehensive analytics platform for ML tracing data. The Insights UI provides real-time analytics about trace performance, quality metrics, tool usage, and tag distributions through an intuitive dashboard interface.

**For technical implementation details, see:** `insights_ui_technical.md`

## Product Requirements

### Navigation and Layout

#### Insights Tab
- A new "Insights" tab that appears next to the "Traces" tab
- **Tab Visibility Rules**:
  - **When on Traces tab**: Insights tab is visible, other experiment tabs (Overview, Runs, etc.) are visible
  - **When on Insights tab**: Insights tab is visible, other experiment tabs (Traces, Overview, Runs, etc.) are visible
  - **When on other tabs**: Insights tab is NOT visible (acts as a secret/hidden link)
- **Navigation Behavior**: Users can navigate between Traces and Insights tabs freely when either is active
- Maintains consistent MLflow UI styling and theme

#### Time Range Selector
- **Location**: Top of the Insights page
- **Type**: Standard calendar dropdown selector
- **Options**:
  - Preset ranges: Last hour, Last 6 hours, Last 24 hours, Last 7 days, Last 30 days
  - Custom date/time range picker
  - Default: Last 24 hours

#### Left-Hand Navigation

The Insights page will have a left-hand sidebar navigation with the following sections:

1. **Traffic & Cost**
   - Primary view for trace volume, latency, and error metrics
   - Default selected view when opening Insights

2. **Quality Metrics**
   - Assessment analysis and quality scoring
   - Success/failure rates and distributions

3. **Tools**
   - Tool discovery and performance analytics
   - Usage patterns and error rates by tool

4. **Tags**
   - Tag distribution and value analysis
   - Tag-based segmentation and filtering

5. **Topics**
   - Topic modeling and clustering (future implementation)
   - Placeholder for advanced analytics

6. **Create View**
   - Custom view builder
   - Save and share custom analytics dashboards

#### Content Area

- **Location**: Right side of the page (main content area)
- **Behavior**: Renders the selected subpage based on left navigation selection
- **Layout**: Responsive grid layout with cards and charts
- **URL Routing**: Each subpage maintains its own state and can be bookmarked
- **Deep Linking**: URL should reflect the current subpage selection
  - Example URLs:
    - `/insights/traffic-cost` (default)
    - `/insights/quality-metrics`
    - `/insights/tools`
    - `/insights/tags`
    - `/insights/topics`
    - `/insights/create-view`
- **Page Refresh Behavior**: When page refreshes, should navigate directly to the subpage specified in URL

### Traffic & Cost Subpage

#### Volume Over Time (Full Width)

**Component**: Full-width bar chart
- **Header**: "Traffic" icon with total trace count (e.g., "186,641 traces")
- **Chart Type**: Bar chart
- **X-axis**: Date (time buckets based on selected range)
- **Y-axis**: Volume (number of traces)
- **Interaction**: Hover shows exact trace count for each time bucket
- **Color**: Single color bars (#077A9D)
- **🚨 EXCEPTION**: This chart does NOT include correlations section (unlike all other cards)

#### Two-Column Layout Below

##### Latency Card (Left)

**Component**: Line chart with percentile metrics
- **Header**: "Latency" with clock icon
- **Metrics Display**: Three key values shown above chart
  - P50: e.g., "4.92s"
  - P90: e.g., "29.77s"  
  - P99: e.g., "41.72s"
- **Chart Type**: Multi-line chart
- **X-axis**: Date
- **Y-axis**: Latency in seconds/milliseconds
- **Lines**: Three separate lines with different colors
  - P50: Light blue (#8BCAE7)
  - P90: Dark blue (#077A9D)
  - P99: Orange (#FFAB00)
- **View Traces Button**: Links to filtered trace view

##### Error Rate Card (Right)

**Component**: Line chart with error rate metrics
- **Header**: "Error rate" with warning icon
- **Primary Metric**: Large percentage display (e.g., "16.6%")
- **Additional Info**: Total error traces count
- **Chart Type**: Single line chart
- **X-axis**: Date
- **Y-axis**: Error rate percentage (0-100%)
- **Line Color**: Red (#DC2626)
- **View Traces Button**: Links to filtered error traces

#### Correlations Section (Bottom of Each Card)

**Component**: Expandable correlation insights
- **Header**: "Correlations"
- **Items**: List of correlated dimensions with:
  - Icon and label (e.g., tag icon + "style: nikhil")
  - Strength indicator (Strong/Moderate/Weak)
  - Statistics: "X traces • Y% of slice • Z% of total"
  - Color-coded correlation strength bar

### Quality Metrics Subpage

#### Assessment Discovery

**Process**: Query all available assessments in the time window
- Automatically detect assessment data types (boolean, numeric, string)
- Group assessments by type for appropriate visualization

#### Two-Column Card Layout

Each assessment gets its own card in a 2-column responsive grid:

##### Assessment Card Structure

**Card Header**:
- **Icon**: Check circle for assessments
- **Assessment Name**: e.g., "professional", "reading-ease-score"
- **Data Type Badge**: Shows detected type (boolean, numeric, string)

**Card Body Content**:

For **Boolean Assessments**:
- **Assessment Name**: Large title
- **Statistics**: "X assessments • Y failures"
- **Failure Rate**: Prominent percentage display (e.g., "1.7% failure rate")
- **Sources**: List of assessment sources (e.g., "Sources: LLM_JUDGE")
- **Chart**: Bar chart showing failure rate over time
  - X-axis: Date
  - Y-axis: Failure rate percentage
  - Bar Color: Red (#DC2626) for failures

For **Numeric Assessments**:
- **Assessment Name**: Large title
- **Statistics**: "X assessments • Y below p50"
- **Percentile Metrics**: Display P50, P90, P99 values
  - P50: e.g., "25.36"
  - P90: e.g., "43.48"
  - P99: e.g., "56.61"
- **Sources**: List of assessment sources (e.g., "Sources: CODE")
- **Chart**: Line chart showing percentile trends
  - X-axis: Date
  - Y-axis: Assessment value
  - Line Color: Blue (#077A9D)

For **String Assessments**:
- **Assessment Name**: Large title
- **Warning Icon**: Alert triangle
- **Message**: "Data type: string"
- **Subtitle**: "Visualization not yet supported for this assessment type"
- **No Chart**: Placeholder state

##### Correlations Section (Per Card)

**For Assessments with Failures**:
- **Header**: "Correlations for Failures"
- **Correlation Items**: 
  - Icon and dimension label
  - Strength indicator (Strong/Moderate/Weak)
  - Statistics and percentage bars
- **Empty State**: "No correlations for failures found" when none exist

**For Numeric Assessments**:
- **Header**: "Correlations for Below P50"
- Similar structure to failure correlations

### Tools Subpage

#### Overall Tools Summary Section

**Header**: "All tools" with tool icon

**Three-Column Layout**:

##### Column 1: Counts Card

**Component**: Tool usage statistics with distribution chart
- **Metrics Display**:
  - Unique Tools count (e.g., "2")
  - Total Invocations count (e.g., "59,147")
  - Traces with Tools count (e.g., "59,147")
- **Chart**: Horizontal bar chart
  - Shows tool names on Y-axis
  - Shows invocation counts on X-axis
  - Sorted by count (descending)
  - Different color for each tool bar
  - Example: nikhil_tool (30,540), samraj_tool (28,607)

##### Column 2: Latencies Card

**Component**: Overall latency metrics with tool breakdown
- **Metrics Display**: P50, P90, P99 for all tools combined
  - P50: e.g., "27.20s"
  - P90: e.g., "33.95s"
  - P99: e.g., "153.82s"
- **Chart**: Horizontal stacked bar chart
  - Shows tool names on Y-axis
  - Shows latency values on X-axis
  - Color-coded bars for different latency levels
  - Example: nikhil_tool (40.07s), samraj_tool (2ms)

##### Column 3: Errors Card

**Component**: Error statistics with tool breakdown
- **Metrics Display**:
  - Average Error Rate percentage (e.g., "48.4%")
  - Traces with Errors count
  - Tools with Errors count (e.g., "1")
- **Chart**: Horizontal bar chart
  - Shows tool names on Y-axis
  - Shows error rate percentage on X-axis
  - Red color bars (#DC2626)
  - Example: samraj_tool (100.0%)

#### Individual Tool Cards Section

**Layout**: Each tool gets a row with 3 columns
**Discovery**: Use tool discovery query to find all tools

##### Per-Tool Card Structure

Each tool (e.g., "nikhil_tool", "samraj_tool") has:

**Column 1: Volume**
- **Header**: Tool name with tool icon
- **Metrics**: "X traces • Y invocations"
- **Toggle**: Switch between "Traces" and "Invocations" view
- **Chart**: Bar chart
  - X-axis: Date
  - Y-axis: Count (traces or invocations)
  - Bar Color: Blue (#077A9D)
- **View Traces Button**: Links to filtered traces

**Column 2: Latency**
- **Header**: "Latency" with clock icon
- **Metrics Display**: P50, P90, P99 values
- **Chart**: Multi-line chart
  - X-axis: Date
  - Y-axis: Latency (ms or seconds)
  - Three lines: P50 (#8BCAE7), P90 (#077A9D), P99 (#FFAB00)
- **View Traces Button**: Links to filtered traces
- **Correlations**: Section showing correlated dimensions

**Column 3: Errors**
- **Header**: "Errors" with warning icon
- **Primary Metric**: Error rate percentage
- **Chart Options**:
  - If errors exist: Line chart showing error rate over time
    - X-axis: Date
    - Y-axis: Error rate percentage
    - Line Color: Red/Pink (#C82D4C)
  - If no errors: "No Errors" message with subtitle "All invocations completed successfully"
- **View Traces Button**: Links to error traces (disabled if 0 errors)
- **Correlations**: Section showing error correlations

### Tags Subpage

#### Tag Discovery and Distribution

**Process**: Query all available tag keys from traces in the time window
- Automatically discover all tag keys used in experiments
- **🚨 FILTER RULE**: Completely ignore all tags where the key has "mlflow." prefix (case-insensitive)
- Count traces per tag key and unique values per key
- Sort keys by trace count (descending)

#### Two-Column Card Layout

Each tag key gets its own card in a 2-column responsive grid:

##### Tag Card Structure

**Card Header**:
- **Icon**: Tag icon (label/price tag icon)
- **Tag Key Name**: e.g., "persona", "topic", "style"
- **View Traces Button**: Links to traces filtered by this tag key

**Card Statistics**:
- **Primary Metric**: Total trace count with this tag (e.g., "186,641")
- **Secondary Info**: "usage(s) across X value(s)" (e.g., "usage(s) across 23,057 value(s)")

**Value Distribution Chart**:
- **Chart Type**: Horizontal stacked bar chart
- **Data**: Top 10 tag values by count
- **Layout**:
  - Each row shows tag value text on the left
  - Horizontal bar on the right showing count
  - Bars use different colors for visual distinction
  - Sorted by count (descending)
- **Bar Colors**: Use a color scale with distinct colors for each value
  - Top value: Primary blue (#077A9D)
  - Subsequent values: Gradient from blue to lighter shades
  - Lower values: Gray scale for less prominent items
- **Value Display**:
  - Tag value text (truncated if too long)
  - Count number on the right side of each bar
- **X-axis Label**: "Invocations →" at bottom of chart

**Example Values**:
- For "persona" tag:
  - "Curious high school student" - 5,339
  - "Software engineer specializing in machine learning" - 5,126
  - "Layperson curious about new technology" - 4,967
  - (etc.)
- For "topic" tag:
  - "Databricks Architecture" - 20,408
  - "Acquisition Rumors" - 17,586
  - "Lakehouse Paradigm" - 9,788
  - (etc.)

##### Correlations Section (Per Card)

**Component**: Expandable correlation insights
- **Header**: "Correlations"
- **Default State**: Show "No correlations found" when no filter is active
- **When Correlations Exist**:
  - List of correlated dimensions (e.g., tools, assessments)
  - Icon and label for each correlation
  - Strength indicator (Strong/Moderate/Weak)
  - Statistics: "X traces • Y% of slice"
  - Visual correlation strength bar
- **Clear Selection Button**: Clears any active correlation filter

##### Interactive Features

**Click on Tag Value**:
- Highlights the selected value in the chart
- Updates correlations section to show correlations for that specific tag value
- Other cards update to show correlations with the selected value
- "Clear selection" button becomes active

**Hover Effects**:
- Show full tag value text in tooltip if truncated
- Display exact count and percentage of total

## 🚨 CRITICAL: Universal Correlations Requirement

### EVERY Card MUST Have Correlations

**MANDATORY REQUIREMENT**: ALL cards across ALL subpages MUST include a Correlations section at the bottom. This is NON-NEGOTIABLE.

#### What Are Correlations?

Correlations use **NPMI (Normalized Pointwise Mutual Information)** scoring to identify dimensions that are statistically associated with the current filter context of each card. They help users understand what factors are related to the metric they're viewing.

#### Universal Correlation Structure

**Every single card** in the Insights UI must have this correlation section:

**Location**: Bottom of every card, below the main content
**Header**: "Correlations" or contextual variant (e.g., "Correlations for Failures", "Correlations for Errors")

**Correlation Computation**:
1. Take the current filter context for the card (e.g., "error traces", "tool X invocations", "assessment Y failures")
2. Compute NPMI scores against these dimensions:
   - **Tools**: Which tools correlate with this filter
   - **Tags**: Which tag key-value pairs correlate
   - **Assessments**: Which assessment failures/values correlate
   - **Errors**: Error patterns that correlate
   - **Other relevant dimensions** based on context
3. Sort by NPMI score (descending)
4. Display top 5 correlations

**Visual Structure**:
- **Correlation Item**: 
  - Icon representing the dimension type (tool, tag, assessment)
  - Label with the correlated value
  - Strength indicator: "Strong" (NPMI > 0.7), "Moderate" (0.4-0.7), "Weak" (< 0.4)
  - Statistics: "X traces • Y% of slice • Z% of total"
  - Visual strength bar (colored based on strength)

**Empty State**:
- When no significant correlations exist: "No correlations found"
- Minimum NPMI threshold: 0.2 (don't show weak correlations below this)

#### Correlation Examples by Card Type

**Traffic & Cost - Latency Card**:
- Shows what correlates with high latency traces (P90+)
- Example: "tool: complex_analyzer - Strong - 1,234 traces • 67% of high latency"

**Traffic & Cost - Error Rate Card**:
- Shows what correlates with error traces
- Example: "tag: environment=production - Strong - 5,678 traces • 89% of errors"

**Quality Metrics - Assessment Card (Boolean)**:
- Shows what correlates with assessment failures
- Example: "tool: validator - Moderate - 234 traces • 45% of failures"

**Tools - Individual Tool Card (Errors column)**:
- Shows what correlates with that tool's errors
- Example: "tag: model=gpt-4 - Strong - 890 traces • 78% of tool errors"

**Tags - Tag Card**:
- Shows what correlates with specific tag values when selected
- Example: "assessment: professional=false - Moderate - 345 traces • 56% of selection"

#### Non-Negotiable Correlation Rules

1. **NO CARD WITHOUT CORRELATIONS**: Every single card must have correlations
   - **🚨 EXCEPTION**: Volume Over Time chart on Traffic & Cost page does NOT have correlations
2. **CONSISTENT PLACEMENT**: Always at the bottom of the card
3. **SAME VISUAL STYLE**: Use the same component/styling across all cards
4. **REAL-TIME UPDATES**: Correlations must update when filters change
5. **PERFORMANCE**: Must be computed efficiently (use caching)

## Visual Reference Screenshots

For exact visual specifications and layout details, refer to the reference screenshots:

- **Traffic & Cost Section**: See `reference_screenshots/traffic_cost.png`
- **Quality Metrics Section**: See `reference_screenshots/quality_metrics.png`
- **Tools Section**: See `reference_screenshots/tools.png`
- **Tags Section**: See `reference_screenshots/tags.png`

These screenshots provide the exact styling, spacing, colors, and component layouts that should be implemented.

## Testing Database

**Test Database Path**: `/Users/nikhil.thorat/Code/mlflow-agent/mlflow_data/mlflow.db`

Use this database when testing and verifying functionality.

## Related Documentation

**For technical implementation details, see:** `insights_ui_technical.md`

## UI Implementation Reference

**Important UI Reference Path**: `~/universe mlflow/web/js/src/experiment-tracking/components/experiment-page/components/traces-v3/trends`

This path contains important reference implementations for how the UI should be built. It's crucial to reference this when thinking about UI architecture and implementation patterns.

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Status**: Ready for Implementation