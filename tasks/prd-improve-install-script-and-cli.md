# PRD: Improve Install Script and CLI

## Introduction

Improve the Ralph install script and CLI to fix bugs, enhance reliability, and provide better user experience. This includes better error handling, clearer feedback messages, and adding essential missing features like an uninstall command. The improvements focus on macOS and Linux platforms.

## Goals

- Fix bugs and improve reliability in install script and CLI
- Enhance user experience with clearer messages and better feedback
- Add `ralph uninstall` command to remove Ralph from PATH
- Improve error handling and edge case coverage
- Ensure consistent behavior across macOS and Linux

## Phases

### Phase 1: Install Script Improvements
**Description:** Improve the install script with better error handling, dependency detection, and PATH configuration guidance. This phase focuses on making the installation process more reliable and user-friendly. Includes quality assurance review for all changes in this phase.

**Branch:** `ralph/improve-install-script-and-cli-phase-1` (branched from current branch)

**User Stories:**
- US-001: Improve install script error handling and feedback
- US-005: Improve install script dependency detection and installation
- US-006: Improve install script PATH detection and guidance
- US-007: Code Review - Edge Case Analysis
- US-008: Security Review - Production Hardening
- US-009: Test Review - Quality Assurance

### Phase 2: CLI Improvements and New Commands
**Description:** Enhance the CLI with better error handling and add essential missing commands (uninstall and version). This phase builds on the existing CLI to provide a more complete and user-friendly experience. Includes quality assurance review for all changes in this phase.

**Branch:** `ralph/improve-install-script-and-cli-phase-2` (built on top of phase-1 branch)

**User Stories:**
- US-002: Improve CLI error handling and user feedback
- US-003: Add ralph uninstall command
- US-004: Add ralph version command
- US-010: Code Review - Edge Case Analysis
- US-011: Security Review - Production Hardening
- US-012: Test Review - Quality Assurance

## User Stories

### Phase 1: Install Script Improvements

### US-001: Improve install script error handling and feedback
**Description:** As a user, I want the install script to provide clear, actionable error messages and handle edge cases gracefully so that installation failures are easy to diagnose and fix.

**Acceptance Criteria:**
- [ ] Write failing test(s) first (TDD Red phase) - test error scenarios (missing bin/ralph.py, permission errors, etc.)
- [ ] Implement minimal code to pass tests (TDD Green phase) - improve error messages with specific guidance
- [ ] Refactor code while keeping tests passing (TDD Refactor phase)
- [ ] All error messages include actionable next steps
- [ ] Handle edge cases: missing directories, permission denied, symlink failures
- [ ] Provide clear success/failure indicators with colored output
- [ ] Script exits with appropriate exit codes (0 for success, non-zero for errors)
- [ ] Typecheck/lint passes

### US-005: Improve install script dependency detection and installation
**Description:** As a user, I want the install script to reliably detect and install dependencies with better feedback so that setup is smooth and predictable.

**Acceptance Criteria:**
- [ ] Write failing test(s) first (TDD Red phase) - test dependency detection and installation flows
- [ ] Implement minimal code to pass tests (TDD Green phase) - improve dependency handling
- [ ] Refactor code while keeping tests passing (TDD Refactor phase)
- [ ] Dependency detection works reliably on macOS and Linux
- [ ] Installation commands handle failures gracefully
- [ ] Clear progress indicators during dependency installation
- [ ] Better handling of unsupported platforms with helpful messages
- [ ] Verify dependencies after installation attempt
- [ ] Typecheck/lint passes

### US-006: Improve install script PATH detection and guidance
**Description:** As a user, I want the install script to accurately detect PATH issues and provide platform-specific guidance so that I can fix PATH configuration easily.

**Acceptance Criteria:**
- [ ] Write failing test(s) first (TDD Red phase) - test PATH detection for different shell configurations
- [ ] Implement minimal code to pass tests (TDD Green phase) - improve PATH detection logic
- [ ] Refactor code while keeping tests passing (TDD Refactor phase)
- [ ] Script detects current shell (bash, zsh, fish) and provides appropriate config file
- [ ] PATH detection works for both interactive and non-interactive shells
- [ ] Provides platform-specific instructions (macOS vs Linux)
- [ ] Offers to add PATH automatically if possible (with user confirmation)
- [ ] Clear instructions for manual PATH configuration
- [ ] Typecheck/lint passes

### US-007: Code Review - Edge Case Analysis
**Description:** As a code reviewer specialist, I want to review all changes in the branch for potential edge case bugs so that critical issues are fixed and non-critical ones are documented.

**Acceptance Criteria:**
- [ ] Review all code changes in the branch for edge cases
- [ ] Fix all critical edge case bugs found
- [ ] Document non-critical edge cases in markdown format
- [ ] Follow best practices for code review and edge case analysis
- [ ] Typecheck/lint passes

### US-008: Security Review - Production Hardening
**Description:** As a code security specialist, I want to review all code created/modified in the branch for security vulnerabilities so that the code is hardened for production use. I want to fix critical issues found, write a report on critical issues that were found/fixed. I don't want to fix the medium and minor issues, but we do want to document them.

**Acceptance Criteria:**
- [ ] Review all code created/modified in the branch for security vulnerabilities
- [ ] Identify and fix security issues (command injection, path traversal, etc.)
- [ ] Ensure proper input validation and sanitization
- [ ] Verify secure handling of user input and file operations
- [ ] Follow security best practices and OWASP guidelines
- [ ] Typecheck/lint passes
- [ ] Security report is written/saved to `tasks/improve-install-script-and-cli/security-report-phase-1.md`

### US-009: Test Review - Quality Assurance
**Description:** As a test-driven development specialist, I want to review all tests in the branch to ensure they follow TDD best practices, are comprehensive, not "cheated", and cover normal use cases and all known edge cases. And fix any issues found.

**Acceptance Criteria:**
- [ ] Verify TDD workflow was followed: tests were written BEFORE implementation code (Red-Green-Refactor cycle)
- [ ] Review all tests created/modified in the branch
- [ ] Verify tests are not "cheated" (no false positives, proper assertions), like skipping tests or deleting tests that are relevant to the changes, or writing tests that are not relevant to the changes
- [ ] Ensure tests were written first and failed initially (Red phase), then implementation made them pass (Green phase)
- [ ] Verify no implementation code exists without corresponding tests
- [ ] Ensure tests cover normal use cases
- [ ] Ensure tests cover all known edge cases
- [ ] Verify test quality follows TDD best practices (tests define behavior, not just verify implementation)
- [ ] Confirm tests are maintainable and well-structured
- [ ] Typecheck/lint passes

### Phase 2: CLI Improvements and New Commands

### US-002: Improve CLI error handling and user feedback
**Description:** As a user, I want the CLI to provide clear error messages and helpful feedback so that I understand what went wrong and how to fix it.

**Acceptance Criteria:**
- [ ] Write failing test(s) first (TDD Red phase) - test error scenarios (invalid commands, missing files, etc.)
- [ ] Implement minimal code to pass tests (TDD Green phase) - improve error messages throughout CLI
- [ ] Refactor code while keeping tests passing (TDD Refactor phase)
- [ ] All error messages are user-friendly and include context
- [ ] Invalid commands show helpful usage hints
- [ ] Missing dependencies or files provide clear guidance
- [ ] Success messages are clear and informative
- [ ] Typecheck/lint passes

### US-003: Add ralph uninstall command
**Description:** As a user, I want to uninstall Ralph from my system so that I can cleanly remove it when no longer needed.

**Acceptance Criteria:**
- [ ] Write failing test(s) first (TDD Red phase) - test uninstall command finds and removes installation
- [ ] Implement minimal code to pass tests (TDD Green phase) - add `handle_uninstall()` function
- [ ] Refactor code while keeping tests passing (TDD Refactor phase)
- [ ] `ralph uninstall` command finds Ralph installation in PATH
- [ ] Command removes symlink or file from install directory
- [ ] Command provides clear feedback about what was removed
- [ ] Command handles case where Ralph is not installed gracefully
- [ ] Command works on both macOS and Linux
- [ ] Help text includes uninstall command
- [ ] Typecheck/lint passes

### US-004: Add ralph version command
**Description:** As a user, I want to check the installed version of Ralph so that I can verify my installation and troubleshoot version-related issues.

**Acceptance Criteria:**
- [ ] Write failing test(s) first (TDD Red phase) - test version command outputs version info
- [ ] Implement minimal code to pass tests (TDD Green phase) - add version detection and display
- [ ] Refactor code while keeping tests passing (TDD Refactor phase)
- [ ] `ralph version` or `ralph --version` displays version information
- [ ] Version can be read from a version file or git tag
- [ ] Command shows version in format: "Ralph CLI vX.Y.Z"
- [ ] Help text includes version command
- [ ] Typecheck/lint passes

### US-010: Code Review - Edge Case Analysis
**Description:** As a code reviewer specialist, I want to review all changes in the branch for potential edge case bugs so that critical issues are fixed and non-critical ones are documented.

**Acceptance Criteria:**
- [ ] Review all code changes in the branch for edge cases
- [ ] Fix all critical edge case bugs found
- [ ] Document non-critical edge cases in markdown format
- [ ] Follow best practices for code review and edge case analysis
- [ ] Typecheck/lint passes

### US-011: Security Review - Production Hardening
**Description:** As a code security specialist, I want to review all code created/modified in the branch for security vulnerabilities so that the code is hardened for production use. I want to fix critical issues found, write a report on critical issues that were found/fixed. I don't want to fix the medium and minor issues, but we do want to document them.

**Acceptance Criteria:**
- [ ] Review all code created/modified in the branch for security vulnerabilities
- [ ] Identify and fix security issues (command injection, path traversal, etc.)
- [ ] Ensure proper input validation and sanitization
- [ ] Verify secure handling of user input and file operations
- [ ] Follow security best practices and OWASP guidelines
- [ ] Typecheck/lint passes
- [ ] Security report is written/saved to `tasks/improve-install-script-and-cli/security-report-phase-2.md`

### US-012: Test Review - Quality Assurance
**Description:** As a test-driven development specialist, I want to review all tests in the branch to ensure they follow TDD best practices, are comprehensive, not "cheated", and cover normal use cases and all known edge cases. And fix any issues found.

**Acceptance Criteria:**
- [ ] Verify TDD workflow was followed: tests were written BEFORE implementation code (Red-Green-Refactor cycle)
- [ ] Review all tests created/modified in the branch
- [ ] Verify tests are not "cheated" (no false positives, proper assertions), like skipping tests or deleting tests that are relevant to the changes, or writing tests that are not relevant to the changes
- [ ] Ensure tests were written first and failed initially (Red phase), then implementation made them pass (Green phase)
- [ ] Verify no implementation code exists without corresponding tests
- [ ] Ensure tests cover normal use cases
- [ ] Ensure tests cover all known edge cases
- [ ] Verify test quality follows TDD best practices (tests define behavior, not just verify implementation)
- [ ] Confirm tests are maintainable and well-structured
- [ ] Typecheck/lint passes

## Functional Requirements

- FR-1: Install script must provide clear, actionable error messages for all failure scenarios
- FR-2: Install script must handle permission errors gracefully with helpful guidance
- FR-3: CLI must show helpful error messages for invalid commands and missing dependencies
- FR-4: `ralph uninstall` command must remove Ralph from PATH and provide confirmation
- FR-5: `ralph version` command must display version information
- FR-6: Install script must detect and install dependencies reliably on macOS and Linux
- FR-7: Install script must detect current shell and provide appropriate PATH configuration instructions
- FR-8: All commands must work consistently on macOS and Linux platforms

## Non-Goals

- No Windows support (out of scope for this iteration)
- No GUI or interactive TUI interface
- No configuration file management
- No automatic updates or version checking
- No plugin or extension system
- No comprehensive test suite rewrite (only add tests for new/changed functionality)

## Design Considerations

- Maintain backward compatibility with existing installations
- Use consistent color coding (red for errors, yellow for warnings, green for success)
- Follow existing code style and patterns
- Keep error messages concise but informative
- Ensure all user-facing text is clear and non-technical where possible

## Technical Considerations

- Install script is bash, must work with bash 3.2+ (macOS default) and modern bash on Linux
- CLI is Python 3, must work with Python 3.6+
- Must handle symlinks correctly (install script creates symlinks)
- Must detect installation location reliably (~/.local/bin or /usr/local/bin)
- PATH detection must work for common shells: bash, zsh, fish
- Version information can be stored in a simple version file or extracted from git

## Success Metrics

- Installation success rate improves (fewer user-reported installation issues)
- Error messages are clear enough that users can self-resolve 90% of issues
- Uninstall command works reliably on both macOS and Linux
- All new functionality has test coverage
- No regressions in existing functionality

## Open Questions

- Should version be stored in a file, extracted from git, or both?
- Should uninstall command remove dependencies or just the Ralph binary?
- Should we add a `ralph status` command to check installation health?
- Should install script offer to automatically add PATH to shell config?
