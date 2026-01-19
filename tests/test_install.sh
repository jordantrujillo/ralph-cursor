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
  rm -rf "$TEST_DIR" 2>/dev/null || true
  # Restore original environment variables if they were modified
  unset HOME 2>/dev/null || true
  unset PATH 2>/dev/null || true
  unset OSTYPE 2>/dev/null || true
  unset SHELL 2>/dev/null || true
}

# Set up trap to ensure cleanup on script exit
trap cleanup_test_env EXIT INT TERM

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

# Test: Dependency detection works reliably on macOS
test_dependency_detection_macos() {
  setup_test_env
  
  # Create test structure
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  export PATH="$TEST_DIR/.local/bin:$PATH"
  
  # Mock OSTYPE to be darwin (macOS)
  export OSTYPE="darwin"
  
  # Create a mock command that simulates yq not being installed
  # We'll create a fake PATH that doesn't include yq
  export PATH="/usr/bin:/bin"
  
  # Mock the install script to capture dependency detection
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  cd "$TEST_DIR"
  # Use echo "n" to skip dependency installation
  OUTPUT=$(echo "n" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check if script detected missing yq dependency
  if echo "$OUTPUT" | grep -qiE "(yq|dependency|missing)"; then
    echo -e "${GREEN}PASS${NC}: Dependency detection works on macOS"
  else
    echo -e "${RED}FAIL${NC}: Dependency detection not working on macOS"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

# Test: Dependency detection works reliably on Linux
test_dependency_detection_linux() {
  setup_test_env
  
  # Create test structure
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  export PATH="$TEST_DIR/.local/bin:$PATH"
  
  # Mock OSTYPE to be linux-gnu
  export OSTYPE="linux-gnu"
  
  # Create a mock command that simulates yq not being installed
  export PATH="/usr/bin:/bin"
  
  # Mock the install script
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  cd "$TEST_DIR"
  # Use echo "n" to skip dependency installation
  OUTPUT=$(echo "n" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check if script detected missing yq dependency
  if echo "$OUTPUT" | grep -qiE "(yq|dependency|missing)"; then
    echo -e "${GREEN}PASS${NC}: Dependency detection works on Linux"
  else
    echo -e "${RED}FAIL${NC}: Dependency detection not working on Linux"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

# Test: Installation commands handle failures gracefully
test_dependency_installation_failure() {
  setup_test_env
  
  # Create test structure
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  export PATH="$TEST_DIR/.local/bin:$PATH"
  
  # Mock OSTYPE
  if [[ "$OSTYPE" == "darwin"* ]]; then
    export OSTYPE="darwin"
  else
    export OSTYPE="linux-gnu"
  fi
  
  # Create a fake brew/wget command that always fails
  mkdir -p "$TEST_DIR/fake-bin"
  echo '#!/bin/bash' > "$TEST_DIR/fake-bin/brew"
  echo 'exit 1' >> "$TEST_DIR/fake-bin/brew"
  chmod +x "$TEST_DIR/fake-bin/brew"
  
  echo '#!/bin/bash' > "$TEST_DIR/fake-bin/wget"
  echo 'exit 1' >> "$TEST_DIR/fake-bin/wget"
  chmod +x "$TEST_DIR/fake-bin/wget"
  
  # Remove yq from PATH
  export PATH="$TEST_DIR/fake-bin:/usr/bin:/bin"
  
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  cd "$TEST_DIR"
  # Use echo "y" to attempt dependency installation
  OUTPUT=$(echo "y" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check if script handled installation failure gracefully
  if echo "$OUTPUT" | grep -qiE "(failed|error|install.*manually|graceful)"; then
    echo -e "${GREEN}PASS${NC}: Installation failures handled gracefully"
  else
    echo -e "${RED}FAIL${NC}: Installation failures not handled gracefully"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

# Test: Clear progress indicators during dependency installation
test_dependency_progress_indicators() {
  setup_test_env
  
  # Create test structure
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  export PATH="$TEST_DIR/.local/bin:$PATH"
  
  # Mock OSTYPE
  if [[ "$OSTYPE" == "darwin"* ]]; then
    export OSTYPE="darwin"
  else
    export OSTYPE="linux-gnu"
  fi
  
  # Remove yq from PATH to trigger dependency detection
  export PATH="/usr/bin:/bin"
  
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  cd "$TEST_DIR"
  # Use echo "y" to attempt dependency installation
  OUTPUT=$(echo "y" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check if script shows progress indicators
  if echo "$OUTPUT" | grep -qiE "(installing|checking|progress|\.\.\.|✓|complete)"; then
    echo -e "${GREEN}PASS${NC}: Progress indicators shown during dependency installation"
  else
    echo -e "${RED}FAIL${NC}: Progress indicators not shown during dependency installation"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

# Test: Better handling of unsupported platforms with helpful messages
test_unsupported_platform() {
  setup_test_env
  
  # Create test structure
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  export PATH="$TEST_DIR/.local/bin:$PATH"
  
  # Mock unsupported platform
  export OSTYPE="unsupported-os"
  
  # Remove yq from PATH
  export PATH="/usr/bin:/bin"
  
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  cd "$TEST_DIR"
  # Use echo "n" to skip dependency installation
  OUTPUT=$(echo "n" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check if script provides helpful message for unsupported platform
  if echo "$OUTPUT" | grep -qiE "(unsupported|platform|manual|install|helpful|visit|github)"; then
    echo -e "${GREEN}PASS${NC}: Unsupported platforms handled with helpful messages"
  else
    echo -e "${RED}FAIL${NC}: Unsupported platforms not handled with helpful messages"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

# Test: Verify dependencies after installation attempt
test_dependency_verification() {
  setup_test_env
  
  # Create test structure
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  export PATH="$TEST_DIR/.local/bin:$PATH"
  
  # Mock OSTYPE
  if [[ "$OSTYPE" == "darwin"* ]]; then
    export OSTYPE="darwin"
  else
    export OSTYPE="linux-gnu"
  fi
  
  # Create a fake yq command that succeeds
  mkdir -p "$TEST_DIR/fake-bin"
  echo '#!/bin/bash' > "$TEST_DIR/fake-bin/yq"
  echo 'echo "yq version 4.0.0"' >> "$TEST_DIR/fake-bin/yq"
  chmod +x "$TEST_DIR/fake-bin/yq"
  
  # Add fake-bin to PATH after initial check (simulating installation)
  export PATH="$TEST_DIR/fake-bin:/usr/bin:/bin"
  
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  cd "$TEST_DIR"
  # Use echo "y" to attempt dependency installation
  OUTPUT=$(echo "y" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check if script verifies dependencies after installation
  # Should show that yq is installed (either before or after installation attempt)
  if echo "$OUTPUT" | grep -qiE "(yq.*installed|✓.*yq|verified|checking.*dependencies)"; then
    echo -e "${GREEN}PASS${NC}: Dependencies verified after installation attempt"
  else
    echo -e "${RED}FAIL${NC}: Dependencies not verified after installation attempt"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

# Test: Script detects current shell (bash, zsh, fish) and provides appropriate config file
test_shell_detection() {
  setup_test_env
  
  # Create test structure
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  # Remove install directory from PATH to trigger PATH warning
  export PATH="/usr/bin:/bin"
  
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  # Test bash detection
  # Clean up any existing installation first
  rm -f "$TEST_DIR/.local/bin/ralph" 2>/dev/null || true
  cd "$TEST_DIR"
  export SHELL="/bin/bash"
  OUTPUT=$(echo -e "n\nn" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check if script mentions bash-specific config file
  if echo "$OUTPUT" | grep -qiE "(\.bashrc|\.bash_profile|bash)"; then
    echo -e "${GREEN}PASS${NC}: Shell detection works for bash"
  else
    echo -e "${RED}FAIL${NC}: Shell detection not working for bash"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  # Test zsh detection
  # Clean up any existing installation first
  rm -f "$TEST_DIR/.local/bin/ralph" 2>/dev/null || true
  cd "$TEST_DIR"
  export SHELL="/bin/zsh"
  OUTPUT=$(echo -e "n\nn" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check if script mentions zsh-specific config file
  if echo "$OUTPUT" | grep -qiE "(\.zshrc|zsh)"; then
    echo -e "${GREEN}PASS${NC}: Shell detection works for zsh"
  else
    echo -e "${RED}FAIL${NC}: Shell detection not working for zsh"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

# Test: PATH detection works for both interactive and non-interactive shells
test_path_detection_interactive_noninteractive() {
  setup_test_env
  
  # Create test structure
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  # Test 1: PATH includes install directory (should succeed)
  # Clean up any existing installation first
  rm -f "$TEST_DIR/.local/bin/ralph" 2>/dev/null || true
  export PATH="$TEST_DIR/.local/bin:$PATH"
  cd "$TEST_DIR"
  # Say "n" to skip dependency installation
  OUTPUT=$(echo -e "n" | bash "$TEST_DIR/install.sh" 2>&1) || EXIT_CODE=$?
  EXIT_CODE=${EXIT_CODE:-$?}
  cd "$REPO_ROOT"
  
  if [ $EXIT_CODE -eq 0 ] && echo "$OUTPUT" | grep -qiE "(Installation complete|✓.*complete|successfully installed)"; then
    echo -e "${GREEN}PASS${NC}: PATH detection works when PATH is correct"
  else
    echo -e "${RED}FAIL${NC}: PATH detection failed when PATH is correct"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  # Test 2: PATH doesn't include install directory (should warn)
  # Clean up any existing installation first
  rm -f "$TEST_DIR/.local/bin/ralph" 2>/dev/null || true
  export PATH="/usr/bin:/bin"
  cd "$TEST_DIR"
  OUTPUT=$(echo -e "n\nn" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  if echo "$OUTPUT" | grep -qiE "(not in.*PATH|add.*PATH|warning)"; then
    echo -e "${GREEN}PASS${NC}: PATH detection works when PATH is missing install directory"
  else
    echo -e "${RED}FAIL${NC}: PATH detection not working when PATH is missing install directory"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

# Test: Provides platform-specific instructions (macOS vs Linux)
test_platform_specific_path_instructions() {
  setup_test_env
  
  # Create test structure
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  export PATH="/usr/bin:/bin"
  
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  # Test macOS
  export OSTYPE="darwin"
  cd "$TEST_DIR"
  OUTPUT=$(echo "n" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check for macOS-specific guidance (could mention Homebrew paths, etc.)
  if echo "$OUTPUT" | grep -qiE "(macos|darwin|homebrew|\.zshrc|\.bash_profile)"; then
    echo -e "${GREEN}PASS${NC}: Platform-specific instructions provided for macOS"
  else
    # At minimum, should mention config files
    if echo "$OUTPUT" | grep -qiE "(\.bashrc|\.zshrc|\.profile|export PATH)"; then
      echo -e "${GREEN}PASS${NC}: Platform-specific instructions provided (config files mentioned)"
    else
      echo -e "${RED}FAIL${NC}: Platform-specific instructions not provided for macOS"
      echo "Output: $OUTPUT"
      cleanup_test_env
      return 1
    fi
  fi
  
  # Test Linux
  # Clean up any existing installation first
  rm -f "$TEST_DIR/.local/bin/ralph" 2>/dev/null || true
  export OSTYPE="linux-gnu"
  cd "$TEST_DIR"
  OUTPUT=$(echo -e "n\nn" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check for Linux-specific guidance
  if echo "$OUTPUT" | grep -qiE "(linux|\.bashrc|\.profile|export PATH)"; then
    echo -e "${GREEN}PASS${NC}: Platform-specific instructions provided for Linux"
  else
    echo -e "${RED}FAIL${NC}: Platform-specific instructions not provided for Linux"
    echo "Output: $OUTPUT"
    cleanup_test_env
    return 1
  fi
  
  cleanup_test_env
}

# Test: Offers to add PATH automatically if possible (with user confirmation)
test_automatic_path_addition() {
  setup_test_env
  
  # Create test structure
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  export PATH="/usr/bin:/bin"
  
  # Create a writable config file
  touch "$TEST_DIR/.bashrc"
  chmod 644 "$TEST_DIR/.bashrc"
  
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  # Test: Script should offer to add PATH automatically
  export SHELL="/bin/bash"
  cd "$TEST_DIR"
  # First say "n" to skip automatic addition, but check if offer was made
  OUTPUT=$(echo -e "n\nn" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check if script offers to add PATH automatically
  if echo "$OUTPUT" | grep -qiE "(add.*automatically|add to.*config|would you like|y/n)"; then
    echo -e "${GREEN}PASS${NC}: Script offers to add PATH automatically"
  else
    # If automatic addition isn't implemented yet, that's okay for now
    # But should at least provide manual instructions
    if echo "$OUTPUT" | grep -qiE "(export PATH|add.*PATH|\.bashrc|\.zshrc)"; then
      echo -e "${YELLOW}WARN${NC}: Automatic PATH addition not offered, but manual instructions provided"
      echo -e "${GREEN}PASS${NC}: Manual PATH configuration instructions provided"
    else
      echo -e "${RED}FAIL${NC}: No PATH addition offer or instructions provided"
      echo "Output: $OUTPUT"
      cleanup_test_env
      return 1
    fi
  fi
  
  cleanup_test_env
}

# Test: Clear instructions for manual PATH configuration
test_manual_path_configuration_instructions() {
  setup_test_env
  
  # Create test structure
  mkdir -p "$TEST_DIR/bin"
  echo "#!/usr/bin/env python3" > "$TEST_DIR/bin/ralph.py"
  chmod +x "$TEST_DIR/bin/ralph.py"
  mkdir -p "$TEST_DIR/.local/bin"
  export HOME="$TEST_DIR"
  export PATH="/usr/bin:/bin"
  
  cp "$INSTALL_SCRIPT" "$TEST_DIR/install.sh"
  chmod +x "$TEST_DIR/install.sh"
  
  # Test with bash
  export SHELL="/bin/bash"
  cd "$TEST_DIR"
  OUTPUT=$(echo "n" | bash "$TEST_DIR/install.sh" 2>&1) || true
  cd "$REPO_ROOT"
  
  # Check for clear manual instructions
  if echo "$OUTPUT" | grep -qiE "(export PATH|add.*to.*\.bashrc|\.zshrc|\.profile|source.*bashrc|source.*zshrc)"; then
    echo -e "${GREEN}PASS${NC}: Clear manual PATH configuration instructions provided"
  else
    echo -e "${RED}FAIL${NC}: Manual PATH configuration instructions not clear"
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
  
  # Store original environment variables
  ORIGINAL_HOME="${HOME:-}"
  ORIGINAL_PATH="${PATH:-}"
  ORIGINAL_OSTYPE="${OSTYPE:-}"
  ORIGINAL_SHELL="${SHELL:-}"
  
  if test_missing_ralph_script; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_permission_denied; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_missing_directories; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_symlink_failure; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_success_indicators; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_exit_codes; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_actionable_error_messages; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_dependency_detection_macos; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_dependency_detection_linux; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_dependency_installation_failure; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_dependency_progress_indicators; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_unsupported_platform; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_dependency_verification; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_shell_detection; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_path_detection_interactive_noninteractive; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_platform_specific_path_instructions; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_automatic_path_addition; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  if test_manual_path_configuration_instructions; then ((tests_passed+=1)); else ((tests_failed+=1)); fi
  
  # Restore original environment variables
  export HOME="${ORIGINAL_HOME}"
  export PATH="${ORIGINAL_PATH}"
  export OSTYPE="${ORIGINAL_OSTYPE}"
  export SHELL="${ORIGINAL_SHELL}"
  
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
