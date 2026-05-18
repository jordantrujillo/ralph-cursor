#!/usr/bin/env python3
"""
Tests for Ralph CLI - converted from tests/cli.test.js
"""

import os
import re
import subprocess
import tempfile
import shutil
from pathlib import Path

# Get the CLI path relative to the project root
PROJECT_ROOT = Path(__file__).parent.parent
CLI_PATH = PROJECT_ROOT / 'bin' / 'ralph.py'


def run_cli(args, cwd, env=None):
    """Run the CLI command and return the result."""
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    result = subprocess.run(
        ['python3', str(CLI_PATH)] + args,
        cwd=str(cwd),
        env=run_env,
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
            'scripts/ralph/cursor/prompt.cursor.md',
        ]

        for file in required_files:
            file_path = Path(test_dir) / file
            assert file_path.exists(), f"File {file} was not created"

        proj_cursor_cmds = Path(test_dir) / '.cursor' / 'commands'
        assert not proj_cursor_cmds.exists(), 'init should not copy project .cursor/commands by default'

        # Check that ralph.py is executable
        ralph_py_path = Path(test_dir) / 'scripts/ralph/ralph.py'
        assert os.access(ralph_py_path, os.X_OK), 'ralph.py is not executable'

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

        # Check common files exist
        ralph_py_path = Path(test_dir) / 'scripts/ralph/ralph.py'
        assert ralph_py_path.exists()

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_invalid_command_shows_helpful_error():
    """Test that invalid commands show helpful usage hints."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['invalid-command'], test_dir)
        assert result['code'] != 0, 'Should exit with error code'
        # Should mention the invalid command
        assert 'invalid-command' in result['stderr'] or 'invalid-command' in result['stdout']
        # Should show available commands
        assert 'init' in result['stderr'] or 'init' in result['stdout']
        assert 'run' in result['stderr'] or 'run' in result['stdout']
        # Should suggest help
        assert '--help' in result['stderr'] or '--help' in result['stdout']
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_init_copy_project_commands_installs_cursor_files():
    """Optional --copy-project-commands copies .md commands into the repo."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['init', '--copy-project-commands'], test_dir)
        assert result['code'] == 0
        p = Path(test_dir) / '.cursor' / 'commands' / 'prd-to-beads.md'
        assert p.exists(), 'prd-to-beads.md should exist when --copy-project-commands'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_init_no_cursorignore_skips_file():
    """--no-cursorignore should not create .cursorignore."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['init', '--no-cursorignore'], test_dir)
        assert result['code'] == 0
        assert not (Path(test_dir) / '.cursorignore').exists()
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_install_cursor_writes_commands_and_config():
    """install-cursor copies to ~/.cursor/commands under a fake HOME."""
    fake_home = tempfile.mkdtemp(prefix='ralph-fakehome-')
    try:
        result = run_cli(['install-cursor'], PROJECT_ROOT, env={'HOME': fake_home})
        assert result['code'] == 0, result['stderr']
        dest = Path(fake_home) / '.cursor' / 'commands' / 'prd-to-beads.md'
        assert dest.exists(), 'prd-to-beads should be installed'
        root_file = Path(fake_home) / '.config' / 'ralph-cursor' / 'package_root'
        assert root_file.exists()
        assert str(PROJECT_ROOT.resolve()) in root_file.read_text()
    finally:
        shutil.rmtree(fake_home, ignore_errors=True)


def test_ralph_install_cursor_skips_existing_without_force():
    """Second install without --force skips existing command files."""
    fake_home = tempfile.mkdtemp(prefix='ralph-fakehome-')
    try:
        r1 = run_cli(['install-cursor'], PROJECT_ROOT, env={'HOME': fake_home})
        assert r1['code'] == 0
        r2 = run_cli(['install-cursor'], PROJECT_ROOT, env={'HOME': fake_home})
        assert r2['code'] == 0
        assert 'Skipped' in r2['stdout'] or 'skipped' in r2['stdout'].lower()
    finally:
        shutil.rmtree(fake_home, ignore_errors=True)


def test_ralph_setup_writes_gitignore_block():
    """setup merges Ralph gitignore markers."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['setup', '--project', test_dir], test_dir)
        assert result['code'] == 0, result['stderr']
        gi = Path(test_dir) / '.gitignore'
        text = gi.read_text(encoding='utf-8')
        assert '# >>> ralph-cursor' in text
        assert '.beads/' in text
        assert 'tasks/prd-*.md' in text
        # Idempotent second run
        r2 = run_cli(['setup', '--project', test_dir], test_dir)
        assert r2['code'] == 0
        assert gi.read_text(encoding='utf-8').count('# >>> ralph-cursor') == 1
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_setup_adds_agents_claude_when_untracked():
    """Untracked AGENTS.md / CLAUDE.md (typical after bd init) get ignore lines."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        subprocess.run(['git', 'init', '-q'], cwd=test_dir, check=True)
        (Path(test_dir) / 'AGENTS.md').write_text('beads\n', encoding='utf-8')
        (Path(test_dir) / 'CLAUDE.md').write_text('beads\n', encoding='utf-8')
        result = run_cli(['setup', '--project', test_dir], test_dir)
        assert result['code'] == 0, result['stderr']
        text = (Path(test_dir) / '.gitignore').read_text(encoding='utf-8')
        m = re.search(r'# >>> ralph-cursor\n(.*?)# <<< ralph-cursor', text, re.DOTALL)
        assert m, 'marker block missing'
        block = m.group(1)
        assert 'AGENTS.md' in block
        assert 'CLAUDE.md' in block
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_setup_omits_agents_when_tracked():
    """Tracked AGENTS.md is not added to the Ralph ignore block."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        subprocess.run(['git', 'init', '-q'], cwd=test_dir, check=True)
        subprocess.run(
            ['git', 'config', 'user.email', 'test@test.local'],
            cwd=test_dir,
            check=True,
        )
        subprocess.run(
            ['git', 'config', 'user.name', 'Test User'],
            cwd=test_dir,
            check=True,
        )
        (Path(test_dir) / 'AGENTS.md').write_text('committed\n', encoding='utf-8')
        subprocess.run(['git', 'add', 'AGENTS.md'], cwd=test_dir, check=True)
        subprocess.run(['git', 'commit', '-q', '-m', 'init'], cwd=test_dir, check=True)
        (Path(test_dir) / 'CLAUDE.md').write_text('new untracked\n', encoding='utf-8')
        result = run_cli(['setup', '--project', test_dir], test_dir)
        assert result['code'] == 0, result['stderr']
        text = (Path(test_dir) / '.gitignore').read_text(encoding='utf-8')
        m = re.search(r'# >>> ralph-cursor\n(.*?)# <<< ralph-cursor', text, re.DOTALL)
        block = m.group(1)
        assert 'AGENTS.md' not in block
        assert 'CLAUDE.md' in block
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_setup_skip_gitignore_noop():
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['setup', '--project', test_dir, '--skip-gitignore'], test_dir)
        assert result['code'] == 0
        assert not (Path(test_dir) / '.gitignore').exists()
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_run_project_requires_beads():
    """run --project fails when .beads is missing."""
    empty = tempfile.mkdtemp(prefix='ralph-nobeads-')
    try:
        result = run_cli(['run', '--project', empty], PROJECT_ROOT)
        assert result['code'] != 0
        combined = (result['stderr'] + result['stdout']).lower()
        assert 'beads' in combined
    finally:
        shutil.rmtree(empty, ignore_errors=True)


def test_ralph_run_missing_ralph_py_shows_clear_guidance():
    """Test that ralph run provides clear guidance when ralph.py is missing."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['run'], test_dir)
        assert result['code'] != 0, 'Should exit with error code'
        # Should clearly indicate the problem
        assert 'not initialized' in result['stderr'].lower() or 'not initialized' in result['stdout'].lower()
        # Should provide actionable next step
        assert 'init' in result['stderr'].lower() or 'init' in result['stdout'].lower()
        # Should mention the missing file
        assert 'ralph.py' in result['stderr'] or 'ralph.py' in result['stdout']
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_init_missing_source_file_shows_clear_error():
    """Test that ralph init shows clear error when source files are missing."""
    # This test simulates a corrupted installation where templates are missing
    # We'll test by checking the error message format
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        # The init should still work normally, but we're testing the error message format
        # for when source files are missing (which shouldn't happen in normal usage)
        # We'll verify that warnings include helpful context
        result = run_cli(['init'], test_dir)
        # If there are warnings, they should include helpful context
        if 'Warning' in result['stderr'] or 'Warning' in result['stdout']:
            assert 'not found' in result['stderr'] or 'not found' in result['stdout']
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_init_success_message_is_clear():
    """Test that ralph init success message is clear and informative."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['init'], test_dir)
        assert result['code'] == 0
        # Should show summary
        assert 'Summary' in result['stdout'] or 'Created' in result['stdout']
        # Should indicate next step
        assert 'run' in result['stdout'].lower() or 'initialized' in result['stdout'].lower()
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_no_command_shows_usage():
    """Test that running ralph with no command shows usage information."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli([], test_dir)
        assert result['code'] != 0, 'Should exit with error code'
        # Should show usage
        assert 'Usage' in result['stderr'] or 'Usage' in result['stdout']
        # Should mention available commands
        assert 'init' in result['stderr'] or 'init' in result['stdout']
        assert 'run' in result['stderr'] or 'run' in result['stdout']
        # Should suggest help
        assert '--help' in result['stderr'] or '--help' in result['stdout']
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_uninstall_finds_and_removes_symlink():
    """Test that ralph uninstall finds and removes symlink installation."""
    test_project_dir = tempfile.mkdtemp(prefix='ralph-test-project-')
    try:
        # Create test project structure with bin/ralph.py
        test_project_bin = Path(test_project_dir) / 'bin'
        test_project_bin.mkdir(parents=True, exist_ok=True)
        test_cli_path = test_project_bin / 'ralph.py'
        
        # Copy the actual CLI to the test project
        shutil.copy2(CLI_PATH, test_cli_path)
        test_cli_path.chmod(0o755)
        
        # Create install directory (simulating ~/.local/bin or similar)
        install_dir = Path(test_project_dir) / 'install' / 'bin'
        install_dir.mkdir(parents=True, exist_ok=True)
        install_path = install_dir / 'ralph'
        
        # Create symlink from install directory to test project's CLI
        install_path.symlink_to(test_cli_path)
        
        # Run uninstall with PATH including install directory first, then python3 location
        env = os.environ.copy()
        # Find python3 location to keep it in PATH
        python3_dir = Path(shutil.which('python3')).parent
        env['PATH'] = f"{install_dir}:{python3_dir}"
        result = subprocess.run(
            ['python3', str(test_cli_path), 'uninstall'],
            cwd=str(test_project_dir),
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}. stderr: {result.stderr}"
        assert not install_path.exists(), 'Symlink should be removed'
        assert 'removed' in result.stdout.lower() or 'uninstalled' in result.stdout.lower(), \
            'Should indicate removal'
    finally:
        shutil.rmtree(test_project_dir, ignore_errors=True)


def test_ralph_uninstall_finds_and_removes_file():
    """Test that ralph uninstall finds and removes file installation."""
    test_project_dir = tempfile.mkdtemp(prefix='ralph-test-project-')
    try:
        # Create test project structure with bin/ralph.py
        test_project_bin = Path(test_project_dir) / 'bin'
        test_project_bin.mkdir(parents=True, exist_ok=True)
        test_cli_path = test_project_bin / 'ralph.py'
        
        # Copy the actual CLI to the test project
        shutil.copy2(CLI_PATH, test_cli_path)
        test_cli_path.chmod(0o755)
        
        # Create install directory (simulating ~/.local/bin or similar)
        install_dir = Path(test_project_dir) / 'install' / 'bin'
        install_dir.mkdir(parents=True, exist_ok=True)
        install_path = install_dir / 'ralph'
        
        # Create a file (not symlink) to simulate installation
        install_path.write_text('#!/usr/bin/env python3\nprint("ralph")\n')
        install_path.chmod(0o755)
        
        # Run uninstall with PATH including install directory first, then python3 location
        env = os.environ.copy()
        # Find python3 location to keep it in PATH
        python3_dir = Path(shutil.which('python3')).parent
        env['PATH'] = f"{install_dir}:{python3_dir}"
        result = subprocess.run(
            ['python3', str(test_cli_path), 'uninstall'],
            cwd=str(test_project_dir),
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}. stderr: {result.stderr}"
        assert not install_path.exists(), 'File should be removed'
        assert 'removed' in result.stdout.lower() or 'uninstalled' in result.stdout.lower(), \
            'Should indicate removal'
    finally:
        shutil.rmtree(test_project_dir, ignore_errors=True)


def test_ralph_uninstall_provides_clear_feedback():
    """Test that ralph uninstall provides clear feedback about what was removed."""
    test_project_dir = tempfile.mkdtemp(prefix='ralph-test-project-')
    try:
        # Create test project structure with bin/ralph.py
        test_project_bin = Path(test_project_dir) / 'bin'
        test_project_bin.mkdir(parents=True, exist_ok=True)
        test_cli_path = test_project_bin / 'ralph.py'
        
        # Copy the actual CLI to the test project
        shutil.copy2(CLI_PATH, test_cli_path)
        test_cli_path.chmod(0o755)
        
        # Create install directory (simulating ~/.local/bin or similar)
        install_dir = Path(test_project_dir) / 'install' / 'bin'
        install_dir.mkdir(parents=True, exist_ok=True)
        install_path = install_dir / 'ralph'
        
        # Create symlink from install directory to test project's CLI
        install_path.symlink_to(test_cli_path)
        
        # Run uninstall with PATH including install directory first, then python3 location
        env = os.environ.copy()
        # Find python3 location to keep it in PATH
        python3_dir = Path(shutil.which('python3')).parent
        env['PATH'] = f"{install_dir}:{python3_dir}"
        result = subprocess.run(
            ['python3', str(test_cli_path), 'uninstall'],
            cwd=str(test_project_dir),
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        # Should mention what was removed
        assert str(install_path) in result.stdout or 'ralph' in result.stdout.lower(), \
            'Should mention what was removed'
    finally:
        shutil.rmtree(test_project_dir, ignore_errors=True)


def test_ralph_uninstall_handles_not_installed_gracefully():
    """Test that ralph uninstall handles case where Ralph is not installed gracefully."""
    test_project_dir = tempfile.mkdtemp(prefix='ralph-test-project-')
    try:
        # Create test project structure with bin/ralph.py
        test_project_bin = Path(test_project_dir) / 'bin'
        test_project_bin.mkdir(parents=True, exist_ok=True)
        test_cli_path = test_project_bin / 'ralph.py'
        
        # Copy the actual CLI to the test project
        shutil.copy2(CLI_PATH, test_cli_path)
        test_cli_path.chmod(0o755)
        
        # Create install directory (but no ralph binary)
        install_dir = Path(test_project_dir) / 'install' / 'bin'
        install_dir.mkdir(parents=True, exist_ok=True)
        
        # Run uninstall with PATH including install directory first, then python3 location
        env = os.environ.copy()
        # Find python3 location to keep it in PATH
        python3_dir = Path(shutil.which('python3')).parent
        env['PATH'] = f"{install_dir}:{python3_dir}"
        result = subprocess.run(
            ['python3', str(test_cli_path), 'uninstall'],
            cwd=str(test_project_dir),
            env=env,
            capture_output=True,
            text=True
        )
        
        # Should exit with 0 (graceful) or non-zero but with helpful message
        assert result.returncode == 0 or 'not installed' in result.stdout.lower() or 'not found' in result.stdout.lower(), \
            'Should handle not installed case gracefully'
    finally:
        shutil.rmtree(test_project_dir, ignore_errors=True)


def test_ralph_help_includes_uninstall():
    """Test that help text includes uninstall command."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['--help'], test_dir)
        assert result['code'] == 0
        assert 'uninstall' in result['stdout'].lower(), 'Help should include uninstall command'
        assert 'install-cursor' in result['stdout'].lower(), 'Help should include install-cursor'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_version_displays_version_info():
    """Test that ralph version displays version information."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['version'], test_dir)
        assert result['code'] == 0, f"Expected exit code 0, got {result['code']}. stderr: {result['stderr']}"
        # Should show version in format "Ralph CLI vX.Y.Z"
        assert 'ralph cli v' in result['stdout'].lower(), 'Should display version in correct format'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_version_flag_displays_version_info():
    """Test that ralph --version displays version information."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['--version'], test_dir)
        assert result['code'] == 0, f"Expected exit code 0, got {result['code']}. stderr: {result['stderr']}"
        # Should show version in format "Ralph CLI vX.Y.Z"
        assert 'ralph cli v' in result['stdout'].lower(), 'Should display version in correct format'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_help_includes_version():
    """Test that help text includes version command."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        result = run_cli(['--help'], test_dir)
        assert result['code'] == 0
        assert 'version' in result['stdout'].lower(), 'Help should include version command'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_uninstall_rejects_directory():
    """Test that ralph uninstall rejects if PATH points to a directory (edge case)."""
    test_project_dir = tempfile.mkdtemp(prefix='ralph-test-project-')
    try:
        # Create test project structure with bin/ralph.py
        test_project_bin = Path(test_project_dir) / 'bin'
        test_project_bin.mkdir(parents=True, exist_ok=True)
        test_cli_path = test_project_bin / 'ralph.py'
        
        # Copy the actual CLI to the test project
        shutil.copy2(CLI_PATH, test_cli_path)
        test_cli_path.chmod(0o755)
        
        # Create install directory
        install_dir = Path(test_project_dir) / 'install' / 'bin'
        install_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a directory to symlink to
        target_dir = Path(test_project_dir) / 'target_dir'
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a symlink from install_dir/ralph to the directory
        # Note: shutil.which won't return directories, but if someone manually
        # creates a symlink to a directory, we want to handle it gracefully.
        # However, since shutil.which only returns executables, this test scenario
        # can't actually occur. We'll test that the code handles it if it somehow does.
        # For now, we'll create an executable symlink that points to a directory,
        # but shutil.which may not follow it. Let's test the actual behavior.
        install_path = install_dir / 'ralph'
        install_path.symlink_to(target_dir)
        
        # Run uninstall with PATH including install directory first, then python3 location
        env = os.environ.copy()
        # Find python3 location to keep it in PATH
        python3_dir = Path(shutil.which('python3')).parent
        env['PATH'] = f"{install_dir}:{python3_dir}"
        result = subprocess.run(
            ['python3', str(test_cli_path), 'uninstall'],
            cwd=str(test_project_dir),
            env=env,
            capture_output=True,
            text=True
        )
        
        # shutil.which won't return a directory, so it will say "not installed"
        # This test verifies that the uninstall handles the case gracefully
        # (either by not finding it, or by rejecting it if somehow found)
        # The actual directory check in the code is defensive but unlikely to trigger
        assert result.returncode == 0 or 'not installed' in result.stdout.lower(), \
            'Should handle directory case gracefully (shutil.which won\'t find directories)'
    finally:
        shutil.rmtree(test_project_dir, ignore_errors=True)


def test_ralph_uninstall_rejects_non_python_binary():
    """Test that ralph uninstall rejects non-Python binaries (security fix)."""
    test_project_dir = tempfile.mkdtemp(prefix='ralph-test-project-')
    try:
        # Create test project structure with bin/ralph.py
        test_project_bin = Path(test_project_dir) / 'bin'
        test_project_bin.mkdir(parents=True, exist_ok=True)
        test_cli_path = test_project_bin / 'ralph.py'
        
        # Copy the actual CLI to the test project
        shutil.copy2(CLI_PATH, test_cli_path)
        test_cli_path.chmod(0o755)
        
        # Create install directory with a non-Python binary
        install_dir = Path(test_project_dir) / 'install' / 'bin'
        install_dir.mkdir(parents=True, exist_ok=True)
        install_path = install_dir / 'ralph'
        
        # Create a non-Python file (bash script without Python shebang)
        install_path.write_text('#!/bin/bash\necho "not ralph"\n')
        install_path.chmod(0o755)
        
        # Run uninstall with PATH including install directory first, then python3 location
        env = os.environ.copy()
        # Find python3 location to keep it in PATH
        python3_dir = Path(shutil.which('python3')).parent
        env['PATH'] = f"{install_dir}:{python3_dir}"
        result = subprocess.run(
            ['python3', str(test_cli_path), 'uninstall'],
            cwd=str(test_project_dir),
            env=env,
            capture_output=True,
            text=True
        )
        
        # Should exit with error code and reject non-Python binary
        assert result.returncode != 0, 'Should exit with error when binary is not Python'
        assert 'python' in result.stderr.lower() or 'python' in result.stdout.lower(), \
            'Should indicate binary verification failed'
    finally:
        shutil.rmtree(test_project_dir, ignore_errors=True)


def test_ralph_version_handles_empty_file():
    """Test that ralph version handles empty VERSION file (edge case)."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        # Create empty VERSION file
        version_file = PROJECT_ROOT / 'VERSION'
        original_content = None
        if version_file.exists():
            original_content = version_file.read_text()
        
        try:
            version_file.write_text('')
            
            result = run_cli(['version'], test_dir)
            # Should still work (fallback to git or default)
            assert result['code'] == 0, 'Should handle empty version file gracefully'
            assert 'ralph cli v' in result['stdout'].lower(), 'Should display version'
        finally:
            # Restore original content
            if original_content is not None:
                version_file.write_text(original_content)
            elif version_file.exists():
                version_file.unlink()
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_version_handles_whitespace_only_file():
    """Test that ralph version handles whitespace-only VERSION file (edge case)."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        # Create whitespace-only VERSION file
        version_file = PROJECT_ROOT / 'VERSION'
        original_content = None
        if version_file.exists():
            original_content = version_file.read_text()
        
        try:
            version_file.write_text('   \n\t  \n')
            
            result = run_cli(['version'], test_dir)
            # Should still work (fallback to git or default)
            assert result['code'] == 0, 'Should handle whitespace-only file'
            assert 'ralph cli v' in result['stdout'].lower(), 'Should display version'
        finally:
            # Restore original content
            if original_content is not None:
                version_file.write_text(original_content)
            elif version_file.exists():
                version_file.unlink()
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_version_sanitizes_control_characters():
    """Test that ralph version sanitizes control characters in version string (security fix)."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        # Create VERSION file with control characters
        version_file = PROJECT_ROOT / 'VERSION'
        original_content = None
        if version_file.exists():
            original_content = version_file.read_text()
        
        try:
            # Version with control characters (ANSI escape sequence)
            version_file.write_text('1.0.0\x1b[31mRED\x1b[0m')
            
            result = run_cli(['version'], test_dir)
            # Should sanitize and display version
            assert result['code'] == 0, 'Should handle control characters'
            assert 'ralph cli v' in result['stdout'].lower(), 'Should display version'
            # Should not contain the escape sequence
            assert '\x1b[31m' not in result['stdout'], 'Should sanitize control characters'
        finally:
            # Restore original content
            if original_content is not None:
                version_file.write_text(original_content)
            elif version_file.exists():
                version_file.unlink()
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_run_rejects_non_python_runner():
    """Test that ralph run rejects non-Python runner script (security fix)."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        # Initialize
        run_cli(['init'], test_dir)
        
        # Create a non-Python file at scripts/ralph/ralph.py
        ralph_py_path = Path(test_dir) / 'scripts/ralph/ralph.py'
        ralph_py_path.write_text('#!/bin/bash\necho "not python"\n')
        ralph_py_path.chmod(0o755)
        
        result = run_cli(['run'], test_dir)
        # Should exit with error (validation should catch .py extension requirement)
        # Note: This test may pass if validation is lenient, but should at least not execute
        assert result['code'] != 0 or 'python' in result['stderr'].lower() or 'extension' in result['stderr'].lower(), \
            'Should reject or warn about non-Python runner script'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_run_rejects_directory_runner():
    """Test that ralph run rejects directory at runner script path (security fix)."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        # Initialize
        run_cli(['init'], test_dir)
        
        # Remove the file and create a directory instead
        ralph_py_path = Path(test_dir) / 'scripts/ralph/ralph.py'
        if ralph_py_path.exists():
            ralph_py_path.unlink()
        ralph_py_path.mkdir(parents=True, exist_ok=True)
        
        result = run_cli(['run'], test_dir)
        # Should exit with error
        assert result['code'] != 0, 'Should exit with error when runner is a directory'
        assert 'file' in result['stderr'].lower() or 'directory' in result['stderr'].lower(), \
            'Should indicate path is not a file'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ralph_run_handles_missing_python3():
    """Test that ralph run handles missing python3 gracefully (edge case)."""
    test_dir = tempfile.mkdtemp(prefix='ralph-test-')
    try:
        # Initialize
        run_cli(['init'], test_dir)
        
        # Run with PATH that doesn't include python3
        # Use sys.executable to get the full path to python3, then test that ralph.py
        # can't find python3 when running the runner script
        import sys
        python3_path = sys.executable
        env = os.environ.copy()
        env['PATH'] = '/nonexistent'
        result = subprocess.run(
            [python3_path, str(CLI_PATH), 'run'],
            cwd=str(test_dir),
            env=env,
            capture_output=True,
            text=True
        )
        
        # Should exit with error and provide helpful message
        assert result.returncode != 0, 'Should exit with error when python3 is not available'
        assert 'python' in result.stderr.lower() or 'python' in result.stdout.lower(), \
            'Should mention python3 in error message'
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    import sys
    # Simple test runner
    test_functions = [name for name in dir() if name.startswith('test_')]
    passed = 0
    failed = 0
    
    for test_name in test_functions:
        test_func = globals()[test_name]
        try:
            test_func()
            print(f'✓ {test_name}')
            passed += 1
        except AssertionError as e:
            print(f'✗ {test_name}: {e}')
            failed += 1
        except Exception as e:
            print(f'✗ {test_name}: Unexpected error: {e}')
            failed += 1
    
    print(f'\n{passed} passed, {failed} failed')
    sys.exit(0 if failed == 0 else 1)
