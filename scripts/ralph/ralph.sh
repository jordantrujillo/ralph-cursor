#!/bin/bash
# Ralph Wiggum - Long-running AI agent loop
# Usage: ./ralph.sh [max_iterations] [--cursor-timeout SECONDS]
# Uses Cursor CLI as the worker

set -e

# Parse arguments
MAX_ITERATIONS=10
CURSOR_TIMEOUT="${RALPH_CURSOR_TIMEOUT:-1800}" # Default: 30 minutes (in seconds)

while [[ $# -gt 0 ]]; do
  case $1 in
    --cursor-timeout)
      CURSOR_TIMEOUT="$2"
      shift 2
      ;;
    *)
      if [[ "$1" =~ ^[0-9]+$ ]]; then
        MAX_ITERATIONS="$1"
      fi
      shift
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRD_FILE="$SCRIPT_DIR/prd.yml"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
LAST_BRANCH_FILE="$SCRIPT_DIR/.last-branch"

# Archive previous run if branch changed
if [ -f "$PRD_FILE" ] && [ -f "$LAST_BRANCH_FILE" ]; then
  # Try yq first, fallback to python if yq not available
  if command -v yq >/dev/null 2>&1; then
    CURRENT_BRANCH=$(yq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || echo "")
  elif command -v python3 >/dev/null 2>&1; then
    CURRENT_BRANCH=$(python3 -c "import yaml, sys; print(yaml.safe_load(open('$PRD_FILE'))['branchName'] if yaml.safe_load(open('$PRD_FILE')) and 'branchName' in yaml.safe_load(open('$PRD_FILE')) else '')" 2>/dev/null || echo "")
  else
    CURRENT_BRANCH=""
  fi
  LAST_BRANCH=$(cat "$LAST_BRANCH_FILE" 2>/dev/null || echo "")
  
  if [ -n "$CURRENT_BRANCH" ] && [ -n "$LAST_BRANCH" ] && [ "$CURRENT_BRANCH" != "$LAST_BRANCH" ]; then
    # Archive the previous run
    DATE=$(date +%Y-%m-%d)
    # Strip "ralph/" prefix from branch name for folder
    FOLDER_NAME=$(echo "$LAST_BRANCH" | sed 's|^ralph/||')
    ARCHIVE_FOLDER="$ARCHIVE_DIR/$DATE-$FOLDER_NAME"
    
    echo "Archiving previous run: $LAST_BRANCH"
    mkdir -p "$ARCHIVE_FOLDER"
    [ -f "$PRD_FILE" ] && cp "$PRD_FILE" "$ARCHIVE_FOLDER/"
    [ -f "$PROGRESS_FILE" ] && cp "$PROGRESS_FILE" "$ARCHIVE_FOLDER/"
    echo "   Archived to: $ARCHIVE_FOLDER"
    
    # Reset progress file for new run
    echo "# Ralph Progress Log" > "$PROGRESS_FILE"
    echo "Started: $(date)" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
  fi
fi

# Track current branch
if [ -f "$PRD_FILE" ]; then
  # Try yq first, fallback to python if yq not available
  if command -v yq >/dev/null 2>&1; then
    CURRENT_BRANCH=$(yq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || echo "")
  elif command -v python3 >/dev/null 2>&1; then
    CURRENT_BRANCH=$(python3 -c "import yaml, sys; print(yaml.safe_load(open('$PRD_FILE'))['branchName'] if yaml.safe_load(open('$PRD_FILE')) and 'branchName' in yaml.safe_load(open('$PRD_FILE')) else '')" 2>/dev/null || echo "")
  else
    CURRENT_BRANCH=""
  fi
  if [ -n "$CURRENT_BRANCH" ]; then
    echo "$CURRENT_BRANCH" > "$LAST_BRANCH_FILE"
  fi
fi

# Initialize progress file if it doesn't exist
if [ ! -f "$PROGRESS_FILE" ]; then
  echo "# Ralph Progress Log" > "$PROGRESS_FILE"
  echo "Started: $(date)" >> "$PROGRESS_FILE"
  echo "---" >> "$PROGRESS_FILE"
fi

echo "Starting Ralph - Max iterations: $MAX_ITERATIONS"
echo "Worker: Cursor"

for i in $(seq 1 $MAX_ITERATIONS); do
  echo ""
  echo "═══════════════════════════════════════════════════════"
  echo "  Ralph Iteration $i of $MAX_ITERATIONS (Worker: Cursor)"
  echo "═══════════════════════════════════════════════════════"
  
  # Cursor worker: use cursor/prompt.cursor.md and execute cursor CLI
  # Uses non-interactive headless mode with file edits enabled
  # Always uses normal spawn (never PTY), stdin is closed (no interactive prompts)
  # Use test prompt if RALPH_TEST_MODE is set
  if [[ "${RALPH_TEST_MODE:-}" == "1" ]]; then
    PROMPT_FILE="$SCRIPT_DIR/cursor/prompt.cursor.test.md"
  else
    PROMPT_FILE="$SCRIPT_DIR/cursor/prompt.cursor.md"
  fi
  PROMPT_TEXT=$(cat "$PROMPT_FILE")
  
  # Find cursor binary: check cursor-agent, then agent
  CURSOR_BINARY=""
  if command -v cursor-agent >/dev/null 2>&1; then
    CURSOR_BINARY="cursor-agent"
  elif command -v agent >/dev/null 2>&1; then
    CURSOR_BINARY="agent"
  else
    echo "Error: Neither 'cursor-agent' nor 'agent' binary found in PATH" >&2
    exit 1
  fi
  
  # Execute cursor with: --model auto --print --force --approve-mcps
  # stdin is automatically closed when using command substitution in bash
  # Per-iteration hard timeout (wall-clock) - kills process if exceeded
  # Note: MCP cleanup is handled by Cursor CLI itself when processes exit normally
  # If MCP processes are orphaned, they may need manual cleanup (outside scope of this script)
  if command -v timeout >/dev/null 2>&1; then
    OUTPUT=$(timeout "$CURSOR_TIMEOUT" "$CURSOR_BINARY" --model auto --print --force --approve-mcps "$PROMPT_TEXT" </dev/null 2>&1 | tee /dev/stderr) || true
    TIMEOUT_EXIT=$?
    if [[ $TIMEOUT_EXIT -eq 124 ]]; then
      echo "Warning: Cursor iteration timed out after ${CURSOR_TIMEOUT} seconds" >&2
    fi
  else
    # Fallback if timeout command is not available
    OUTPUT=$("$CURSOR_BINARY" --model auto --print --force --approve-mcps "$PROMPT_TEXT" </dev/null 2>&1 | tee /dev/stderr) || true
  fi
  
  # Check for completion signal
  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo ""
    echo "Ralph completed all tasks!"
    echo "Completed at iteration $i of $MAX_ITERATIONS"
    exit 0
  fi
  
  echo "Iteration $i complete. Continuing..."
  sleep 2
done

echo ""
echo "Ralph reached max iterations ($MAX_ITERATIONS) without completing all tasks."
echo "Check $PROGRESS_FILE for status."
exit 1
