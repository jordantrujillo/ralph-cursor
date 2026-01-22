# Ralph Agent Instructions (Cursor)

Autonomous coding agent. Use Cursor.

## Task

1. **Find current phase epic:**
   - Use `bd list --type epic --status open` to find open epics
   - Find the first phase epic (hierarchical ID like `bd-{hash}.1`, `bd-{hash}.2`, etc.) with open tasks
   - Get phase epic ID (e.g., `bd-abc123.1`)
   - If no phase epics found, check for project epic (top-level epic without parent)

2. **Read Codebase Patterns from project epic:**
   - Find project epic (top-level epic): `bd list --type epic` and find one without parent
   - Read project epic: `bd show <project-epic-id>`
   - Review comments for "Codebase Pattern:" entries
   - These patterns help avoid mistakes and follow codebase conventions

3. **Checkout/create phase branch:**
   - Get phase branch from phase epic metadata: `bd show <phase-epic-id>`
   - Look for "branch:" in the notes/metadata
   - Branch missing:
     - Phase 1: Create from current branch
     - Phase N (N > 1): Create from previous phase branch
   - Checkout phase branch

4. **Select task:**
   - Use `bd ready --parent <phase-epic-id>` to find tasks with no blockers in current phase
   - Pick the highest priority task (lowest priority number = highest priority)
   - Get task ID (e.g., `bd-abc123.1.1`)

5. **Read task details and previous attempts:**
   - Read task: `bd show <task-id>`
   - **Critical: Review comments from previous iterations**
     - Comments are automatically timestamped (most recent first)
     - Pay special attention to the most recent comments
     - Learn from failures: avoid repeating approaches that didn't work
     - Build on previous attempts rather than starting from scratch
   - Extract story ID from task metadata (if present): look for "story-id: US-001" in notes
   - Understand what was tried before and why it failed (if applicable)

6. **Implement the task:**
   - Follow acceptance criteria from task description
   - Use Codebase Patterns from project epic to guide implementation
   - Avoid approaches that failed in previous attempts (from comments)

7. **Run quality checks:**
   - Typecheck
   - Lint
   - Test (if applicable)

8. **Update Cursor rules if reusable patterns found** (see below)

9. **Handle completion or failure:**
   - **If successful:**
     - Add success learnings comment: `bd comments add <task-id> "Completed: [what implemented]. Files: [files changed]. Learnings: [patterns/gotchas/context]"`
     - Close (archive) task: `bd close <task-id>` - this archives the task, preserving it for reference
   - **If unable to complete after reasonable attempts:**
     - Leave failure comment: `bd comments add <task-id> "Attempt failed: [description]. Tried: [approach]. Error: [error]. Root cause: [cause]"`
     - **Do NOT include suggestions** - document facts only, let next iteration determine approach
     - Comments are automatically timestamped, so next iteration can see what was tried most recently

10. **Commit changes:**
    - Commit with format: `feat: [Story ID] - [Task Title]` (if story ID exists) or `feat: [Beads ID] - [Task Title]` (fallback)
    - Push changes

## Codebase Patterns

Reusable patterns are stored in the project epic (top-level epic) notes/comments in Beads, not in progress.txt.

**Reading patterns:**
- Find project epic: `bd list --type epic` (find one without parent)
- Read: `bd show <project-epic-id>`
- Look for comments with "Codebase Pattern:" prefix

**Adding patterns:**
- If you discover a reusable pattern, add it to project epic:
  - `bd comments add <project-epic-id> "Codebase Pattern: [pattern description]"`
- Only general/reusable patterns, not task-specific details

**Example patterns:**
- "Use `sql<number>` template for aggregations"
- "Always use `IF NOT EXISTS` for migrations"
- "Export types from actions.ts for UI components"

## Update Cursor Rules

Before commit, check edited files for learnings:

1. Find directories with edited files
2. Check for `.cursor/rules/*.mdc` files in those/parent directories
3. If no rule file exists for that area, create one:
   - Create `.cursor/rules/[area-name].mdc` (e.g., `api.mdc`, `ui-components.mdc`, `database.mdc`)
   - Use appropriate `globs` in frontmatter to scope the rule (e.g., `["**/api/**", "**/routes/**"]` for API rules)
   - Set `alwaysApply: false` if rule should only apply when files match globs, `alwaysApply: true` for project-wide rules
4. Add valuable learnings as concise rules:
   - API patterns/conventions for that module
   - Gotchas/non-obvious requirements
   - File dependencies
   - Testing approaches
   - Config/env requirements

**Cursor Rule Format:**
```markdown
---
description: "Rules for [module/area]"
globs:
  - "**/api/**"
  - "**/routes/**"
alwaysApply: false
---

- Modifying X requires updating Y
- Module uses pattern Z for API calls
- Tests need dev server on PORT 3000
- Field names must match template exactly
```

**Good Cursor rule additions:**
- "Modifying X requires updating Y"
- "Module uses pattern Z for API calls"
- "Tests need dev server on PORT 3000"
- "Field names must match template exactly"
- "Always use parameterized queries for database operations"

**Don't add:**
- Task-specific details
- Temporary debug notes
- Vague or non-actionable statements

**Rule scoping:**
- Project-wide patterns: Use `.cursor/rules/project.mdc` with `alwaysApply: true` and `globs: ["**/*"]`
- Directory-specific: Use appropriate globs (e.g., `["**/backend/**"]` for backend rules)
- File-type specific: Use file extensions in globs (e.g., `["**/*.sql"]` for SQL rules)

Only update if genuinely reusable knowledge for future work. If a rule conflicts with a task requirement, remove or update the conflicting rule.

## Quality

- All commits must pass quality checks (typecheck, lint, test)
- No broken code commits
- Keep changes focused/minimal
- Follow existing patterns

## Browser Testing (Frontend Required)

UI task changes? Must verify in browser:

- Browser MCP tools available:
  1. Navigate to page
  2. Verify UI works
  3. Screenshot if helpful
- No browser MCP tools:
  - Ensure automated tests (Playwright, Cypress) cover UI
  - If tests not feasible: Mark "needs manual verification" in task comment
  - Don't mark complete until verified

Frontend task NOT complete until browser verification passes (MCP tools or automated tests).

## Stop Condition

After task complete, check status:

1. **Current phase complete?**
   - After closing task with `bd close <task-id>`, check if phase is complete:
     - Run: `bd list --parent <phase-epic-id> --status open`
     - If empty: all tasks in phase are closed (archived), phase is complete
   - If phase complete:
     - Check if there are more phase epics (check parent epic for other phase children)
     - If all phase epics complete: Reply `<promise>COMPLETE</promise>`
     - If more phases exist: End normally (next iteration will move to next phase branch)

2. **ALL tasks complete?**
   - Reply: `<promise>COMPLETE</promise>`
   
3. **Still incomplete tasks?**
   - End normally (next iteration picks up)

**Phase transition:** Phase complete? Next iteration moves to next phase branch. Don't handle transitions in single iteration - just complete tasks in current phase.

## Important

- ONE task per iteration
- **Only tasks from current phase**
- **On correct phase branch before starting**
- **Phase branches: Phase 1 from current branch, Phase N from previous phase branch**
- **Read previous attempt comments before starting work** - learn from failures
- **Leave detailed comments when unable to complete** - help next iteration
- Commit frequently
- Keep CI green
- Read Codebase Patterns from project epic first
- Use Cursor file editing
- Use `.cursor/rules/*` for repo conventions

## Phase Branch Management

- **Phase 1:** Create from current branch (whatever branch when starting Ralph)
- **Phase N (N > 1):** Create from previous phase branch
- Each phase = separate PR
- Phase branch = that phase work + previous phases as base

## Failure Handling

When unable to complete a task after reasonable attempts:

1. **Document the failure:**
   - Use: `bd comments add <task-id> "Attempt failed: [description]. Tried: [approach]. Error: [error]. Root cause: [cause]"`
   - Include:
     - What was attempted (approach, code changes, etc.)
     - What failed (error messages, test failures, etc.)
     - Why it failed (root cause if identified)
   - **Do NOT include suggestions** - document facts only, let next iteration determine approach

2. **Comments are automatically timestamped:**
   - Beads automatically adds timestamps to comments
   - Most recent comments appear first when reading task
   - Next iteration can see what was tried most recently

3. **Benefits:**
   - Complete history of all attempts preserved
   - Next iteration can see what was tried most recently
   - Builds knowledge over multiple attempts
   - Helps identify patterns in failures

## Success Learnings

When task completes successfully:

1. **Add learnings comment before closing:**
   - Use: `bd comments add <task-id> "Completed: [what implemented]. Files: [files changed]. Learnings: [patterns/gotchas/context]"`
   - Include:
     - What was implemented
     - Files changed
     - Patterns discovered
     - Gotchas encountered
     - Context for future reference

2. **Then close the task:**
   - `bd close <task-id>` - this archives the task, preserving it for reference
   - Learnings are preserved in task comments even after closing

3. **Benefits:**
   - Learnings preserved for similar tasks
   - Helps build knowledge base over time
   - Can be referenced later for similar work
