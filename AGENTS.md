# Ralph Agent Instructions

## Overview

Ralph is an autonomous AI agent loop that runs Cursor CLI repeatedly until all PRD items are complete. Each iteration is a fresh worker invocation with clean context.

## Commands

```bash
# Run the flowchart dev server
cd flowchart && npm run dev

# Build the flowchart
cd flowchart && npm run build

# Bootstrap global Cursor commands (once per machine, from ralph-cursor clone)
python3 bin/ralph.py install-cursor

# Portable loop: any repo with .beads/ (cwd = that repo)
python3 /path/to/ralph-cursor/bin/ralph.py run --project "$(pwd)" [max_iterations] [--cursor-timeout SECONDS]

# Legacy: in-repo runner after `ralph init`
python3 scripts/ralph/ralph.py [max_iterations] [--cursor-timeout SECONDS]

# Merge Ralph .gitignore block (adds AGENTS.md / CLAUDE.md / .claude/ only when untracked — typical after bd init)
python3 /path/to/ralph-cursor/bin/ralph.py setup --project "$(pwd)"

# Convert PRD markdown to Beads issues (manual bd commands — see global command prd-to-beads)
# ~/.cursor/commands/prd-to-beads.md after install-cursor
```

## Key Files

- `bin/ralph.py` - CLI (`install-cursor`, `setup`, `init`, `run` with `--project`, …)
- `scripts/ralph/ralph.py` - The Python loop (Cursor worker)
- `scripts/ralph/cursor/prompt.cursor.md` - Instructions given to each Cursor iteration
- `.beads/` - Beads git-backed JSONL storage (task tracking)
- `flowchart/` - Interactive React Flow diagram explaining how Ralph works

## Flowchart

Interactive diagram (React Flow) in `flowchart/`: `cd flowchart && npm install && npm run dev` (production build: `npm run build`). See [README.md](README.md) for more context.

## Patterns

- Each iteration spawns a fresh Cursor invocation with clean context
- Memory persists via git history, Beads issue comments, and Beads issue metadata
- Tasks should be small enough to complete in one context window
- Always update AGENTS.md with discovered patterns for future iterations
- Cursor slash commands for PRD / setup ship globally under `~/.cursor/commands/` (`ralph install-cursor` from this clone); see `~/.config/ralph-cursor/package_root` for the recorded clone path
- Cursor-specific prompts are in `scripts/ralph/cursor/` subfolder (bundled with the runner in this repo)
- `scripts/ralph/.last-branch` is written by the runner for branch tracking (gitignored); delete locally if it shows up as noise—it is not meant to be committed

## Phases and Branching

Ralph supports breaking down large PRDs into multiple phases, each with its own branch:

- **Phase branches:** Each phase gets its own branch (e.g., `ralph/feature-name-phase-1`, `ralph/feature-name-phase-2`)
- **Branch hierarchy:** Phase 1 branches from `main`, Phase N branches from Phase N-1's branch
- **Incremental PRs:** Each phase can be reviewed as a separate PR, keeping PRs manageable
- **Automatic progression:** Ralph automatically moves to the next phase when the current phase is complete
- **PRD structure:** PRDs can define phases in the markdown, which get converted to phase epics in Beads
- **Legacy support:** PRDs without phases are treated as a single phase for backward compatibility

## Beads Workflow

Ralph uses Beads, a git-backed graph issue tracker, for task management:

- **Epics:** Project epic (top-level), phase epics (one per phase)
- **Tasks:** User stories become tasks under phase epics
- **Dependencies:** Tasks have dependencies based on priority (lower priority number tasks depend on higher priority number tasks)
- **Status:** Open tasks are active, closed tasks are archived
- **Comments:** Task comments preserve attempt history and learnings
- **Metadata:** Branch names and story IDs stored in issue notes

### Beads Initialization

When initializing Beads in a new repository:

```bash
# Initialize Beads (prefix auto-derived from directory name)
bd init
```

The prefix is automatically derived from the directory name (e.g., directory `myapp` → prefix `myapp` → issue IDs like `myapp-a3f2dd`).

### Common Beads Commands

```bash
# Initialize Beads (prefix auto-derived from directory name)
bd init

# List open epics
bd list --type epic --status open

# List ready tasks (no blockers)
bd ready

# Show issue details
bd show <issue-id>

# Close (archive) a task
bd close <task-id>

# Add comment to issue
bd comments add <issue-id> "comment text"

# Add metadata/notes
bd update <issue-id> --notes "key: value"

# Update issue fields
bd update <issue-id> --title "New title" --status in_progress

# List tasks in a phase
bd list --parent <phase-epic-id> --status open

# Get configuration
bd config list
bd config get issue_prefix
```

### Creating Project Structure

```bash
# 1. Create project epic
EPIC_ID=$(bd create --title "Feature Name" --type epic \
  --description "Feature description" --json | jq -r '.id')

# 2. Add branch metadata (REQUIRED for Ralph!)
bd note "$EPIC_ID" "branch: ralph/feature-name"

# 3. Create tasks under epic
bd create --title "Task 1" --type task --parent "$EPIC_ID" \
  --description "Task description with acceptance criteria"

# 4. Verify structure
bd show "$EPIC_ID"
bd ready
```

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:7510c1e2 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
