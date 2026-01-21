# Ralph Agent Instructions

## Overview

Ralph is an autonomous AI agent loop that runs Cursor CLI repeatedly until all PRD items are complete. Each iteration is a fresh worker invocation with clean context.

## Commands

```bash
# Run the flowchart dev server
cd flowchart && npm run dev

# Build the flowchart
cd flowchart && npm run build

# Run Ralph (from your project that has Beads initialized)
python3 scripts/ralph/ralph.py [max_iterations] [--cursor-timeout SECONDS]

# Convert PRD markdown to Beads issues using Cursor CLI
./scripts/ralph/cursor/convert-to-beads.sh tasks/prd-[feature-name].md [--model MODEL]

# Migrate existing prd.yml to Beads issues
python3 scripts/ralph/migrate-prd-to-beads.py [prd.yml path]
```

## Key Files

- `scripts/ralph/ralph.py` - The Python loop (Cursor worker)
- `scripts/ralph/cursor/prompt.cursor.md` - Instructions given to each Cursor iteration
- `scripts/ralph/cursor/convert-to-beads.sh` - Convert PRD markdown → Beads issues via Cursor CLI
- `scripts/ralph/migrate-prd-to-beads.py` - Migrate existing prd.yml → Beads issues
- `.beads/` - Beads git-backed JSONL storage (task tracking)
- `flowchart/` - Interactive React Flow diagram explaining how Ralph works

## Flowchart

The `flowchart/` directory contains an interactive visualization built with React Flow. It's designed for presentations - click through to reveal each step with animations.

To run locally:
```bash
cd flowchart
npm install
npm run dev
```

## Patterns

- Each iteration spawns a fresh Cursor invocation with clean context
- Memory persists via git history, Beads issue comments, and Beads issue metadata
- Tasks should be small enough to complete in one context window
- Always update AGENTS.md with discovered patterns for future iterations
- Cursor-specific prompts are in `scripts/ralph/cursor/` subfolder

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

### Common Beads Commands

```bash
# List open epics
bd list --type epic --status open

# List ready tasks (no blockers)
bd ready

# Show issue details
bd show <issue-id>

# Close (archive) a task
bd close <task-id>

# Add comment to issue
bd update <issue-id> --comment "text"

# Add metadata/notes
bd note <issue-id> "key: value"

# List tasks in a phase
bd list --parent <phase-epic-id> --status open
```
