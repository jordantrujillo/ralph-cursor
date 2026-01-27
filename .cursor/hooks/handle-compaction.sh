#!/bin/bash
# Hook script to handle context compaction
# Called by Cursor's preCompact hook before context window compaction occurs

set -euo pipefail

# Read JSON input from stdin
input=$(cat)
if [ -z "$input" ]; then
    echo "{}" >&2
    exit 0
fi

# Parse JSON input using jq (if available) or basic parsing
parse_json() {
    local key="$1"
    if command -v jq >/dev/null 2>&1; then
        echo "$input" | jq -r ".$key // empty"
    else
        # Basic grep-based parsing as fallback (not perfect but works for simple cases)
        echo "$input" | grep -o "\"$key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | sed 's/.*"\([^"]*\)".*/\1/' || echo ""
    fi
}

# Get values from input
transcript_path=$(parse_json "transcript_path")
workspace_roots=$(parse_json "workspace_roots")
context_usage_percent=$(parse_json "context_usage_percent")
conversation_id=$(parse_json "conversation_id")

# Get project root (first workspace root)
project_root="${CURSOR_PROJECT_DIR:-}"
if [ -z "$project_root" ] && [ -n "$workspace_roots" ]; then
    # Try to extract first workspace root from JSON
    if command -v jq >/dev/null 2>&1; then
        project_root=$(echo "$workspace_roots" | jq -r '.[0] // empty' 2>/dev/null || echo "")
    fi
fi
if [ -z "$project_root" ]; then
    project_root="."
fi

# Signal file path
signal_file="${project_root}/.ralph-compact-signal"
task_file="${project_root}/.ralph-current-task"

# Get current task ID from environment variable or file
task_id="${RALPH_CURRENT_TASK_ID:-}"
if [ -z "$task_id" ] && [ -f "$task_file" ]; then
    task_id=$(cat "$task_file" 2>/dev/null | head -n1 | tr -d '\n' || echo "")
fi

# Extract learnings from transcript if available
learnings=""
if [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
    # Extract recent agent messages/thoughts from transcript
    # Look for patterns like "Assistant:", "Thinking:", or similar
    # Get last 2000 characters as learnings summary
    if command -v tail >/dev/null 2>&1; then
        learnings=$(tail -c 2000 "$transcript_path" 2>/dev/null | head -c 1000 || echo "")
    fi
fi

# If no learnings extracted, create a basic message
if [ -z "$learnings" ]; then
    learnings="Context compaction triggered at ${context_usage_percent}% usage. Conversation ID: ${conversation_id}"
fi

# Add comment to Beads task if task_id is available
if [ -n "$task_id" ] && command -v bd >/dev/null 2>&1; then
    # Escape learnings for shell (replace newlines with spaces, escape quotes)
    safe_learnings=$(echo "$learnings" | tr '\n' ' ' | sed "s/'/'\"'\"'/g")
    
    # Create comment message
    comment="Context compaction detected (${context_usage_percent}% usage). Learnings: ${safe_learnings}"
    
    # Add comment to Beads task
    if bd comments add "$task_id" "$comment" >/dev/null 2>&1; then
        echo "Added learnings to Beads task: $task_id" >&2
    else
        echo "Warning: Failed to add comment to Beads task: $task_id" >&2
    fi
else
    if [ -z "$task_id" ]; then
        echo "Warning: No current task ID found (RALPH_CURRENT_TASK_ID or .ralph-current-task)" >&2
    fi
    if ! command -v bd >/dev/null 2>&1; then
        echo "Warning: Beads CLI (bd) not found in PATH" >&2
    fi
fi

# Create signal file to notify Ralph
touch "$signal_file"
echo "{\"task_id\":\"${task_id}\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"context_usage_percent\":${context_usage_percent}}" > "$signal_file"

# Output user message (optional - shown in Cursor UI)
cat <<EOF
{
  "user_message": "Context compaction detected (${context_usage_percent}% usage). Learnings saved to Beads task. Ralph will restart with fresh context."
}
EOF

exit 0
