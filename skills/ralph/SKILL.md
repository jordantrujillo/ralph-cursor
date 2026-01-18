---
name: ralph
description: "Convert PRDs to prd.yml format for the Ralph autonomous agent system. Use when you have an existing PRD and need to convert it to Ralph's YAML format. Triggers on: convert this prd, turn this into ralph format, create prd.yml from this, ralph yaml."
---

# Ralph PRD Converter

Converts existing PRDs to the prd.yml format that Ralph uses for autonomous execution.

---

## The Job

Take a PRD (markdown file or text) and convert it to `scripts/ralph/prd.yml`.

---

## Output Format

**For PRDs without phases (single phase):**
```yaml
project: MyApp
branchName: ralph/feature-name-kebab-case
description: Feature description from PRD title/intro
phases:
  - phaseNumber: 1
    branchName: ralph/feature-name-kebab-case
    description: Phase description (or same as main description)
    userStories:
      - id: US-001
        title: Story title
        description: As a user, I want feature so that benefit
        acceptanceCriteria:
          - Criterion 1
          - Criterion 2
          - Typecheck passes
        priority: 1
        passes: false
        notes: 
```

**For PRDs with phases:**
```yaml
project: MyApp
branchName: ralph/feature-name-kebab-case
description: Feature description from PRD title/intro
phases:
  - phaseNumber: 1
    branchName: ralph/feature-name-phase-1
    description: Phase 1 description
    userStories:
      - id: US-001
        title: Story title
        description: As a user, I want feature so that benefit
        acceptanceCriteria:
          - Criterion 1
          - Criterion 2
          - Typecheck passes
        priority: 1
        passes: false
        notes: 
  - phaseNumber: 2
    branchName: ralph/feature-name-phase-2
    description: Phase 2 description
    userStories:
      - id: US-005
        title: Story title
        description: As a user, I want feature so that benefit
        acceptanceCriteria:
          - Criterion 1
          - Criterion 2
          - Typecheck passes
        priority: 1
        passes: false
        notes: 
```

**Important:** Always use the `phases` structure, even for single-phase PRDs. This ensures consistency.

**Important: Do NOT use quotes around YAML values unless necessary.** Quotes are only needed for:
- Strings starting with special characters like `@`, `*`, `&`, `!`, `|`, `>`, `%`
- Strings containing colons followed by spaces (e.g., `key: value` as a string value)
- Strings that would be interpreted as numbers/booleans/null (e.g., `"true"`, `"123"`, `"null"`)
- Empty strings (use `notes: ` without quotes instead of `notes: ""`)

For normal text values, omit quotes to save tokens.

---

## Story Size: The Number One Rule

**Each story must be completable in ONE Ralph iteration (one context window).**

Ralph spawns a fresh Cursor instance per iteration with no memory of previous work. If a story is too big, the LLM runs out of context before finishing and produces broken code.

### Right-sized stories:
- Add a database column and migration
- Add a UI component to an existing page
- Update a server action with new logic
- Add a filter dropdown to a list

### Too big (split these):
- "Build the entire dashboard" - Split into: schema, queries, UI components, filters
- "Add authentication" - Split into: schema, middleware, login UI, session handling
- "Refactor the API" - Split into one story per endpoint or pattern

**Rule of thumb:** If you cannot describe the change in 2-3 sentences, it is too big.

---

## Story Ordering: Dependencies First

Stories execute in priority order. Earlier stories must not depend on later ones.

**Correct order:**
1. Schema/database changes (migrations)
2. Server actions / backend logic
3. UI components that use the backend
4. Dashboard/summary views that aggregate data

**Wrong order:**
1. UI component (depends on schema that does not exist yet)
2. Schema change

---

## Acceptance Criteria: Must Be Verifiable

Each criterion must be something Ralph can CHECK, not something vague.

### Good criteria (verifiable):
- "Add `status` column to tasks table with default 'pending'"
- "Filter dropdown has options: All, Active, Completed"
- "Clicking delete shows confirmation dialog"
- "Typecheck passes"
- "Tests pass"

### Bad criteria (vague):
- "Works correctly"
- "User can do X easily"
- "Good UX"
- "Handles edge cases"

### Always include as final criterion:
```
"Typecheck passes"
```

For stories with testable logic, also include:
```
"Tests pass"
```

### For stories that change UI, also include:
```
"Verify in browser using dev-browser skill"
```

Frontend stories are NOT complete until visually verified. Ralph will use the dev-browser skill to navigate to the page, interact with the UI, and confirm changes work.

---

## Automatic Phase Creation

When converting a PRD without phases, **automatically create phases if the PRD has 6+ user stories**. Use these heuristics:

### Phase Grouping Strategies

1. **By Dependency Order (Most Common):**
   - Phase 1: Database/schema changes, migrations
   - Phase 2: Backend services, API endpoints, server actions
   - Phase 3: UI components, pages, frontend integration
   - Phase 4: Advanced features, polish, optimization

2. **By Codebase Area:**
   - Phase 1: Backend changes (database, services, APIs)
   - Phase 2: Frontend changes (components, pages, UI)
   - Phase 3: Integration and testing

3. **By Feature Completeness:**
   - Phase 1: Core functionality (MVP)
   - Phase 2: Additional features
   - Phase 3: Polish and edge cases

### Phase Naming

Use descriptive names:
- `Phase 1: Database & Core Logic`
- `Phase 2: API Endpoints`
- `Phase 3: UI Components`
- `Phase 4: Advanced Features`

### Branch Naming

- Phase 1: `ralph/[feature-name]-phase-1`
- Phase 2: `ralph/[feature-name]-phase-2`
- etc.

### Example Auto-Split

**Input:** PRD with 8 stories, no phases
- Stories: DB migration, model, service, API endpoint 1, API endpoint 2, UI list, UI detail, UI edit

**Output:** 3 phases
- Phase 1 (3 stories): DB migration, model, service
- Phase 2 (2 stories): API endpoint 1, API endpoint 2
- Phase 3 (3 stories): UI list, UI detail, UI edit

---

## Conversion Rules

1. **Auto-detect if phases are needed:**
   - **If PRD has phases:** Group stories by phase, create one phase entry per PRD phase
   - **If PRD has no phases BUT has 6+ stories:** Automatically split into logical phases:
     - Group by dependency order (schema → backend → UI)
     - Group by codebase area (database → API → frontend)
     - Aim for 3-6 stories per phase
     - Create phase names like "Phase 1: Database & Core Logic", "Phase 2: API Endpoints", "Phase 3: UI Components"
   - **If PRD has no phases AND has 5 or fewer stories:** Create a single phase (phaseNumber: 1) with all stories

2. **Each user story becomes one YAML entry** within its phase
3. **IDs**: Sequential across all phases (US-001, US-002, etc.) - maintain global sequence
4. **Priority**: Within each phase, based on dependency order. Priority resets per phase (starts at 1)
5. **All stories**: `passes: false` and empty `notes`
6. **branchName**: 
   - Top-level `branchName`: Base feature branch (e.g., `ralph/feature-name`)
   - Phase `branchName`: Phase-specific branch (e.g., `ralph/feature-name-phase-1`)
   - For single-phase PRDs, both can be the same
7. **Always add**: "Typecheck passes" to every story's acceptance criteria
8. **Phase branches:** Each phase branch is built on top of the previous phase's branch (or main for phase 1)

---

## Splitting Large PRDs

If a PRD has big features, split them into phases:

**Original:**
> "Add user notification system" (8 stories)

**Split into phases:**
**Phase 1: Database & Core Service**
1. US-001: Add notifications table to database
2. US-002: Create notification service for sending notifications
3. US-003: Add notification model and types

**Phase 2: UI Components**
4. US-004: Add notification bell icon to header
5. US-005: Create notification dropdown panel
6. US-006: Add mark-as-read functionality

**Phase 3: Advanced Features**
7. US-007: Add notification preferences page
8. US-008: Add notification filtering and sorting

Each phase is a focused, reviewable unit. Each story is one focused change that can be completed and verified independently.

**Auto-splitting guidelines:**
- If you see 6+ stories without phases, automatically create phases
- Group by dependency (database → service → UI)
- Group by codebase area (backend → frontend)
- Aim for 3-6 stories per phase

---

## Example

**Input PRD:**
```markdown
# Task Status Feature

Add ability to mark tasks with different statuses.

## Requirements
- Toggle between pending/in-progress/done on task list
- Filter list by status
- Show status badge on each task
- Persist status in database
```

**Output prd.yml (single phase example):**
```yaml
project: TaskApp
branchName: ralph/task-status
description: Task Status Feature - Track task progress with status indicators
phases:
  - phaseNumber: 1
    branchName: ralph/task-status
    description: Task Status Feature - Track task progress with status indicators
    userStories:
      - id: US-001
        title: Add status field to tasks table
        description: As a developer, I need to store task status in the database.
        acceptanceCriteria:
          - Add status column: 'pending' | 'in_progress' | 'done' (default 'pending')
          - Generate and run migration successfully
          - Typecheck passes
        priority: 1
        passes: false
        notes: 
      - id: US-002
        title: Display status badge on task cards
        description: As a user, I want to see task status at a glance.
        acceptanceCriteria:
          - Each task card shows colored status badge
          - Badge colors: gray=pending, blue=in_progress, green=done
          - Typecheck passes
          - Verify in browser using dev-browser skill
        priority: 2
        passes: false
        notes: 
      - id: US-003
        title: Add status toggle to task list rows
        description: As a user, I want to change task status directly from the list.
        acceptanceCriteria:
          - Each row has status dropdown or toggle
          - Changing status saves immediately
          - UI updates without page refresh
          - Typecheck passes
          - Verify in browser using dev-browser skill
        priority: 3
        passes: false
        notes: 
      - id: US-004
        title: Filter tasks by status
        description: As a user, I want to filter the list to see only certain statuses.
        acceptanceCriteria:
          - Filter dropdown: All | Pending | In Progress | Done
          - Filter persists in URL params
          - Typecheck passes
          - Verify in browser using dev-browser skill
        priority: 4
        passes: false
        notes: 
```

---

## Archiving Previous Runs

**Before writing a new prd.yml, check if there is an existing one from a different feature:**

1. Read the current `prd.yml` if it exists
2. Check if `branchName` differs from the new feature's branch name
3. If different AND `progress.txt` has content beyond the header:
   - Create archive folder: `archive/YYYY-MM-DD-feature-name/`
   - Copy current `prd.yml` and `progress.txt` to archive
   - Reset `progress.txt` with fresh header

**The ralph.py script handles this automatically** when you run it, but if you are manually updating prd.yml between runs, archive first.

---

## Checklist Before Saving

Before writing prd.yml, verify:

- [ ] **Previous run archived** (if prd.yml exists with different branchName, archive it first)
- [ ] **Phases structure used** (even for single-phase PRDs)
- [ ] **Auto-split applied if needed:** If PRD has 6+ stories without phases, automatically created phases
- [ ] **If PRD has phases:** Stories grouped correctly by phase
- [ ] **If PRD has phases:** Each phase has unique branchName
- [ ] **Phase sizes reasonable:** Each phase has 3-6 stories (not too large for review)
- [ ] Each story is completable in one iteration (small enough)
- [ ] Stories are ordered by dependency (schema to backend to UI)
- [ ] Every story has "Typecheck passes" as criterion
- [ ] UI stories have "Verify in browser using dev-browser skill" as criterion
- [ ] Acceptance criteria are verifiable (not vague)
- [ ] No story depends on a later story
- [ ] Story IDs are sequential across all phases (US-001, US-002, etc.)
