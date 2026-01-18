# Ralph Agent Instructions

## Overview

Ralph is an autonomous AI agent loop that runs an AI worker (default: Amp, optional: Cursor CLI) repeatedly until all PRD items are complete. Each iteration is a fresh worker invocation with clean context.

## Commands

```bash
# Run the flowchart dev server
cd flowchart && npm run dev

# Build the flowchart
cd flowchart && npm run build

# Run Ralph (from your project that has scripts/ralph/prd.yml)
./scripts/ralph/ralph.sh [max_iterations] [--worker amp|cursor] [--cursor-timeout SECONDS]

# Convert PRD markdown to prd.yml using Cursor CLI
./scripts/ralph/cursor/convert-to-prd-json.sh tasks/prd-[feature-name].md [--model MODEL] [--out OUT_YML]
```

## Key Files

- `scripts/ralph/ralph.sh` - The bash loop (Amp + optional Cursor worker)
- `scripts/ralph/prompt.md` - Instructions given to each Amp iteration
- `scripts/ralph/cursor/prompt.cursor.md` - Instructions given to each Cursor iteration
- `scripts/ralph/cursor/convert-to-prd-json.sh` - Convert PRD markdown → `scripts/ralph/prd.yml` via Cursor CLI
- `scripts/ralph/prd.yml.example` - Example PRD format
- `scripts/ralph/prd.yml` - User stories with `passes` status (the task list)
- `scripts/ralph/progress.txt` - Append-only learnings for future iterations
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

- Each iteration spawns a fresh worker invocation (Amp or Cursor) with clean context
- Memory persists via git history, `scripts/ralph/progress.txt`, and `scripts/ralph/prd.yml`
- Stories should be small enough to complete in one context window
- Always update AGENTS.md with discovered patterns for future iterations
- Cursor-specific prompts are in `scripts/ralph/cursor/` subfolder