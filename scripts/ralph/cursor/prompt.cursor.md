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
8. Update AGENTS.md if reusable patterns found (see below)
9. If checks pass: 
   - Set story `passes: true` in PRD
   - Append progress to `progress.txt`
   - Commit ALL with `feat: [Story ID] - [Story Title]`, attempt to push to remote branch, do not try again if fails.

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

## Update AGENTS.md

Before commit, check edited files for learnings:

1. Find directories with edited files
2. Check for AGENTS.md in those/parent directories
3. Add valuable learnings:
   - API patterns/conventions for that module
   - Gotchas/non-obvious requirements
   - File dependencies
   - Testing approaches
   - Config/env requirements

**Good AGENTS.md additions:**
- "Modifying X requires updating Y"
- "Module uses pattern Z for API calls"
- "Tests need dev server on PORT 3000"
- "Field names must match template exactly"

**Don't add:**
- Story-specific details
- Temporary debug notes
- Info already in progress.txt

Only update if genuinely reusable knowledge for future work.

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
