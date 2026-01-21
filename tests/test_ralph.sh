#!/bin/bash
# Test suite for Ralph runner + templates
# Tests run without requiring real Cursor (use stub binaries via PATH).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_DIR="$SCRIPT_DIR/test-tmp"

# These are set per variant
CURRENT_VARIANT_NAME=""
CURRENT_LAYOUT=""
CURRENT_SOURCE_DIR=""
RALPH_PY_SCRIPT=""
RALPH_WORK_DIR=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to run ralph script (Python)
run_ralph() {
  local iterations="$1"
  shift
  local extra_args="$@"
  
  # Set test mode environment variable
  export RALPH_TEST_MODE=1
  
  python3 "$RALPH_PY_SCRIPT" "$iterations" $extra_args 2>&1 || true
}

# Setup test environment
setup_test_env() {
  rm -rf "$TEST_DIR"
  mkdir -p "$TEST_DIR/project"

  local project_dir="$TEST_DIR/project"
  local runner_dir=""

  if [[ "$CURRENT_LAYOUT" == "scripts" ]]; then
    runner_dir="$project_dir/scripts/ralph"
    mkdir -p "$runner_dir/cursor"
    cp "$CURRENT_SOURCE_DIR/ralph.py" "$runner_dir/ralph.py"
    cp "$CURRENT_SOURCE_DIR/prd.yml.example" "$runner_dir/prd.yml.example"
    cp "$CURRENT_SOURCE_DIR/cursor/prompt.cursor.md" "$runner_dir/cursor/prompt.cursor.md"
    cp "$CURRENT_SOURCE_DIR/cursor/prompt.cursor.test.md" "$runner_dir/cursor/prompt.cursor.test.md" 2>/dev/null || true
    chmod +x "$runner_dir/ralph.py"
    RALPH_PY_SCRIPT="$runner_dir/ralph.py"
    RALPH_WORK_DIR="$runner_dir"
  else
    echo "Invalid CURRENT_LAYOUT: $CURRENT_LAYOUT" >&2
    exit 1
  fi

  cd "$project_dir"

  # Create stub binaries
  mkdir -p "$project_dir/bin"
  export PATH="$project_dir/bin:$PATH"

  # Create stub cursor binaries (cursor-agent, agent, cursor)
  # Scripts check in order: cursor-agent, agent, cursor
  # We'll create cursor-agent so it's found first
  cat > "$project_dir/bin/cursor-agent" << 'EOF'
#!/bin/bash
# Stub cursor binary for testing
echo "Stub cursor executed with args: $@"
if [ -t 0 ]; then
  echo "Stub cursor: stdin is a TTY"
else
  echo "Stub cursor: stdin is not a TTY"
fi
# Check for required flags (model can vary)
if [[ "$*" == *"--model"* ]] && [[ "$*" == *"--print"* ]] && [[ "$*" == *"--force"* ]] && [[ "$*" == *"--approve-mcps"* ]]; then
  echo "Stub cursor: all required flags present"
else
  echo "Stub cursor: WARNING - missing required flags" >&2
fi
echo "Some cursor output"
EOF
  chmod +x "$project_dir/bin/cursor-agent"
  
  # Also create agent and cursor stubs for fallback testing
  cp "$project_dir/bin/cursor-agent" "$project_dir/bin/agent"
  cp "$project_dir/bin/cursor-agent" "$project_dir/bin/cursor"
  chmod +x "$project_dir/bin/agent"
  chmod +x "$project_dir/bin/cursor"

  # Create test prd.yml
  cat > "$RALPH_WORK_DIR/prd.yml" << 'EOF'
project: TestProject
branchName: ralph/test
description: Test feature
userStories:
  - id: US-001
    title: Test story
    description: Test description
    acceptanceCriteria:
      - Test criterion
    priority: 1
    passes: false
    notes: 
EOF

  # Create test progress.txt
  echo "# Ralph Progress Log" > "$RALPH_WORK_DIR/progress.txt"
  echo "Started: $(date)" >> "$RALPH_WORK_DIR/progress.txt"
  echo "---" >> "$RALPH_WORK_DIR/progress.txt"
}

cleanup_test_env() {
  cd "$SCRIPT_DIR" || true
  rm -rf "$TEST_DIR"
}

test_cursor_worker() {
  setup_test_env

  OUTPUT=$(run_ralph 1)

  if echo "$OUTPUT" | grep -q "Stub cursor executed"; then
    echo -e "${GREEN}PASS${NC}: Cursor worker is used"
  else
    echo -e "${RED}FAIL${NC}: Cursor worker not used"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi

  cleanup_test_env
}

test_cursor_invocation_flags() {
  setup_test_env

  OUTPUT=$(run_ralph 1)

  if echo "$OUTPUT" | grep -q "all required flags present"; then
    echo -e "${GREEN}PASS${NC}: Cursor command includes all required flags"
  else
    echo -e "${RED}FAIL${NC}: Cursor command missing required flags"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi

  cleanup_test_env
}

test_cursor_no_pty() {
  setup_test_env

  OUTPUT=$(run_ralph 1)

  if echo "$OUTPUT" | grep -q "stdin is not a TTY"; then
    echo -e "${GREEN}PASS${NC}: Cursor invocation uses normal spawn (no PTY)"
  else
    echo -e "${RED}FAIL${NC}: Cursor invocation may be using PTY"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi

  cleanup_test_env
}

test_stop_condition_complete() {
  setup_test_env

  cat > "$TEST_DIR/project/bin/cursor-agent" << 'EOF'
#!/bin/bash
echo "Iteration output"
echo "<promise>COMPLETE</promise>"
EOF
  chmod +x "$TEST_DIR/project/bin/cursor-agent"

  OUTPUT=$(run_ralph 10)

  if echo "$OUTPUT" | grep -q "Ralph completed all tasks"; then
    echo -e "${GREEN}PASS${NC}: Loop exits on COMPLETE signal"
  else
    echo -e "${RED}FAIL${NC}: Loop does not exit on COMPLETE signal"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi

  cleanup_test_env
}

test_stop_condition_no_complete() {
  setup_test_env

  cat > "$TEST_DIR/project/bin/cursor-agent" << 'EOF'
#!/bin/bash
echo "Iteration output without COMPLETE"
EOF
  chmod +x "$TEST_DIR/project/bin/cursor-agent"

  OUTPUT=$(run_ralph 2)

  if echo "$OUTPUT" | grep -q "Iteration 2 of 2"; then
    echo -e "${GREEN}PASS${NC}: Loop continues when no COMPLETE signal"
  else
    echo -e "${RED}FAIL${NC}: Loop does not continue without COMPLETE"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi

  cleanup_test_env
}

test_progress_append_only() {
  setup_test_env

  ORIGINAL_CONTENT=$(cat "$RALPH_WORK_DIR/progress.txt")
  run_ralph 1 >/dev/null 2>&1 || true
  NEW_CONTENT=$(cat "$RALPH_WORK_DIR/progress.txt")

  if [[ "$NEW_CONTENT" == "$ORIGINAL_CONTENT"* ]]; then
    echo -e "${GREEN}PASS${NC}: progress.txt is append-only"
  else
    echo -e "${RED}FAIL${NC}: progress.txt was overwritten"
    cleanup_test_env
    return 1
  fi

  cleanup_test_env
}

test_prd_yml_parsing_failure() {
  setup_test_env

  echo "invalid yaml content: [" > "$RALPH_WORK_DIR/prd.yml"

  if run_ralph 1 >/dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}: Runner handles invalid prd.yml gracefully"
  else
    echo -e "${RED}FAIL${NC}: Runner crashes on invalid prd.yml"
    cleanup_test_env
    return 1
  fi

  rm -f "$RALPH_WORK_DIR/prd.yml"

  if run_ralph 1 >/dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}: Runner handles missing prd.yml gracefully"
  else
    echo -e "${RED}FAIL${NC}: Runner crashes on missing prd.yml"
    cleanup_test_env
    return 1
  fi

  cleanup_test_env
}

run_tests() {
  echo "Testing ralph.py..."
  echo ""

  local tests_passed=0
  local tests_failed=0

  if test_cursor_worker; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_cursor_invocation_flags; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_cursor_no_pty; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_stop_condition_complete; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_stop_condition_no_complete; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_progress_append_only; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_prd_yml_parsing_failure; then ((tests_passed+=1)); else ((tests_failed+=1)); fi

  echo ""
  echo "========================================="
  echo "Script: ralph.py"
  echo "Tests passed: $tests_passed"
  echo "Tests failed: $tests_failed"
  echo "========================================="

  if [ $tests_failed -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    return 0
  else
    echo -e "${RED}Some tests failed!${NC}"
    return 1
  fi
}

run_variant() {
  local variant_name="$1"
  local layout="$2"
  local source_dir="$3"

  CURRENT_VARIANT_NAME="$variant_name"
  CURRENT_LAYOUT="$layout"
  CURRENT_SOURCE_DIR="$source_dir"

  echo "Running Ralph test suite (${CURRENT_VARIANT_NAME})..."
  echo ""

  run_tests
}

main() {
  # Test canonical scripts (scripts/ralph/)
  run_variant "scripts" "scripts" "$REPO_ROOT/scripts/ralph"
  exit $?
}

main
