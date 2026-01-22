# Ralph

![Ralph](ralph.webp)

Ralph is an autonomous AI agent loop that runs Cursor CLI repeatedly until all PRD items are complete. Each iteration is a fresh worker invocation with clean context. Memory persists via git history, Beads issue comments, and Beads issue metadata.

Based on [Geoffrey Huntley's Ralph pattern](https://ghuntley.com/ralph/).

[Read my in-depth article on how OP uses Ralph](https://x.com/ryancarson/status/2008548371712135632)

## Prerequisites

- Cursor CLI (`cursor-agent` or `agent` command) installed and authenticated
- Python 3 installed
- Beads CLI (`bd` command) installed - [Install Beads](https://github.com/steveyegge/beads)
- A git repository for your project

## Installation

### Install Ralph CLI

Install the Ralph CLI globally:

```bash
# From the ralph-cursor repository root
./install.sh
```

This installs the `ralph` command to `~/.local/bin` (or `/usr/local/bin` if that's not writable). Make sure this directory is in your PATH.

### Initialize Ralph in your project

Navigate to your project directory and initialize Ralph:

```bash
# Basic initialization
ralph init

# With CLI config template
ralph init --cursor-cli

# Overwrite existing files
ralph init --force
```

This copies the necessary Ralph files into your project's `scripts/ralph/` directory and initializes Beads if needed.

### Verify Beads Initialization

Ralph automatically initializes Beads with a project-specific prefix during `ralph init`. Verify it's set up correctly:

```bash
# Check Beads is initialized
ls .beads/

# Verify the issue prefix
bd config get issue_prefix
```

If Beads wasn't initialized or needs manual setup:

```bash
# Initialize Beads (prefix auto-derives from directory name)
bd init
```

The prefix is automatically derived from your directory name (e.g., directory `myapp` → prefix `myapp` → issue IDs like `myapp-a3f2dd`).

## Workflow

### 1. Create a PRD

Generate a PRD using Cursor in the IDE with the repo's Cursor rules (see `.cursor/rules/`), or create one manually. It is recommended to go back and forth with the agent until you are happy with the PRD. Important that you take the time to READ it. 

### 2. Convert PRD to Beads Issues

> **Note**: The automated conversion scripts (`convert-to-beads.sh` and `migrate-prd-to-beads.py`) are not yet implemented. 
> For now, you'll need to manually create Beads issues using the `bd` CLI commands. 
> See `.cursor/commands/prd-to-beads.md` for the conversion process and Beads command reference.

### 3. Run Ralph

Use the Ralph CLI to run the agent loop:

```bash
# Run with default settings (10 iterations)
ralph run

# Run with custom iteration count
ralph run 20

# Run with timeout and model selection
ralph run 10 --cursor-timeout 3600 --model claude-3.5-sonnet
```

You can also run the Python script directly:

```bash
python3 scripts/ralph/ralph.py [max_iterations] [--cursor-timeout SECONDS] [--model MODEL]
```

**Environment Variables:**
- `RALPH_CURSOR_TIMEOUT` - Default timeout in seconds (default: 1800)
- `RALPH_MODEL` - Default model to use (default: 'auto')

The runner loop will invoke Cursor CLI repeatedly. The worker prompt instructs it to:
- Read Beads issues using `bd ready`, `bd show`, etc.
- Implement one task per iteration, run checks, commit, and close the task
- Stop by outputting `<promise>COMPLETE</promise>` when all tasks are closed

**Note:** `--cursor-timeout` only applies if a `timeout` binary is available on your PATH. If it isn't, Ralph will use Python's timeout mechanism.

## Key Files

| File | Purpose |
|------|---------|
| `bin/ralph.py` | The Ralph CLI tool (`ralph init` and `ralph run` commands) |
| `scripts/ralph/ralph.py` | The Python loop that spawns fresh Cursor invocations |
| `scripts/ralph/cursor/prompt.cursor.md` | Instructions given to each Cursor iteration |
| `.beads/` | Beads git-backed JSONL storage (task tracking) |
| `flowchart/` | Interactive visualization of how Ralph works |

## Flowchart

The `flowchart/` directory contains the source code. To run locally:

```bash
cd flowchart
npm install
npm run dev
```

## Critical Concepts

### Each Iteration = Fresh Context

Each iteration spawns a **new Cursor invocation** with clean context. The only memory between iterations is:
- Git history (commits from previous iterations)
- Beads issue comments (learnings and attempt history)
- Beads issue metadata (status, dependencies, branch names)

### Small Tasks

Each PRD item should be small enough to complete in one context window. If a task is too big, the LLM runs out of context before finishing and produces poor code.

Right-sized stories:
- Add a database column and migration
- Add a UI component to an existing page
- Update a server action with new logic
- Add a filter dropdown to a list

Too big (split these):
- "Build the entire dashboard"
- "Add authentication"
- "Refactor the API"

### AGENTS.md Files (Cursor Workspace Rules)

In Cursor, `AGENTS.md` files are workspace-level rule files that provide persistent instructions to the AI agent. They're not automatically updated by Ralph, but agents are instructed to update them when they discover reusable patterns.

**Format:** Keep AGENTS.md files as small as possible with short, concise rules:

**Example:**

```markdown
## Testing

### Rules
- Use X for Y
- Always do Z when W
- Never forget to update A when changing B
```

**How AGENTS.md works:**
- `AGENTS.md` files are read by Cursor as workspace rules (similar to `.cursor/rules/` files)
- Agents check for `AGENTS.md` files in directories where they make changes
- If valuable patterns are discovered, agents add them to nearby `AGENTS.md` files
- Main learnings go into Beads issue comments (especially Codebase Patterns in project epic)

**What belongs in AGENTS.md:**
- Directory-specific API patterns or conventions (short rules only)
- Gotchas or non-obvious requirements for that module
- Dependencies between files in that area
- Configuration or environment requirements
- If Agent is given a task that is in conflict with a rule, it should remove that rule from the AGENTS.md file.

**What belongs in Beads:**
- Task-specific implementation details (in task comments)
- Learnings from each iteration (in task comments)
- General codebase patterns (in project epic comments)

### Feedback Loops

Ralph only works if there are feedback loops:
- Typecheck catches type errors
- Tests verify behavior
- CI must stay green (broken code compounds across iterations)

### Browser Verification for UI Stories

Frontend stories must include "Verify in browser using browser MCP tools" in acceptance criteria. Ralph will use browser MCP tools (if configured) to navigate to the page, interact with the UI, and confirm changes work.

### Stop Condition

When all tasks are closed (archived), Ralph outputs `<promise>COMPLETE</promise>` and the loop exits.

## Debugging

Check current state:

```bash
# See open tasks
bd list --status open

# See ready tasks (no blockers)
bd ready

# Show task details
bd show <task-id>

# List tasks in a phase
bd list --parent <phase-epic-id> --status open

# Check git history
git log --oneline -10
```

## Customizing prompts

Edit the worker prompt to customize Ralph's behavior for your project:
- Add project-specific quality check commands
- Include codebase conventions
- Add common gotchas for your stack

Worker prompt location:
- `scripts/ralph/cursor/prompt.cursor.md`

## CLI Commands

### `ralph init`

Initialize Ralph in your current repository:

```bash
ralph init [--force] [--cursor-cli]
```

Options:
- `--force` - Overwrite existing files
- `--cursor-cli` - Also install `.cursor/cli.json` template

### `ralph run`

Run the Ralph agent loop:

```bash
ralph run [max_iterations] [--cursor-timeout SECONDS] [--model MODEL]
```

Arguments:
- `max_iterations` - Maximum number of iterations (default: 10)

Options:
- `--cursor-timeout SECONDS` - Timeout for cursor worker in seconds (default: 1800, from `RALPH_CURSOR_TIMEOUT` env)
- `--model MODEL` - Model to use for cursor worker (default: 'auto', from `RALPH_MODEL` env)

## Archiving

Ralph automatically archives completed tasks when they are closed. Beads preserves closed tasks for reference but they don't appear in active task queries.

## References

- [Geoffrey Huntley's Ralph article](https://ghuntley.com/ralph/)
- [Beads Issue Tracker](https://github.com/steveyegge/beads)
