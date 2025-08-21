# Console Cleanup Errors Documentation

This document tracks all console errors, warnings, and spam messages found during the cleanup process to enable Playwright MCP to read console output properly.

## Error #1: React.forwardRef() Warning

**Error Type:** React Warning
**Severity:** Warning
**Status:** ✅ **FIXED**

### Error Message:
```
Warning: Function components cannot be given refs. Attempts to access this ref will fail. Did you mean to use React.forwardRef()?

Check the render method of `SlotClone`.
```

### Location:
- **Component:** Tooltip (design-system InfoTooltip)
- **Context:** TraceActionsDropdown → GenAITracesTableActions → TracesV3Content
- **Stack Trace Origins:** 
  - `design-system_src_design-system_Tooltip_InfoTooltip_tsx`
  - `js_packages_web-shared_src_genai-traces-table_GenAiTracesTableBody_tsx`
  - `mlflow_web_js_src_experiment-tracking_components_experiment-page_components_traces-v3_TracesV-*`

### Analysis:
This is a React warning caused by the design system's Tooltip component not properly handling refs when used within the GenAI traces table. The warning occurs in the traces view component stack.

### Root Cause:
The Tooltip component in the design system needs to use `React.forwardRef()` to properly handle ref forwarding to function components.

### Impact:
- Creates console noise that prevents Playwright MCP from reading console output
- Does not break functionality but indicates improper ref handling
- Appears in traces table interactions

### Recommended Action:
1. **Short-term:** Suppress this specific warning in development
2. **Long-term:** Fix the Tooltip component in design system to use `React.forwardRef()`
3. **Investigation needed:** Check if this is a known issue in the design system

### Files to Investigate:
- `js/packages/web-shared/src/genai-traces-table/GenAITracesTableActions.tsx:146-154` ✅ **FOUND**

### Solution Found:
The issue is in `GenAITracesTableActions.tsx` lines 146-154. The `Tooltip` component is trying to forward a ref to the `ActionButton` (Button component), but the Button component isn't properly handling ref forwarding.

**Current problematic code:**
```tsx
<Tooltip
  componentId="mlflow.genai-traces-table.actions-disabled-tooltip"
  content={intl.formatMessage({...})}
>
  {ActionButton}
</Tooltip>
```

**Potential fixes:**
1. **Wrap in a div:** Wrap the ActionButton in a div to handle the ref
2. **Use asChild pattern:** Use the `asChild` prop if Tooltip supports it
3. **Use forwardRef:** Ensure the Button component uses React.forwardRef()

**Recommended fix:**
```tsx
<Tooltip
  componentId="mlflow.genai-traces-table.actions-disabled-tooltip"
  content={intl.formatMessage({...})}
>
  <div>{ActionButton}</div>
</Tooltip>
```

### ✅ **IMPLEMENTATION COMPLETE**
**Date:** 2025-07-14
**File Modified:** `js/packages/web-shared/src/genai-traces-table/GenAITracesTableActions.tsx:143-163`
**Change:** Restructured conditional rendering to avoid ref forwarding issues (same fix as Error #4)
**Result:** Eliminates React.forwardRef() warning from console output

---

## Error #2: Duplicate React Keys Warning

**Error Type:** React Warning
**Severity:** Warning
**Status:** ✅ **FIXED**

### Error Message:
```
Warning: Encountered two children with the same key, `evaluation-monitoring`. Keys should be unique so that components maintain their identity across updates. Non-unique keys may cause children to be duplicated and/or omitted — the behavior is unsupported and could change in a future version.
```

### Location:
- **Component:** SegmentedControlGroup → TabSelectorBar → ExperimentPageHeaderWithDescription
- **Context:** Experiment page tabs navigation
- **Stack Trace Origins:**
  - `js_packages_visualization_index_css` (SegmentedControlGroup)
  - `mlflow_web_js_src_experiment-tracking_components_experiment-page_components_ExperimentViewDes-*` (TabSelectorBar)
  - `mlflow_web_js_src_experiment-tracking_pages_experiment-page-tabs_ExperimentPageTabs_tsx` (ExperimentPageHeaderWithDescription)

### Analysis:
This is a React warning caused by duplicate keys in the experiment page tab navigation. The key `evaluation-monitoring` is being used for two different children components in the same parent, which violates React's requirement for unique keys.

### Root Cause:
The TabSelectorBar component is generating duplicate keys for tab items, specifically for the "evaluation-monitoring" tab. This suggests that the tab configuration or rendering logic is creating multiple elements with the same key.

### Impact:
- Creates console noise that prevents Playwright MCP from reading console output
- Could cause UI rendering issues where tabs are duplicated or omitted
- Affects the experiment page navigation experience

### Recommended Action:
1. **Short-term:** Add unique suffixes to duplicate keys (e.g., `evaluation-monitoring-1`, `evaluation-monitoring-2`)
2. **Long-term:** Fix the tab rendering logic to ensure unique keys are generated
3. **Investigation needed:** Check the experiment page tab configuration and rendering

### Files to Investigate:
- `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/header/tab-selector-bar/TabSelectorBar.tsx` ✅ **FOUND**

### Solution Found:
The issue is in `TabSelectorBar.tsx` lines 114-166. The component renders two `Link` components for each tab:
1. One with className "tab-icon-text" 
2. One with className "tab-icon-with-tooltip"

Both were using the same `key={tabName}` which caused duplicate keys for "evaluation-monitoring" and other tabs.

### ✅ **IMPLEMENTATION COMPLETE**
**Date:** 2025-07-14  
**File Modified:** `mlflow/web/js/src/experiment-tracking/components/experiment-page/components/header/tab-selector-bar/TabSelectorBar.tsx:117,134`  
**Change:** 
- Line 117: Changed `key={tabName}` to `key={`${tabName}-text`}`
- Line 134: Changed `key={tabName}` to `key={`${tabName}-tooltip`}`

**Result:** Eliminates duplicate React keys warning by ensuring each Link component has a unique key

---

## Error #3: React.forwardRef() Warning (Second Instance)

**Error Type:** React Warning  
**Severity:** Warning  
**Status:** ✅ **FIXED**

### Error Message:
```
Warning: Function components cannot be given refs. Attempts to access this ref will fail. Did you mean to use React.forwardRef()?

Check the render method of `SlotClone`.
```

### Location:
- **Component:** TraceActionsDropdown (line 734) → GenAITracesTableActions (line 695)  
- **Context:** Same GenAI traces table actions but different instance
- **Stack Trace Origins:**
  - `js_packages_web-shared_src_genai-traces-table_GenAiTracesTableBody_tsx` (lines 734, 695)
  - `design-system_src_design-system_Tooltip_InfoTooltip_tsx` (line 243)

### Analysis:
This appears to be another instance of the same Tooltip ref forwarding issue, but at different line numbers in the same component. This suggests there are multiple Tooltip usages in the GenAITracesTableActions component that need fixing.

### Files to Investigate:
- `js/packages/web-shared/src/genai-traces-table/GenAITracesTableActions.tsx` - Check for other Tooltip instances

### ✅ **IMPLEMENTATION COMPLETE - REVERTED**
**Date:** 2025-07-14  
**Status:** ❌ **REVERTED** - These fixes were reverted because they used the wrong approach  
**Files Reverted:**
1. `js/packages/web-shared/src/genai-traces-table/GenAITracesTable.tsx:592` - Removed unnecessary div wrapper
2. `js/packages/web-shared/src/genai-traces-table/GenAiTracesTableBodyRows.tsx:116-123` - Removed unnecessary div wrapper  
3. `js/packages/web-shared/src/genai-traces-table/GenAITracesTableToolbar.tsx:185` - Removed unnecessary div wrapper

**Reason for Revert:** The div wrapper approach was incorrect. These components don't actually have ref forwarding issues - only the DropdownMenu.Trigger with asChild prop had the problem, which was properly fixed in Error #4.

**Result:** Only the actual problematic component (GenAITracesTableActions) uses the proper conditional rendering fix

---

## Error #4: React.forwardRef() Warning (DropdownMenu.Trigger)

**Error Type:** React Warning  
**Severity:** Warning  
**Status:** ✅ **FIXED**

### Error Message:
```
Warning: Function components cannot be given refs. Attempts to access this ref will fail. Did you mean to use React.forwardRef()?

Check the render method of `SlotClone`.
```

### Location:
- **Component:** TraceActionsDropdown (line 734) → GenAITracesTableActions (line 695)
- **Context:** DropdownMenu.Trigger with asChild prop trying to forward ref to Tooltip component
- **Stack Trace Origins:**
  - `js_packages_web-shared_src_genai-traces-table_GenAiTracesTableBody_tsx` (lines 734, 695)
  - `design-system_src_design-system_Tooltip_InfoTooltip_tsx` (line 243)

### Analysis:
The DropdownMenu.Trigger component with `asChild` prop is trying to forward a ref to the conditional content (Tooltip or ActionButton), but the Tooltip component doesn't properly handle ref forwarding. This is similar to the previous Tooltip ref forwarding issues.

### Root Cause:
The `DropdownMenu.Trigger` with `asChild` expects its child to be able to accept a ref, but the conditional rendering between Tooltip and ActionButton creates a mismatch in ref handling.

### ✅ **IMPLEMENTATION COMPLETE**
**Date:** 2025-07-14  
**File Modified:** `js/packages/web-shared/src/genai-traces-table/GenAITracesTableActions.tsx:143-163`  
**Change:** Restructured the conditional rendering to avoid ref forwarding issues by:
1. Moving the conditional logic outside of DropdownMenu.Trigger
2. When `noTracesSelected` is true: Tooltip wraps a div containing DropdownMenu.Trigger
3. When `noTracesSelected` is false: DropdownMenu.Trigger is used directly
4. This avoids the `asChild` prop trying to forward refs through conditional rendering

**Result:** Eliminates React.forwardRef() warning from DropdownMenu.Trigger component by properly handling the ref forwarding pattern

---

## Next Steps:
- Continue documenting additional console errors as they are provided
- Categorize errors by type (React warnings, console.log statements, actual errors)
- Prioritize fixes based on impact and frequency






## ALL ERRORS ARE IN raw-console.md