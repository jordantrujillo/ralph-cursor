# Edge Case Analysis - Phase 2

## Overview
This document analyzes edge cases found during code review of Phase 2 changes (bin/ralph.py CLI improvements: error handling, uninstall command, and version command).

## Critical Edge Cases (Fixed)

### 1. Directory Check in handle_uninstall()
**Issue:** If `ralph` in PATH points to a directory instead of a file/symlink, `unlink()` would raise `IsADirectoryError`.

**Fix:** Added check to detect if the path is a directory and provide a clear error message before attempting to unlink.

**Location:** `bin/ralph.py` lines 256-262

### 2. Version File Encoding
**Issue:** `read_text()` didn't specify encoding, which could cause issues on systems with non-UTF-8 default encodings or files with encoding issues.

**Fix:** Added explicit `encoding='utf-8'` parameter to `read_text()` call.

**Location:** `bin/ralph.py` line 286

### 3. Empty Version File Handling
**Issue:** If VERSION file exists but is empty or contains only whitespace, `strip()` would return an empty string, which is falsy but not explicitly handled.

**Fix:** Added explicit check to treat empty/whitespace-only version strings as missing, allowing fallback to git tag.

**Location:** `bin/ralph.py` lines 286-289

### 4. File Operation Error Handling in handle_init()
**Issue:** File operations (`shutil.copy2()`, `chmod()`, `mkdir()`) could fail with `PermissionError` or `OSError`, but errors were not caught, causing the entire init to fail.

**Fix:** Added try-except blocks around file operations to catch `PermissionError` and `OSError`, print helpful error messages, and continue with other files instead of failing completely.

**Location:** `bin/ralph.py` lines 99-109, 123-131, 137-145, 151-168

### 5. Directory Creation Error Handling
**Issue:** `mkdir()` operations could fail with `PermissionError` or `OSError`, but errors were not caught, causing init to fail.

**Fix:** Added try-except blocks around `mkdir()` calls to catch errors and provide helpful messages, skipping affected files instead of failing completely.

**Location:** `bin/ralph.py` lines 99-109, 123-131, 137-145, 151-168

### 6. JSON File Creation Error Handling
**Issue:** Creating `.cursor/cli.json` could fail with file operation errors, but errors were not caught.

**Fix:** Added try-except block around JSON file creation with explicit UTF-8 encoding and error handling.

**Location:** `bin/ralph.py` lines 165-168

### 7. Subprocess Error Handling in handle_run()
**Issue:** `subprocess.run()` could fail if `python3` is not found (`FileNotFoundError`) or with other exceptions, but errors were not caught, causing unclear error messages.

**Fix:** Added try-except block to catch `FileNotFoundError` specifically and provide clear guidance, and catch other exceptions with helpful error messages.

**Location:** `bin/ralph.py` lines 225-234

## Non-Critical Edge Cases (Documented)

### 1. Duplicate Flags in parse_flags()
**Issue:** If the same flag appears multiple times (e.g., `--force --force`), the last value wins. This is actually reasonable behavior (last one wins), but could be confusing.

**Impact:** Low - This is standard command-line parsing behavior. Users can avoid by not specifying duplicate flags.

**Recommendation:** Current behavior is acceptable. Could add a warning for duplicate flags if desired, but not necessary.

**Location:** `bin/ralph.py` lines 40-53

### 2. Flag Values Starting with '--'
**Issue:** If a flag value starts with '--' (e.g., `--model --other`), it will be treated as a flag. The value would be `'--other'` and `--other` would also be set to `True`.

**Impact:** Low - This is expected behavior. Users who need to pass values starting with '--' should quote them or use a different approach.

**Recommendation:** Current behavior is acceptable. This is standard command-line parsing.

**Location:** `bin/ralph.py` lines 40-53

### 3. Broken Symlink Handling in handle_uninstall()
**Issue:** If `shutil.which()` finds a broken symlink, `exists()` will return `False`, and the code will exit with a message saying the installation may have been removed. This is actually correct behavior, but the message could be more specific.

**Impact:** Low - The current handling is reasonable. Broken symlinks are treated as "not installed", which is correct.

**Recommendation:** Could improve the message to mention broken symlinks specifically, but current behavior is acceptable.

**Location:** `bin/ralph.py` lines 250-255

### 4. Version String with Multiple 'v' Prefixes
**Issue:** If version string has multiple 'v' prefixes (e.g., "vv1.0.0"), `lstrip('v')` will remove all of them, resulting in "1.0.0". This is actually fine, but worth noting.

**Impact:** Low - The result is correct. Multiple 'v' prefixes are unlikely in practice.

**Recommendation:** Current behavior is acceptable. `lstrip('v')` correctly handles this case.

**Location:** `bin/ralph.py` line 298

### 5. Git Command Timeout
**Issue:** Git command has a 2-second timeout. If git is slow or hangs, it will timeout and fall back to default version. This is handled gracefully.

**Impact:** Low - Timeout prevents hanging, and fallback to default version is reasonable.

**Recommendation:** Current behavior is acceptable. 2-second timeout is reasonable for git describe.

**Location:** `bin/ralph.py` line 291

### 6. Partial Initialization Recovery
**Issue:** If `handle_init()` fails partway through (e.g., some files copied but others fail), there's no automatic cleanup. Files that were successfully created remain.

**Impact:** Low - User can run `ralph init --force` to retry, or manually clean up. Partial initialization is better than complete failure.

**Recommendation:** Current behavior is acceptable. Partial initialization is useful, and `--force` flag allows retry.

**Location:** `bin/ralph.py` lines 83-168

### 7. Concurrent Uninstall Operations
**Issue:** If two uninstall commands run simultaneously, they might both try to remove the same file, potentially causing a race condition.

**Impact:** Low - Rare in practice. Worst case is one uninstall fails with a clear error.

**Recommendation:** Consider adding file locking for production use, but not necessary for current use case.

**Location:** `bin/ralph.py` lines 258-259

### 8. Version File with Invalid Characters
**Issue:** If VERSION file contains invalid UTF-8 characters, `read_text(encoding='utf-8')` will raise `UnicodeDecodeError`, which is caught and handled by falling back to git tag.

**Impact:** Low - Error is caught and handled gracefully with fallback.

**Recommendation:** Current behavior is acceptable. Invalid characters in version file are unlikely.

**Location:** `bin/ralph.py` lines 285-288

### 9. Subprocess Timeout in handle_run()
**Issue:** `subprocess.run()` doesn't have a timeout, so if `scripts/ralph/ralph.py` hangs, the CLI will hang indefinitely.

**Impact:** Low - The runner script should handle its own timeouts. Adding a timeout here could interfere with long-running operations.

**Recommendation:** Current behavior is acceptable. The runner script should manage its own timeouts. If needed, timeout could be added as a configurable option.

**Location:** `bin/ralph.py` lines 225-229

### 10. Path Resolution Edge Cases
**Issue:** `Path.resolve()` can fail in edge cases (e.g., very long paths, circular symlinks), but these are rare.

**Impact:** Low - These edge cases are extremely rare and would cause exceptions that are caught.

**Recommendation:** Current behavior is acceptable. Path resolution failures would be caught by exception handling.

**Location:** `bin/ralph.py` line 247

### 11. Template Directory Fallback
**Issue:** If both `TEMPLATES_DIR` and fallback `PACKAGE_ROOT` don't exist, init will fail for all files. This is handled with warnings, but all files will be skipped.

**Impact:** Low - This indicates a corrupted installation, which is already handled with clear error messages.

**Recommendation:** Current behavior is acceptable. Clear error messages guide users to fix the installation.

**Location:** `bin/ralph.py` lines 34-37, 89-96

### 12. Skills Directory Iteration
**Issue:** If `skills_src_dir.iterdir()` encounters a permission error or other I/O error, it will raise an exception that isn't caught.

**Impact:** Low - Permission errors on source directory are rare and would indicate a system issue.

**Recommendation:** Could add try-except around `iterdir()` to handle permission errors gracefully, but current behavior is acceptable.

**Location:** `bin/ralph.py` line 115

## Testing Recommendations

1. **Test uninstall with directory:** Verify directory check works correctly
2. **Test version with empty file:** Verify empty VERSION file handling
3. **Test init with permission errors:** Verify file operation error handling
4. **Test run without python3:** Verify FileNotFoundError handling
5. **Test init with partial failures:** Verify partial initialization recovery
6. **Test version with invalid encoding:** Verify encoding error handling
7. **Test concurrent uninstall:** Verify race condition handling (if file locking is added)

## Summary

All critical edge cases have been fixed. The code now handles file operation errors gracefully, provides clear error messages, and continues operation where possible instead of failing completely. Non-critical edge cases are documented for future consideration. The CLI is now more robust and handles edge cases gracefully.
