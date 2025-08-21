# Trends Todo System - User Guide

## Quick Commands

### Adding Todos
- **"Add todo item that [specific task]"**
- Examples: "Add todo item that implements user feedback analysis"
- Result: Added to `docs/todos.md` with priority and context

### Working on Todos  
- **"Work on todos"** - Starts structured workflow (Phase 0-4)
- **"Work on [specific todo]"** - Targets specific item
- Result: Guided through planning → implementation → completion

## The 4-Phase Workflow

**Phase 0: Setup** - Read todos, verify dev environment, check orphaned tasks
**Phase 1: Select** - Choose todo from prioritized list  
**Phase 2: Plan** - Research components, validate SQL, create implementation plan
**Phase 3: Implement** - Execute plan, run quality checks, user testing
**Phase 4: Complete** - Branch, commit, PR generation, move to done

## Example Usage

### Adding a Todo
```
You: "Add todo item that implements export functionality for charts"
Me: Added to Medium Priority in docs/todos.md with component dependencies and testing requirements.
```

### Working on a Todo
```
You: "Work on todos"
Me: [Shows prioritized list with status indicators]
    HIGH: 1. Complete Quality Metrics ⚠️ (partially implemented)
    MEDIUM: 2. Export Chart Functionality (enhancement)
You: "1"
Me: [Follows Phase 0-4: Setup → Plan → Implement → Complete]
```

## Key Patterns

### Commands
- **"Add todo..."** - Adds to docs/todos.md
- **"Work on todos"** - Starts 4-phase workflow
- **"y/n"** during workflow - Approve/reject plans
- **Numbers** - Select from lists

### Best Practices
- Be specific when adding todos
- Have dev server running before starting work
- Review generated PR descriptions carefully

### File Structure Reference
- **todos.md** - Your todo list
- **workflow-core.md** - Phase 0-4 process
- **workflow-troubleshooting.md** - Issue resolution
- **work/** - Active work tracking
- **done/** - Completed tasks

**Getting Started**: "What's the project status?" → "Add todo item that..." → "Work on todos"