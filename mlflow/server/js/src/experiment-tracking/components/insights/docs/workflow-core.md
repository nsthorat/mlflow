# Todo Workflow System - Core Process

Structured workflow for implementing items from `docs/todos.md`. Work isolation in `docs/work/`, completion tracking in `docs/done/`.

**Files:**
- **docs/todos.md** - Your todo list (simple bullet points)
- **docs/project-description.md** - Project context and features
- **docs/project-reference.md** - Detailed technical reference
- **docs/work/** - Active work folders
- **docs/done/** - Completed tasks
- **docs/workflow-troubleshooting.md** - Common issues and solutions

**CRITICAL**: Follow all steps in the workflow! Do not miss executing any steps!

## Phase 0: SETUP

1. **Read todos**: Read docs/todos.md in full using Read tool
   - If does not exist: STOP and tell user no docs/todos.md exists

2. **Read project description**: Read docs/project-description.md in full using Read tool
   - If missing, create it using Task agents to analyze codebase
   - Present proposed content to user for confirmation

3. **Verify dev environment**:
   - Check MLflow dev server: `ps aux | grep "yarn start --projects mlflow" | grep -v grep`
   - If not running: `nohup yarn start --projects mlflow > /tmp/mlflow_dev_server.log 2>&1 &`
   - Wait for: "dev-proxy for monolith,url-proxy started at [URL] 🚀"

4. **Check for orphaned tasks**:
   ```bash
   mkdir -p docs/work docs/done && orphaned_count=0 && for d in docs/work/*/task.md; do [ -f "$d" ] || continue; pid=$(grep "^**Agent PID:" "$d" | cut -d' ' -f3); [ -n "$pid" ] && ps -p "$pid" >/dev/null 2>&1 && continue; orphaned_count=$((orphaned_count + 1)); task_name=$(basename $(dirname "$d")); task_title=$(head -1 "$d" | sed 's/^# //'); echo "$orphaned_count. $task_name: $task_title"; done
   ```
   - If orphaned tasks exist, STOP: "Found orphaned task(s). What would you like to do? (resume <number|name> / reset <number|name> / ignore all)"

## Phase 1: SELECT

1. **Present todos**: Context-aware numbered summaries with priority indicators
   - HIGH: Critical features, dependencies for other work
   - MEDIUM: Feature enhancements, performance improvements  
   - LOW: Nice-to-have features, documentation updates

2. **Get user selection**: STOP: "Which todo would you like to work on? (enter number)"

3. **Initialize work folder**:
   - Generate folder name: `date +%Y-%m-%d-%H-%M-%S`-brief-task-title
   - Get agent PID: `echo $PPID`
   - Create docs/work/[task-folder-name]/task.md with initial content
   - Remove selected todo from docs/todos.md

## Phase 2: REFINE

1. **Refine Description**: Use Task agents to understand current functionality
   - Present description to user
   - STOP: "Use this description? (y/n)"

2. **Define implementation plan**: Use Task agents to investigate:
   - Where changes are needed
   - Available design system components
   - Existing trends components for reuse
   - SQL query patterns and validation
   - Present plan to user including **VERIFICATION PLAN**
   - STOP: "Use this implementation plan? (y/n)"

3. **Final confirmation**: Present full task.md content
   - STOP: "Use this description and implementation plan? (y/n)"
   - Update task.md with Status: "In Progress" and Started timestamp

## Phase 3: IMPLEMENT

1. **Execute implementation plan**:
   - Work through checkboxes sequentially
   - Update checkboxes as completed
   - Capture important findings in Notes

2. **Run complete code quality checks** (MUST run ALL, rerun ALL if any fail):
   - Dev server status verification
   - `yarn lint:fix` - Fix linting issues
   - `yarn prettier:fix` - Format code
   - `yarn type-check` - TypeScript validation
   - **TARGETED TESTS FIRST**: `yarn test src/experiment-tracking/components/experiment-page/components/traces-v3/trends` - Run your specific component tests first
   - `yarn i18n:extract` - Extract internationalization messages
   - `yarn knip` - Remove unused exports
   - Theme compliance check (no hardcoded pixels)
   - Analytics tracking verification
   - **CRITICAL**: If ANY check fails, fix issues and rerun ALL checks again starting with targeted tests

3. **Self-verification** (MANDATORY before user testing):
   - **ALWAYS verify UI changes yourself first using Playwright or manual testing**
   - Use Playwright browser automation to verify both success and error states render correctly
   - Take screenshots of different states if needed
   - Test responsive behavior at different screen sizes
   - Confirm no regressions in existing functionality
   - **NEVER ask user to test without doing self-verification first**

4. **Present user test steps with dev.local URLs** from implementation plan
   - Provide specific dev.local URLs for user testing
   - STOP: "Self-verification complete. Please run the user tests at the provided URLs. Do all tests pass? (y/n)"

## Phase 4: COMPLETE

1. **Show changes** for review (git diff via vs-claude)
2. **STOP**: "Ready to commit all changes? (y/n)"
3. **If approved**:
   - Create branch: `git checkout -b [descriptive-name]`
   - Commit changes: `git add . && git commit -m "[message]"`
   - Push: `git pp`
   - Create PR with structured description
   - Move task to done: `mv docs/work/[task-name]/task.md docs/done/[task-name].md`
4. **STOP**: "Task complete! Continue with next todo? (y/n)"

## Key Patterns

- **Component Reuse**: Always check trends/components/ first
- **SQL Validation**: Use execute_databricks_sql.py during planning
- **Theme Compliance**: Use theme.spacing, theme.colors (no pixels)
- **Analytics**: Add components to trendsLogging.ts
- **Card Architecture**: Use TrendsSliceCard for layouts