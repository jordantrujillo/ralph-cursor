# Ralph PRD to Beads Converter

Converts existing PRDs to Beads issues that Ralph uses for autonomous execution.

---

## The Job

Take a PRD (markdown file or text) and convert it to Beads issues using `bd` commands.

---

## Beads Commands Reference

- `bd epic create <title> [--description TEXT] [--parent EPIC_ID]` - Create an epic
- `bd task create <title> [--description TEXT] [--parent EPIC_ID] [--priority NUMBER]` - Create a task
- `bd note <ISSUE_ID> "text"` - Add metadata/notes to an issue
- `bd dep add <CHILD_ID> <PARENT_ID>` - Add dependency (child depends on parent)
- `bd show <ISSUE_ID>` - Show issue details
- `bd list [--type epic|task] [--parent EPIC_ID] [--status open|closed]` - List issues

---

## Conversion Process

### 1. Create Project Epic (Top-Level)

Create the project epic first:

```bash
bd epic create "<Project Name>" --description "<Project description>"
```

Store branch name in notes:
```bash
bd note <project-epic-id> "branch: ralph/feature-name-kebab-case"
```

### 2. Create Phase Epics

For each phase, create a phase epic with parent = project epic:

```bash
bd epic create "Phase N: <Phase Description>" --description "<Phase description>" --parent <project-epic-id>
```

Store phase branch name in notes:
```bash
bd note <phase-epic-id> "branch: ralph/feature-name-phase-N"
```

### 3. Create Tasks (User Stories)

**CRITICAL: Create tasks in priority order (ascending by priority number)**

Lower priority number = higher priority = create first.

For each user story (sorted by priority, ascending):

```bash
bd task create "<Story ID>: <Story Title>" --description "<Story description>

Acceptance Criteria:
- Criterion 1
- Criterion 2
- Typecheck passes" --parent <phase-epic-id> --priority <priority-number>
```

Store story ID in notes:
```bash
bd note <task-id> "story-id: US-001"
```

### 4. Set Up Dependencies

**CRITICAL: Priority-based dependencies**

After creating all tasks in a phase, set up dependencies based on priority:
- Lower priority number tasks depend on higher priority number tasks
- Example: If US-002 has priority 2 and US-001 has priority 1, then: `bd dep add <US-002-task-id> <US-001-task-id>`
- This ensures `bd ready` shows tasks in correct development order

For each task (except the first), add dependency on the previous task:
```bash
bd dep add <current-task-id> <previous-task-id>
```

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
"Verify in browser using browser MCP tools"
```

Frontend stories are NOT complete until visually verified. Ralph will use browser MCP tools (if configured) to navigate to the page, interact with the UI, and confirm changes work.

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
   - **If PRD has phases:** Group stories by phase, create one phase epic per PRD phase
   - **If PRD has no phases BUT has 6+ stories:** Automatically split into logical phases:
     - Group by dependency order (schema → backend → UI)
     - Group by codebase area (database → API → frontend)
     - Aim for 3-6 stories per phase
     - Create phase names like "Phase 1: Database & Core Logic", "Phase 2: API Endpoints", "Phase 3: UI Components"
   - **If PRD has no phases AND has 5 or fewer stories:** Create a single phase epic with all stories

2. **Each user story becomes one Beads task** within its phase epic
3. **IDs**: Sequential across all phases (US-001, US-002, etc.) - maintain global sequence
4. **Priority**: Within each phase, based on dependency order. Priority resets per phase (starts at 1)
5. **All tasks**: Created as open (not closed)
6. **branchName**: 
   - Top-level branch: Base feature branch (e.g., `ralph/feature-name`)
   - Phase branch: Phase-specific branch (e.g., `ralph/feature-name-phase-1`)
   - For single-phase PRDs, both can be the same
7. **Always add**: "Typecheck passes" to every task's acceptance criteria
8. **Phase branches:** Each phase branch is built on top of the previous phase's branch (or main for phase 1)

---

## Priority Organization (CRITICAL)

**Tasks must be organized by priority - what needs to be developed first.**

- Lower priority number = higher priority = should be created first
- Create tasks in priority order (ascending by priority number)
- Set up dependencies: lower priority number tasks depend on higher priority number tasks (priority 2 depends on priority 1)
- This ensures `bd ready` will show tasks in the correct development order

**Example:**
- Priority 1 task: Create database migration
- Priority 2 task: Create API endpoint (depends on priority 1)
- Priority 3 task: Create UI component (depends on priority 2)

Dependencies: `bd dep add <priority-2-task-id> <priority-1-task-id>`, `bd dep add <priority-3-task-id> <priority-2-task-id>`

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

**Output Beads Commands:**

```bash
# Create project epic
PROJECT_EPIC=$(bd epic create "TaskApp" --description "Task Status Feature - Track task progress with status indicators")
bd note $PROJECT_EPIC "branch: ralph/task-status"

# Create phase epic
PHASE_EPIC=$(bd epic create "Phase 1: Task Status Feature" --description "Task Status Feature - Track task progress with status indicators" --parent $PROJECT_EPIC)
bd note $PHASE_EPIC "branch: ralph/task-status"

# Create tasks in priority order
TASK1=$(bd task create "US-001: Add status field to tasks table" --description "As a developer, I need to store task status in the database.

Acceptance Criteria:
- Add status column: 'pending' | 'in_progress' | 'done' (default 'pending')
- Generate and run migration successfully
- Typecheck passes" --parent $PHASE_EPIC --priority 1)
bd note $TASK1 "story-id: US-001"

TASK2=$(bd task create "US-002: Display status badge on task cards" --description "As a user, I want to see task status at a glance.

Acceptance Criteria:
- Each task card shows colored status badge
- Badge colors: gray=pending, blue=in_progress, green=done
- Typecheck passes
- Verify in browser using browser MCP tools" --parent $PHASE_EPIC --priority 2)
bd note $TASK2 "story-id: US-002"
bd dep add $TASK2 $TASK1  # Priority 2 depends on priority 1

TASK3=$(bd task create "US-003: Add status toggle to task list rows" --description "As a user, I want to change task status directly from the list.

Acceptance Criteria:
- Each row has status dropdown or toggle
- Changing status saves immediately
- UI updates without page refresh
- Typecheck passes
- Verify in browser using browser MCP tools" --parent $PHASE_EPIC --priority 3)
bd note $TASK3 "story-id: US-003"
bd dep add $TASK3 $TASK2  # Priority 3 depends on priority 2

TASK4=$(bd task create "US-004: Filter tasks by status" --description "As a user, I want to filter the list to see only certain statuses.

Acceptance Criteria:
- Filter dropdown: All | Pending | In Progress | Done
- Filter persists in URL params
- Typecheck passes
- Verify in browser using browser MCP tools" --parent $PHASE_EPIC --priority 4)
bd note $TASK4 "story-id: US-004"
bd dep add $TASK4 $TASK3  # Priority 4 depends on priority 3
```

---

## Checklist Before Completing

Before finishing the conversion, verify:

- [ ] **Phases structure used** (even for single-phase PRDs)
- [ ] **Auto-split applied if needed:** If PRD has 6+ stories without phases, automatically created phases
- [ ] **If PRD has phases:** Stories grouped correctly by phase
- [ ] **If PRD has phases:** Each phase has unique branch name in notes
- [ ] **Phase sizes reasonable:** Each phase has 3-6 stories (not too large for review)
- [ ] Each story is completable in one iteration (small enough)
- [ ] Stories are ordered by dependency (schema to backend to UI)
- [ ] **Tasks created in priority order** (ascending by priority number)
- [ ] **Dependencies set up correctly** (lower priority number tasks depend on higher priority number tasks)
- [ ] Every story has "Typecheck passes" as criterion
- [ ] UI stories have "Verify in browser using browser MCP tools" as criterion
- [ ] Acceptance criteria are verifiable (not vague)
- [ ] No story depends on a later story
- [ ] Story IDs are sequential across all phases (US-001, US-002, etc.)
- [ ] Branch names stored in epic notes
- [ ] Story IDs stored in task notes

---

## Verification

After conversion, verify the structure:

```bash
# List project epics
bd list --type epic

# List phase epics
bd list --type epic --parent <project-epic-id>

# List ready tasks (should show tasks in priority order)
bd ready --parent <phase-epic-id>

# Show task details
bd show <task-id>
```
