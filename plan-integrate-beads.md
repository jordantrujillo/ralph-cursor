---
name: Integrate Beads Issue Tracker
overview: Replace the YAML-based prd.yml system with Beads, a git-backed graph issue tracker. This will provide dependency tracking, better merge conflict handling, and a more structured approach to task management for Ralph.
todos:
  - id: check-beads-availability
    content: Add Beads CLI availability check to ralph.py initialization
    status: done
  - id: update-ralph-branch-reading
    content: Replace _get_branch_name() in ralph.py to read from Beads metadata instead of YAML
    status: done
  - id: update-ralph-archive-logic
    content: Update _archive_previous_run() to work with Beads structure instead of prd.yml
    status: done
  - id: update-cursor-prompt
    content: "Replace prd.yml and progress.txt reading in prompt.cursor.md with Beads commands (bd ready, bd show, bd close). Add failure comment handling: read previous attempt comments (timestamped) before starting, leave detailed comments using bd update --comment when unable to complete task. Store Codebase Patterns in project epic notes."
    status: done
  - id: remove-progress-txt
    content: Remove all progress.txt references from ralph.py (progress_file, _initialize_progress_file, archive logic). Remove progress.txt from .gitignore.
    status: done
  - id: create-migration-script
    content: Create migrate-prd-to-beads.py to convert existing prd.yml files to Beads issues. Organize tasks by priority (create in priority order, set up dependencies based on priority).
    status: done
  - id: create-beads-converter
    content: Create convert-to-beads.sh to replace convert-to-prd-yml.sh. Organize tasks by priority (create in priority order, set up dependencies based on priority).
    status: done
  - id: update-ralph-init
    content: Add Beads initialization check to bin/ralph.py init command
    status: done
  - id: update-agents-md
    content: Update AGENTS.md to document Beads workflow instead of prd.yml, remove progress.txt references
    status: done
  - id: update-readme
    content: Update README.md with Beads examples, remove prd.yml and progress.txt references
    status: done
  - id: update-cursor-command
    content: Rename and update .cursor/commands/prd-to-yml.md to prd-to-beads.md. Ensure it instructs to organize tasks by priority (what needs to be developed first) and set up dependencies accordingly.
    status: done
---

# Beads Integration Plan

## Overview

Replace the current `prd.yml` YAML-based task tracking with Beads, a distributed git-backed graph issue tracker. This provides dependency tracking, hierarchical task organization, and better conflict resolution for multi-agent workflows.

## Architecture Changes

### Current System

- `prd.yml` - YAML file with phases and user stories
- Stories tracked with `passes: true/false` boolean
- Branch names stored in YAML
- No dependency tracking between stories

### New System (Beads)

- `.beads/` directory - Git-backed JSONL storage
- Hierarchical IDs: `bd-{hash}` for epics, `bd-{hash}.{n}` for tasks
- Dependency graph via `bd dep add`
- Branch names stored in Beads issue metadata
- Status tracking via Beads open/closed states

## Implementation Strategy

### Phase 1: Core Integration

**1.1 Update `ralph.py` to use Beads**

- Replace `_get_branch_name()` to read from Beads instead of YAML
  - Use `bd show <epic-id>` to get branch name from metadata
- Replace PRD file checking with Beads initialization check
- Remove `progress_file` references - no longer needed (everything in Beads)
- Update `_archive_previous_run()` to work with Beads structure (remove progress.txt archiving)
- Remove `_initialize_progress_file()` method
- Add Beads command availability check in `__init__`

**1.2 Update `prompt.cursor.md`**

- Remove "Read `scripts/ralph/prd.yml`" and "Read `progress.txt`" - replace with Beads commands
- Replace story selection logic:
  - Old: "Pick highest priority story from current phase where `passes: false`"
  - New: "Use `bd ready` to find tasks with no blockers in current phase epic"
- **Add task selection and learning:**
  - Before starting work on a task, read existing comments: `bd show <task-id>`
  - Review comments from previous iterations (comments are timestamped, showing most recent attempts first)
  - Use this context to understand what was tried last and avoid repeating failed approaches
  - Read Codebase Patterns from project epic notes (stored in Beads, not progress.txt)
- Replace status updates:
  - Old: "Set story `passes: true` in PRD"
  - New: "Close (archive) task with `bd close <task-id>` if successful - closing archives the task, preserving it for reference"
- **Add failure handling:**
  - If unable to complete task after reasonable attempts, leave a comment in Beads:
    - Use `bd update <task-id> --comment "text"` to add a comment (comments are automatically timestamped and append-only)
    - Include: what was attempted, what failed, error messages, why it failed
    - Do NOT include suggestions of what to try next - let the next iteration figure out the approach
    - Format: `Attempt failed: [description]. Tried: [approach]. Error: [error]. Root cause: [cause]`
    - Comments are automatically timestamped, so the next agent can see what was tried most recently
- **Add success learnings:**
  - When task completes successfully, add a comment with learnings:
    - Use `bd update <task-id> --comment "text"` to add learnings before closing
    - Include: what was implemented, files changed, patterns discovered, gotchas, context
    - Format: `Completed: [what implemented]. Files: [files changed]. Learnings: [patterns/gotchas/context]`
- **Codebase Patterns:**
  - Store Codebase Patterns in project epic notes (not in progress.txt)
  - Use `bd update <project-epic-id> --comment` to add/update patterns
  - Read patterns from project epic before starting work
- Update commit message format:
  - Extract story ID from Beads metadata: `bd show <task-id>` and parse `story-id: US-001` from notes
  - Use format: `feat: [Story ID] - [Task Title]` (if story ID exists) or `feat: [Beads ID] - [Task Title]` (fallback)
- Update phase detection to use Beads hierarchical structure:
  - Find current phase epic (first phase epic with open tasks)
  - Get phase epic ID from hierarchical structure
- Update branch checkout logic to read branch from Beads metadata:
  - Use `bd show <phase-epic-id>` and extract branch from metadata/notes
- Update completion detection:
  - After closing task, run `bd list --parent <phase-epic-id> --status open`
  - If empty: phase complete, check for remaining phase epics
  - If all phase epics complete: output `<promise>COMPLETE</promise>`

**1.3 Add Beads initialization to `bin/ralph.py`**

- Check for `bd` command in PATH during `ralph init`
- Run `bd init` if Beads not initialized
- Add Beads to required dependencies documentation

### Phase 2: Migration Tools

**2.1 Create `scripts/ralph/migrate-prd-to-beads.py`**

- Read existing `prd.yml` file
- Create Beads epic for project (top-level)
- For each phase:
  - Create phase-level epic with hierarchical ID (e.g., `bd-{hash}.{phaseNumber}`)
  - Store phase `branchName` in epic metadata
  - **Organize tasks by priority** - create tasks in priority order (lower priority number = higher priority = created first)
  - For each user story (sorted by priority, ascending):
    - Create task with hierarchical ID (e.g., `bd-{hash}.{phaseNumber}.{storyNumber}`)
    - Convert acceptance criteria to task description
    - Set priority from story priority (lower number = higher priority)
    - If `passes: true`, close the task
    - Store story ID (US-001) in task metadata using `bd note <task-id> "story-id: US-001"` for human-readable reference in commits/logs
- Create dependencies:
  - **Priority-based dependencies**: Lower priority number tasks depend on higher priority number tasks (priority 2 depends on priority 1)
  - Use `bd dep add <child> <parent>` to create dependencies based on priority order
  - Allow manual dependency specification in migration

**2.2 Update `convert-to-prd-yml.sh` → `convert-to-beads.sh`**

- Rename script to `convert-to-beads.sh`
- Update to use Beads commands instead of YAML generation
- Convert PRD markdown directly to Beads issues
- Maintain same phase/story structure but create Beads issues
- **Organize tasks by priority** - create tasks in priority order (what needs to be developed first)
- Set up dependencies based on priority (lower priority number tasks depend on higher priority number tasks)

### Phase 3: Documentation Updates

**3.1 Update `AGENTS.md`**

- Replace references to `prd.yml` with Beads commands
- Update workflow to use `bd ready`, `bd show`, `bd close`
- Document Beads initialization requirement
- Update examples to show Beads commands

**3.2 Update `README.md`**

- Replace PRD conversion examples with Beads commands
- Update debugging section to use `bd` commands
- Add Beads installation requirement
- Update workflow diagrams if needed

**3.3 Update `.cursor/commands/prd-to-yml.md` → `prd-to-beads.md`**

- Rename command file
- Update to generate Beads issues instead of YAML
- Maintain same structure but output Beads creation commands
- **Critical: Priority organization**
  - Tasks must be organized by priority - what needs to be developed first
  - Lower priority number = higher priority = should be created first
  - Create tasks in priority order (ascending by priority number)
  - Set up dependencies: lower priority number tasks depend on higher priority number tasks (priority 2 depends on priority 1)
  - This ensures `bd ready` will show tasks in the correct development order

### Phase 4: Cleanup & Testing

**4.1 Remove deprecated files**

- Remove `prd.yml.example` (or convert to Beads example)
- Remove `progress.txt` references and file handling
- Update `ralph.py` to remove YAML reading code and progress.txt handling
- Remove `yq` dependency (no longer needed)
- Update `.gitignore` to remove progress.txt entry (if present)

**4.2 Update example/template files**

- Create Beads example structure in documentation
- Update `bin/ralph.py` init to not copy `prd.yml.example`

**4.3 Testing**

- Test migration script with existing `prd.yml` files
- Test that tasks are created in priority order (lower priority number = created first)
- Test that dependencies are set up correctly based on priority (lower priority number tasks depend on higher priority number tasks)
- Test that `bd ready` shows tasks in correct development order
- Test Ralph workflow with Beads
- Test phase transitions with hierarchical IDs
- Test dependency tracking
- Test branch name extraction from Beads metadata
- Test failure comment creation and reading
- Test that next iteration reads previous attempt comments and learns from them

## File Changes Summary

### Modified Files

- `scripts/ralph/ralph.py` - Replace YAML reading with Beads commands, remove progress.txt references
- `scripts/ralph/cursor/prompt.cursor.md` - Update to use Beads workflow, remove progress.txt references
- `bin/ralph.py` - Add Beads initialization check
- `AGENTS.md` - Update documentation, remove progress.txt references
- `README.md` - Update examples and requirements, remove progress.txt references

### New Files

- `scripts/ralph/migrate-prd-to-beads.py` - Migration tool
- `scripts/ralph/cursor/convert-to-beads.sh` - PRD to Beads converter
- `.cursor/commands/prd-to-beads.md` - Updated command documentation

### Deprecated Files

- `scripts/ralph/prd.yml.example` - No longer needed (or convert to Beads example)
- `scripts/ralph/cursor/convert-to-prd-yml.sh` - Replaced by `convert-to-beads.sh`
- `.cursor/commands/prd-to-yml.md` - Replaced by `prd-to-beads.md`
- `scripts/ralph/progress.txt` - No longer needed (all information stored in Beads comments/notes)

## Key Implementation Details

### Hierarchical Structure Mapping

```
Project (Epic): bd-{project-hash}
  └─ Phase 1 (Epic): bd-{project-hash}.1
      └─ Story 1 (Task): bd-{project-hash}.1.1
      └─ Story 2 (Task): bd-{project-hash}.1.2
  └─ Phase 2 (Epic): bd-{project-hash}.2
      └─ Story 3 (Task): bd-{project-hash}.2.1
```

### Branch Name Storage

Store branch names in Beads issue metadata using `bd` commands:

```bash
bd note <epic-id> "branch: ralph/feature-name-phase-1"
```

### Dependency Tracking

Use story priority and explicit dependencies:

- **Priority organization**: Tasks are organized by priority - lower priority number = higher priority = what needs to be developed first
- Lower priority number = higher priority task
- If US-002 has priority 2 and US-001 has priority 1, US-002 depends on US-001
- Use `bd dep add <child> <parent>` to create dependencies
- **When converting PRD to Beads**: Create tasks in priority order (ascending by priority number) and set up dependencies so lower priority number tasks depend on higher priority number tasks
- This ensures `bd ready` will show tasks in the correct development order

### Status Mapping

- `passes: false` → Open Beads issue
- `passes: true` → Closed (archived) Beads issue
- Use `bd ready` to find open tasks with no blockers
- **Closing = Archiving**: Closing a task or epic in Beads archives it - the task is preserved for reference but no longer appears in active task lists

### Failure Comments and Learning

When an agent cannot complete a task, it leaves a comment in the Beads issue for the next iteration. **Comments are automatically timestamped and append-only** - they preserve the complete history of all attempts.

**Before starting work:**

1. Read task details: `bd show <task-id>`
2. Review comments from previous iterations (comments are timestamped, showing most recent attempts)
3. Pay special attention to the most recent comments to understand what was tried last
4. Learn from failures: avoid repeating approaches that didn't work
5. Build on previous attempts rather than starting from scratch

**When task cannot be completed:**

1. Use `bd update <task-id> --comment "text"` to add a comment (comments are automatically timestamped)
2. Include:

   - What was attempted (approach, code changes, etc.)
   - What failed (error messages, test failures, etc.)
   - Why it failed (root cause if identified)

3. Do NOT include suggestions of what to try next - document facts only, let the next iteration determine the approach

4. Format example:
   ```
   Attempt failed: Tried implementing X using approach Y.
   Error: Type error in file Z at line N.
   Root cause: Missing type definition for interface A.
   ```


(Timestamp is automatically added by Beads)

5. **Critical**: Comments are automatically append-only - each comment is preserved with its timestamp

**Benefits:**

- Complete history of all attempts preserved with timestamps
- Next iteration can see what was tried most recently (most recent comments first)
- Timestamps help identify the sequence of attempts
- Builds knowledge over multiple attempts
- Helps identify patterns in failures across iterations
- All information in one place (Beads) - no need for separate progress.txt file

### Codebase Patterns Storage

Codebase Patterns (reusable project-wide patterns) are stored in the project epic notes/comments in Beads, replacing the "Codebase Patterns" section that was previously in progress.txt.

**Storage:**

- Store in project epic (top-level epic) using `bd update <project-epic-id> --comment`
- Format: `Codebase Pattern: [pattern description]`
- Multiple patterns can be stored as separate comments or in a single formatted comment

**Usage:**

- Read patterns from project epic before starting work: `bd show <project-epic-id>`
- Review patterns to understand codebase conventions
- Add new patterns discovered during implementation as comments to project epic
- Patterns are preserved across all tasks and iterations

**Example:**

```bash
bd update bd-project-hash --comment "Codebase Pattern: Use sql<number> template for aggregations"
bd update bd-project-hash --comment "Codebase Pattern: Always use IF NOT EXISTS for migrations"
```

### Success Learnings Storage

When a task completes successfully, store learnings in Beads task comments before closing:

**Storage:**

- Add comment to task before closing: `bd update <task-id> --comment "text"`
- Include: what was implemented, files changed, patterns discovered, gotchas, context
- Format: `Completed: [what implemented]. Files: [files changed]. Learnings: [patterns/gotchas/context]`

**Usage:**

- Learnings are preserved in task comments even after task is closed (archived)
- Can be referenced later for similar tasks
- Helps build knowledge base over time

### Epic Completion Detection

Ralph detects epic completion using Beads commands:

**After completing a task:**

1. Close (archive) the task with `bd close <task-id>` - this archives it, preserving it for reference
2. Get current phase epic ID (from hierarchical structure, e.g., `bd-{hash}.1`)
3. Check if phase epic is complete:
   ```bash
   bd list --parent <phase-epic-id> --status open
   ```


   - If this returns no tasks, all tasks in the phase are closed (archived), so the phase epic is complete
   - Alternative: `bd epic status <phase-epic-id>` shows completion percentage (100% = complete)
   - Closed tasks are archived and don't appear in open task lists

4. If phase complete:

   - Check if there are more phase epics (check parent epic for other phase children)
   - If all phase epics complete, signal `<promise>COMPLETE</promise>`
   - If more phases exist, next iteration will move to next phase branch

**Completion check logic in `prompt.cursor.md`:**

- After closing (archiving) task with `bd close <task-id>`
- Run `bd list --parent <phase-epic-id> --status open` 
- If empty: phase complete (all tasks archived), check for more phases
- If all phases complete: output `<promise>COMPLETE</promise>`
- Otherwise: end iteration normally (next iteration continues)

**Note:** Closed tasks are archived, not deleted - they remain accessible for reference but don't appear in active task queries like `bd ready` or `bd list --status open`

## Migration Path

1. **Existing projects**: Run `migrate-prd-to-beads.py` to convert existing `prd.yml`
2. **New projects**: Use `convert-to-beads.sh` directly from PRD markdown
3. **Backward compatibility**: None - full replacement approach

## Dependencies

- Beads CLI (`bd`) must be installed and in PATH
- Beads initialized in repository (`bd init`)
- Git repository (already required for Ralph)
