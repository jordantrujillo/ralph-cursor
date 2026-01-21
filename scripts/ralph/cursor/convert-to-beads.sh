#!/bin/bash
# Convert PRD markdown to Beads issues using Cursor CLI
#
# Usage:
#   ./convert-to-beads.sh tasks/prd-[feature-name].md [--model MODEL] [--out OUT_DIR]
#
# This script uses Cursor CLI to convert a PRD markdown file into Beads issues.
# The conversion creates a hierarchical structure:
# - Project epic (top-level)
# - Phase epics (one per phase)
# - Tasks (one per user story)
#
# Tasks are created in priority order and dependencies are set up based on priority
# (lower priority number tasks depend on higher priority number tasks).

set -e

# Default values
MODEL="${RALPH_MODEL:-auto}"
PRD_FILE=""
OUT_DIR=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --out)
            OUT_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 <prd-file> [--model MODEL] [--out OUT_DIR]"
            echo ""
            echo "Convert PRD markdown to Beads issues using Cursor CLI"
            echo ""
            echo "Arguments:"
            echo "  prd-file          Path to PRD markdown file"
            echo ""
            echo "Options:"
            echo "  --model MODEL    Model to use (default: auto, from RALPH_MODEL env)"
            echo "  --out OUT_DIR    Output directory for generated files (optional)"
            echo "  --help, -h       Show this help message"
            exit 0
            ;;
        *)
            if [[ -z "$PRD_FILE" ]]; then
                PRD_FILE="$1"
            else
                echo "Error: Unknown argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# Check required arguments
if [[ -z "$PRD_FILE" ]]; then
    echo "Error: PRD file path required" >&2
    echo "Usage: $0 <prd-file> [--model MODEL] [--out OUT_DIR]" >&2
    exit 1
fi

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PRD_PATH="$PRD_FILE"
if [[ ! "$PRD_PATH" =~ ^/ ]]; then
    PRD_PATH="$REPO_ROOT/$PRD_PATH"
fi

# Check if PRD file exists
if [[ ! -f "$PRD_PATH" ]]; then
    echo "Error: PRD file not found: $PRD_PATH" >&2
    exit 1
fi

# Check for Beads CLI
if ! command -v bd &> /dev/null; then
    echo "Error: Beads CLI (bd) not found in PATH" >&2
    echo "Please install Beads: https://github.com/beads-org/beads" >&2
    exit 1
fi

# Check if Beads is initialized
if [[ ! -d "$REPO_ROOT/.beads" ]]; then
    echo "Error: Beads not initialized in repository" >&2
    echo "Please run: bd init" >&2
    exit 1
fi

# Check for Cursor CLI
CURSOR_BINARY=""
for binary in cursor-agent agent; do
    if command -v "$binary" &> /dev/null; then
        CURSOR_BINARY="$binary"
        break
    fi
done

if [[ -z "$CURSOR_BINARY" ]]; then
    echo "Error: Cursor CLI not found (tried: cursor-agent, agent)" >&2
    echo "Please install Cursor CLI" >&2
    exit 1
fi

# Read PRD content
PRD_CONTENT="$(cat "$PRD_PATH")"

# Create prompt for Cursor
PROMPT_FILE="$(mktemp)"
cat > "$PROMPT_FILE" << 'PROMPT_EOF'
# Convert PRD to Beads Issues

You are converting a PRD (Product Requirements Document) markdown file into Beads issues.

## Your Task

Read the PRD markdown provided and create Beads issues using the `bd` command.

## Beads Commands Reference

- `bd epic create <title> [--description TEXT] [--parent EPIC_ID]` - Create an epic
- `bd task create <title> [--description TEXT] [--parent EPIC_ID] [--priority NUMBER]` - Create a task
- `bd note <ISSUE_ID> "text"` - Add metadata/notes to an issue
- `bd dep add <CHILD_ID> <PARENT_ID>` - Add dependency (child depends on parent)
- `bd show <ISSUE_ID>` - Show issue details
- `bd list [--type epic|task] [--parent EPIC_ID] [--status open|closed]` - List issues

## Conversion Rules

1. **Create project epic (top-level):**
   - Title: Project name from PRD
   - Description: Project description from PRD
   - Store branch name in notes: `bd note <epic-id> "branch: ralph/feature-name"`

2. **For each phase:**
   - Create phase epic with parent = project epic
   - Title: "Phase N: [phase description]"
   - Store phase branch name in notes: `bd note <epic-id> "branch: ralph/feature-name-phase-N"`

3. **For each user story (within phase):**
   - **CRITICAL: Create tasks in priority order (ascending by priority number)**
   - Lower priority number = higher priority = create first
   - Create task with parent = phase epic
   - Title: "[Story ID]: [Story Title]"
   - Description: Story description + acceptance criteria
   - Priority: Use story priority number
   - Store story ID in notes: `bd note <task-id> "story-id: US-001"`

4. **Set up dependencies:**
   - After creating all tasks in a phase, set up dependencies based on priority
   - Lower priority number tasks depend on higher priority number tasks
   - Example: If US-002 has priority 2 and US-001 has priority 1, then: `bd dep add <US-002-task-id> <US-001-task-id>`
   - This ensures `bd ready` shows tasks in correct development order

5. **Priority organization:**
   - Tasks must be organized by priority - what needs to be developed first
   - Lower priority number = higher priority = should be created first
   - Create tasks in priority order (ascending by priority number)
   - Set up dependencies: lower priority number tasks depend on higher priority number tasks

## Output Format

Execute the `bd` commands directly. Show the output of each command.

After conversion, show:
- Project epic ID
- Phase epic IDs
- Summary of tasks created

## PRD Content

```markdown
PROMPT_EOF

echo "$PRD_CONTENT" >> "$PROMPT_FILE"
echo '```' >> "$PROMPT_FILE"

# Run Cursor CLI
echo "Converting PRD to Beads issues using Cursor CLI..."
echo "Model: $MODEL"
echo "PRD file: $PRD_PATH"
echo ""

cd "$REPO_ROOT"

# Execute Cursor CLI
"$CURSOR_BINARY" \
    --model "$MODEL" \
    --print \
    --force \
    --approve-mcps \
    "$(cat "$PROMPT_FILE")"

# Cleanup
rm -f "$PROMPT_FILE"

echo ""
echo "✓ Conversion complete!"
echo ""
echo "View your Beads issues:"
echo "  bd list --type epic"
echo "  bd ready  # Show ready tasks (no blockers)"
