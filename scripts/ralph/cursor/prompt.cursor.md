# Ralph Agent Instructions (Cursor)

Autonomous coding agent. Use Cursor.

## Task

1. Read `scripts/ralph/prd.yml`
2. Read `progress.txt` (check Codebase Patterns first)
3. **Find current phase:**
   - PRD has `phases`: Find first phase (by phaseNumber) with `passes: false` story
   - No phases (legacy): Entire PRD = single phase, use top-level `branchName`
   - Work one phase at a time
4. **Checkout/create phase branch:**
   - Get phase `branchName`
   - Branch missing:
     - Phase 1: Create from current branch
     - Phase N (N > 1): Create from previous phase branch
   - Checkout phase branch
5. Pick highest priority story from current phase where `passes: false`
6. Implement that story
7. Run quality checks (typecheck, lint, test)
8. Update Cursor rules if reusable patterns found (see below)
9. Append progress to `progress.txt` (pass or fail)
10. If checks pass: 
   - Set story `passes: true` in PRD
   - Commit and push ALL with `feat: [Story ID] - [Story Title]`

## Progress Format

APPEND to progress.txt (never replace):
```
## [Date/Time] - [Story ID]
- What implemented
- Files changed
- **Learnings:**
  - Patterns (e.g., "codebase uses X for Y")
  - Gotchas (e.g., "update Z when changing W")
  - Context (e.g., "evaluation panel in component X")
---
```

Learnings section critical - helps future iterations avoid mistakes.

## Consolidate Patterns

Reusable pattern found? Add to `## Codebase Patterns` at TOP of progress.txt (create if missing):

```
## Codebase Patterns
- Use `sql<number>` template for aggregations
- Always use `IF NOT EXISTS` for migrations
- Export types from actions.ts for UI components
```

Only general/reusable patterns, not story-specific.

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
- Story-specific details
- Temporary debug notes
- Info already in progress.txt
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

UI story changes? Must verify in browser:

- Browser MCP tools available:
  1. Navigate to page
  2. Verify UI works
  3. Screenshot if helpful
- No browser MCP tools:
  - Ensure automated tests (Playwright, Cypress) cover UI
  - If tests not feasible: Mark "needs manual verification" in progress
  - Don't mark complete until verified

Frontend story NOT complete until browser verification passes (MCP tools or automated tests).

## Stop Condition

After story complete, check status:

1. **Current phase complete?**
   - All stories in phase have `passes: true`:
     - More phases with incomplete stories: Continue (next iteration handles)
     - Last phase: Check if ALL stories across ALL phases have `passes: true`
   
2. **ALL stories complete?**
   - Reply: `<promise>COMPLETE</promise>`
   
3. **Still incomplete stories?**
   - End normally (next iteration picks up)

**Phase transition:** Phase complete? Next iteration moves to next phase branch. Don't handle transitions in single iteration - just complete stories in current phase.

## Important

- ONE story per iteration
- **Only stories from current phase**
- **On correct phase branch before starting**
- **Phase branches: Phase 1 from current branch, Phase N from previous phase branch**
- Commit frequently
- Keep CI green
- Read Codebase Patterns in progress.txt first
- Use Cursor file editing
- Use `.cursor/rules/*` for repo conventions

## Phase Branch Management

- **Phase 1:** Create from current branch (whatever branch when starting Ralph)
- **Phase N (N > 1):** Create from previous phase branch
- Each phase = separate PR
- Phase branch = that phase work + previous phases as base
