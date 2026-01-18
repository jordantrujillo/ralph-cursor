#!/usr/bin/env python3
"""
Tests for Ralph CLI - converted from tests/cli.test.js
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path

# Get the CLI path relative to the project root
PROJECT_ROOT = Path(__file__).parent.parent
CLI_PATH = PROJECT_ROOT / 'bin' / 'ralph.py'


def run_cli(args, cwd):
    """Run the CLI command and return the result."""
    result = subprocess.run(
        ['python3', str(CLI_PATH)] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True
    )
    return {
        'code': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr
    }


def test_ralph_init_creates_directory_and_files():
    """Test that ralph init creates scripts/ralph/ directory and files."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['init'], test_dir)
        assert result['code'] == 0, f"Expected exit code 0, got {result['code']}. stderr: {result['stderr']}"

        # Check that required files were created
        required_files = [
            'scripts/ralph/ralph.py',
            'scripts/ralph/prd.yml.example',
            'scripts/ralph/cursor/prompt.cursor.md',
            'scripts/ralph/cursor/prompt.convert-to-prd-yml.md',
            'scripts/ralph/cursor/convert-to-prd-yml.sh',
        ]

        for file in required_files:
            file_path = Path(test_dir) / file
            assert file_path.exists(), f"File {file} was not created"

        # Check that ralph.py is executable
        ralph_py_path = Path(test_dir) / 'scripts/ralph/ralph.py'
        assert os.access(ralph_py_path, os.X_OK), 'ralph.py is not executable'

        # Check that convert-to-prd-yml.sh is executable
        convert_script_path = Path(test_dir) / 'scripts/ralph/cursor/convert-to-prd-yml.sh'
        assert os.access(convert_script_path, os.X_OK), 'convert-to-prd-yml.sh is not executable'

        assert 'Created' in result['stdout'] or 'file' in result['stdout'], 'Should show files were created'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_init_does_not_overwrite_existing_files():
    """Test that ralph init does not overwrite existing files by default."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        # First init
        run_cli(['init'], test_dir)

        # Read original content
        ralph_py_path = Path(test_dir) / 'scripts/ralph/ralph.py'
        original_content = ralph_py_path.read_text()

        # Modify the file
        modified_content = original_content + '\n# Modified'
        ralph_py_path.write_text(modified_content)

        # Run init again
        result = run_cli(['init'], test_dir)
        assert result['code'] == 0

        # Check that file was not overwritten
        current_content = ralph_py_path.read_text()
        assert current_content == modified_content, 'File should not be overwritten'
        assert 'Skipped' in result['stdout'], 'Should show files were skipped'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_init_force_overwrites_existing_files():
    """Test that ralph init --force overwrites existing files."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        # First init
        run_cli(['init'], test_dir)

        # Modify the file
        ralph_py_path = Path(test_dir) / 'scripts/ralph/ralph.py'
        modified_content = '# Modified'
        ralph_py_path.write_text(modified_content)

        # Run init with --force
        result = run_cli(['init', '--force'], test_dir)
        assert result['code'] == 0

        # Check that file was overwritten (should have original content, not modified)
        current_content = ralph_py_path.read_text()
        assert current_content != modified_content, 'File should be overwritten'
        assert len(current_content) > len(modified_content), 'File should have original content'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_run_invokes_repo_local_runner():
    """Test that ralph run invokes repo-local runner."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        # Initialize
        run_cli(['init'], test_dir)

        # Create stub runner that just prints a message
        stub_runner = """#!/usr/bin/env python3
import sys
print("STUB_RUNNER_CALLED")
print(f"ITERATIONS: {sys.argv[1] if len(sys.argv) > 1 else '10'}")
sys.exit(0)
"""
        ralph_py_path = Path(test_dir) / 'scripts/ralph/ralph.py'
        ralph_py_path.write_text(stub_runner)
        ralph_py_path.chmod(0o755)

        # Create stub binaries directory
        bin_dir = Path(test_dir) / 'bin'
        bin_dir.mkdir(parents=True, exist_ok=True)

        # Run with modified PATH
        env = os.environ.copy()
        env['PATH'] = f"{bin_dir}:{env.get('PATH', '')}"
        result = subprocess.run(
            ['python3', str(CLI_PATH), 'run', '5'],
            cwd=str(test_dir),
            env=env,
            capture_output=True,
            text=True
        )

        assert 'STUB_RUNNER_CALLED' in result.stdout, 'Runner should be invoked'
        assert 'ITERATIONS: 5' in result.stdout, 'Iterations should be passed'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_run_executes_ralph_py():
    """Test that ralph run executes ralph.py."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        # Initialize
        run_cli(['init'], test_dir)

        # Create stub runner
        stub_runner = """#!/usr/bin/env python3
import sys
print("STUB_RUNNER_CALLED")
print(f"ITERATIONS: {sys.argv[1] if len(sys.argv) > 1 else '10'}")
sys.exit(0)
"""
        ralph_py_path = Path(test_dir) / 'scripts/ralph/ralph.py'
        ralph_py_path.write_text(stub_runner)
        ralph_py_path.chmod(0o755)

        # Create stub cursor binary
        bin_dir = Path(test_dir) / 'bin'
        bin_dir.mkdir(parents=True, exist_ok=True)

        stub_cursor = """#!/bin/bash
echo "stub cursor"
exit 0
"""
        cursor_path = bin_dir / 'cursor'
        cursor_path.write_text(stub_cursor)
        cursor_path.chmod(0o755)

        # Run with cursor worker
        env = os.environ.copy()
        env['PATH'] = f"{bin_dir}:{env.get('PATH', '')}"
        result = subprocess.run(
            ['python3', str(CLI_PATH), 'run'],
            cwd=str(test_dir),
            env=env,
            capture_output=True,
            text=True
        )

        assert 'STUB_RUNNER_CALLED' in result.stdout, 'Runner should be invoked'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_run_fails_if_not_initialized():
    """Test that ralph run fails if not initialized."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['run'], test_dir)
        assert result['code'] != 0, 'Should exit with error code'
        assert 'not initialized' in result['stderr'] or 'not initialized' in result['stdout'], \
            'Should indicate Ralph is not initialized'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_init_installs_cursor_files():
    """Test that ralph init installs cursor files."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['init'], test_dir)
        assert result['code'] == 0

        # Check cursor files exist
        cursor_prompt_path = Path(test_dir) / 'scripts/ralph/cursor/prompt.cursor.md'
        assert cursor_prompt_path.exists()

        convert_script_path = Path(test_dir) / 'scripts/ralph/cursor/convert-to-prd-yml.sh'
        assert convert_script_path.exists()

        # Check common files exist
        ralph_py_path = Path(test_dir) / 'scripts/ralph/ralph.py'
        assert ralph_py_path.exists()

        prd_example_path = Path(test_dir) / 'scripts/ralph/prd.yml.example'
        assert prd_example_path.exists()
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
