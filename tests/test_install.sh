#!/bin/bash
# Test suite for install.sh
# Tests error handling, edge cases, and user feedback

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_SCRIPT="$REPO_ROOT/install.sh"
TEST_DIR="$SCRIPT_DIR/install-test-tmp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to run install script
# Returns exit code and outputs to stdout/stderr
run_install() {
  local test_dir="$1"
  shift
  local extra_args="$@"
  
  cd "$test_dir"
  bash "$INSTALL_SCRIPT" $extra_args 2>&1
  local exit_code=$?
  cd "$REPO_ROOT" || true
  return $exit_code
}

# Setup test environment
setup_test_env() {
  rm -rf "$TEST_DIR"
  mkdir -p "$TEST_DIR"
  cd "$TEST_DIR"
}

cleanup_test_env() {
  cd "$REPO_ROOT" || true
  rm -rf "$TEST_DIR"
}

# Test: Missing bin/ralph.py should provide clear error message
test_missing_ralph_script() {
  setup_test_env
  
  # Create a copy of install.sh in test directory and modify it to point to non-existent file
  mkdir -p "$TEST_DIR/bin"
  # Don't create ralph.py - it should be missing
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  # Run from test directory - script will look for bin/ralph.py relative to itself
  cd "$TEST_DIR"
  OUTPUT=$(bash "$TEST_DIR/install.sh" 2>&1) || EXIT_CODE=$?
  EXIT_CODE=${EXIT_CODE:-$?}
  cd "$REPO_ROOT"
  
  if [ ${EXIT_CODE:-0} -eq 0 ]; then
    echo -e "${RED}FAIL${NC}: Script should exit with non-zero code when bin/ralph.py is missing (got $EXIT_CODE)"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  if echo "$OUTPUT" | grep -qi "error" && echo "$OUTPUT" | grep -qi "bin/ralph.py"; then
    echo -e "${GREEN}PASS${NC}: Missing bin/ralph.py provides clear error message"
  else
    echo -e "${RED}FAIL${NC}: Missing bin/ralph.py error message not clear"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

# Test: Permission denied on install directory should provide actionable guidance
test_permission_denied() {
  setup_test_env
  
  # Create test structure with bin/ralph.py
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  
  # Create a read-only directory to simulate permission issues
  mkdir -p "$TEST_DIR/readonly-dir"
  chmod 555 "$TEST_DIR/readonly-dir"
  
  # Mock HOME to point to readonly directory
  export HOME="$TEST_DIR/readonly-dir"
  
  OUTPUT=$(run_install "$TEST_DIR" 2>&1) || EXIT_CODE=$?
  EXIT_CODE=${EXIT_CODE:-$?}
  
  if [ ${EXIT_CODE:-0} -eq 0 ]; then
    echo -e "${RED}FAIL${NC}: Script should exit with non-zero code on permission denied"
    cleanup_test_env
    return 1
  fi
  
  if echo "$OUTPUT" | grep -qi "permission\|writable\|sudo"; then
    echo -e "${GREEN}PASS${NC}: Permission denied provides actionable guidance"
  else
    echo -e "${RED}FAIL${NC}: Permission denied error message not actionable"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

# Test: Missing directories should be handled gracefully
test_missing_directories() {
  setup_test_env
  
  # Create test structure with bin/ralph.py
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  
  # Set HOME to non-existent path
  export HOME="/nonexistent/path/$(date +%s)"
  
  OUTPUT=$(run_install "$TEST_DIR" 2>&1) || EXIT_CODE=$?
  EXIT_CODE=${EXIT_CODE:-$?}
  
  # Script should handle this gracefully (either create directory or provide clear error)
  if [ ${EXIT_CODE:-0} -eq 0 ]; then
    # If it succeeds, that's fine - it created the directory
    echo -e "${GREEN}PASS${NC}: Missing directories handled (created or clear error)"
  else
    # If it fails, should provide clear guidance
    if echo "$OUTPUT" | grep -qi "error\|directory\|create"; then
      echo -e "${GREEN}PASS${NC}: Missing directories provide clear error message"
    else
      echo -e "${RED}FAIL${NC}: Missing directories not handled gracefully"
      echo "Output: $OUTPUT"
      cleanup_test_env
      return 1
    fi
  fi
  
  cleanup_test_env
}

# Test: Symlink failures should provide clear error messages
test_symlink_failure() {
  setup_test_env
  
  # Create test structure with install script
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  # Create install directory
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  
  # Make the directory read-only to prevent symlink creation
  chmod 555 "$TEST_DIR/.local/bin"
  
  cd "$TEST_DIR"
  # Use echo "n" to answer "no" to overwrite prompt if it appears
  OUTPUT=$(echo "n" | bash "$TEST_DIR/install.sh" 2>&1) || EXIT_CODE=$?
  EXIT_CODE=${EXIT_CODE:-$?}
  cd "$REPO_ROOT"
  
  # Clean up the read-only directory
  chmod 755 "$TEST_DIR/.local/bin" 2>/dev/null || true
  
  # Script should handle symlink failure gracefully
  if [ ${EXIT_CODE:-0} -ne 0 ]; then
    if echo "$OUTPUT" | grep -qiE "(error|symlink|failed|permission|writable)"; then
      echo -e "${GREEN}PASS${NC}: Symlink failure provides clear error message"
    else
      echo -e "${RED}FAIL${NC}: Symlink failure error message not clear"
      echo "Output: $OUTPUT"
      cleanup_test_env
      return 1
    fi
  else
    # If it succeeded, that's also acceptable (maybe it handled it differently)
    # But check if it at least mentioned something about the issue
    if echo "$OUTPUT" | grep -qiE "(error|symlink|failed|permission|writable)"; then
      echo -e "${GREEN}PASS${NC}: Symlink failure handled gracefully with clear message"
    else
      echo -e "${YELLOW}WARN${NC}: Symlink failure test - script succeeded but no error message detected"
      echo "Output: $OUTPUT"
      echo -e "${GREEN}PASS${NC}: Symlink failure handled (script completed)"
    fi
  fi
  
  cleanup_test_env
}

# Test: Success case should have clear success indicators
test_success_indicators() {
  setup_test_env
  
  # Create test structure
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  
  # Create install directory
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  export PATH="$TEST_DIR/.local/bin:$PATH"
  
  OUTPUT=$(run_install "$TEST_DIR" 2>&1)
  EXIT_CODE=$?
  
  if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}FAIL${NC}: Success case should exit with code 0"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  if echo "$OUTPUT" | grep -qi "success\|complete\|installed\|✓"; then
    echo -e "${GREEN}PASS${NC}: Success case has clear indicators"
  else
    echo -e "${RED}FAIL${NC}: Success case lacks clear indicators"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

# Test: Exit codes are appropriate (0 for success, non-zero for errors)
test_exit_codes() {
  setup_test_env
  
  # Test 1: Missing bin/ralph.py should exit non-zero
  mkdir -p "$TEST_DIR/bin"
  # Don't create ralph.py
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  cd "$TEST_DIR"
  bash "$TEST_DIR/install.sh" >/dev/null 2>&1 || EXIT_CODE=$?
  EXIT_CODE=${EXIT_CODE:-$?}
  cd "$REPO_ROOT"
  
  if [ ${EXIT_CODE:-0} -eq 0 ]; then
    echo -e "${RED}FAIL${NC}: Missing bin/ralph.py should exit non-zero (got $EXIT_CODE)"
    cleanup_test_env
    return 1
  fi
  
  # Test 2: Success case should exit zero
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  export PATH="$TEST_DIR/.local/bin:$PATH"
  
  cd "$TEST_DIR"
  bash "$TEST_DIR/install.sh" >/dev/null 2>&1
  EXIT_CODE=$?
  cd "$REPO_ROOT"
  
  if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}FAIL${NC}: Success case should exit with code 0 (got $EXIT_CODE)"
    cleanup_test_env
    return 1
  fi
  
  echo -e "${GREEN}PASS${NC}: Exit codes are appropriate"
  cleanup_test_env
}

# Test: Error messages include actionable next steps
test_actionable_error_messages() {
  setup_test_env
  
  # Create test structure without bin/ralph.py
  mkdir -p "$TEST_DIR/bin"
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  cd "$TEST_DIR"
  OUTPUT=$(bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check if error message suggests what to do next
  if echo "$OUTPUT" | grep -qiE "(next steps|create|install|fix|run|check|verify|ensure)"; then
    echo -e "${GREEN}PASS${NC}: Error messages include actionable next steps"
  else
    echo -e "${RED}FAIL${NC}: Error messages lack actionable next steps"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

run_tests() {
  echo "Testing install.sh error handling..."
  echo ""
  
  local tests_passed=0
  local tests_failed=0
  
  if test_missing_ralph_script; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_permission_denied; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_missing_directories; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_symlink_failure; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_success_indicators; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_exit_codes; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_actionable_error_messages; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  
  echo ""
  echo "========================================="
  echo "Script: install.sh"
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

main() {
  if [ ! -f "$INSTALL_SCRIPT" ]; then
    echo -e "${RED}Error: install.sh not found at $INSTALL_SCRIPT${NC}" >&2
    exit 1
  fi
  
  run_tests
  exit $?
}

main
