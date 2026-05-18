#!/usr/bin/env python3
"""
Ralph CLI - Autonomous AI agent loop installer and runner

Commands:
  install-cursor  Copy global Cursor slash commands to ~/.cursor/commands/ (bootstrap)
  init            Initialize Ralph in the current repository (legacy in-repo runner)
  setup           Merge Ralph .gitignore block into a project
  run             Run Ralph agent loop [--project DIR for portable mode]
  uninstall, version

Init options:
  --force, --cursor-cli, --copy-project-commands, --no-cursorignore

Run options:
  --project DIR   Use bundled runner with cwd=DIR (requires .beads in that repo)
  plus scripts/ralph/ralph.py args: max_iterations, --cursor-timeout, --model, --debug
"""

import os
import re
import sys
import shutil
import json
import subprocess
from pathlib import Path

# Get script directory and package root
# Resolve symlinks to get the actual script location
script_path = Path(__file__).resolve()
SCRIPT_DIR = script_path.parent
PACKAGE_ROOT = SCRIPT_DIR.parent
# Try templates directory first, fall back to source directory
TEMPLATES_DIR = PACKAGE_ROOT / 'templates'
if not TEMPLATES_DIR.exists():
    TEMPLATES_DIR = PACKAGE_ROOT

GITIGNORE_MARKER_START = '# >>> ralph-cursor'
GITIGNORE_MARKER_END = '# <<< ralph-cursor'

GITIGNORE_RALPH_LINES = [
    '.beads/',
    'tasks/prd-*.md',
    'scripts/ralph/.last-branch',
    'scripts/ralph/logs/',
    'scripts/ralph/archive/',
]


def _git_path_tracked(repo_root: Path, rel_path: str) -> bool:
    """True if rel_path is in the git index (staged or committed)."""
    if not (repo_root / '.git').exists():
        return False
    try:
        r = subprocess.run(
            ['git', '-C', str(repo_root), 'ls-files', '--error-unmatch', '--', rel_path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _beads_init_optional_gitignore_lines(repo_root: Path):
    """
    `bd init` often creates AGENTS.md and CLAUDE.md at repo root. If they exist but
    are not yet tracked by git, add them to the Ralph ignore block so they are not
    committed by mistake. Skip when already tracked (user had them before Beads).
    """
    repo_root = repo_root.resolve()
    extra = []
    for name in ('AGENTS.md', 'CLAUDE.md'):
        if not (repo_root / name).is_file():
            continue
        if _git_path_tracked(repo_root, name):
            continue
        extra.append(name)
    return extra


def _ralph_gitignore_inner_lines(repo_root: Path):
    lines = list(GITIGNORE_RALPH_LINES)
    for line in _beads_init_optional_gitignore_lines(repo_root):
        if line not in lines:
            lines.append(line)
    return lines


def _ralph_gitignore_block(repo_root: Path):
    inner = '\n'.join(_ralph_gitignore_inner_lines(repo_root))
    return f'{GITIGNORE_MARKER_START}\n{inner}\n{GITIGNORE_MARKER_END}\n'


def apply_ralph_gitignore_block(repo_root: Path):
    """Insert or replace the marker-wrapped Ralph block in repo_root/.gitignore."""
    repo_root = repo_root.resolve()
    path = repo_root / '.gitignore'
    block = _ralph_gitignore_block(repo_root)
    existing = path.read_text(encoding='utf-8') if path.exists() else ''

    pattern = re.compile(
        re.escape(GITIGNORE_MARKER_START) + r'\n.*?\n' + re.escape(GITIGNORE_MARKER_END) + r'\n?',
        re.DOTALL,
    )
    if pattern.search(existing):
        new_content = pattern.sub(block, existing)
    else:
        if existing and not existing.endswith('\n'):
            existing += '\n'
        sep = '\n' if existing.strip() else ''
        new_content = existing + sep + block

    path.write_text(new_content, encoding='utf-8')


def parse_flags(args):
    """Parse command line flags into a dictionary."""
    flags = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('--'):
            if i + 1 < len(args) and not args[i + 1].startswith('--'):
                flags[arg] = args[i + 1]
                i += 1
            else:
                flags[arg] = True
        i += 1
    return flags


def handle_init(args):
    """Handle the 'init' command."""
    flags = parse_flags(args)
    force = flags.get('--force', False)
    cursor_cli = flags.get('--cursor-cli', False)
    copy_project_commands = flags.get('--copy-project-commands', False)
    no_cursorignore = flags.get('--no-cursorignore', False)

    repo_root = Path.cwd()
    target_dir = repo_root / 'scripts' / 'ralph'

    # Create scripts/ralph directory
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f'Created: {target_dir}')

    # Check for Beads CLI
    if not shutil.which('bd'):
        print('Warning: Beads CLI (bd) not found in PATH', file=sys.stderr)
        print('  Ralph requires Beads for task tracking.', file=sys.stderr)
        print('  Please install Beads: https://github.com/steveyegge/beads', file=sys.stderr)
        print('', file=sys.stderr)
        response = input('Continue anyway? (y/N): ').strip().lower()
        if response != 'y':
            print('Aborted.', file=sys.stderr)
            sys.exit(1)
    
    # Check if Beads is initialized
    beads_dir = repo_root / '.beads'
    if not beads_dir.exists():
        print('Beads not initialized in repository.', file=sys.stdout)
        print('  Initializing Beads...', file=sys.stdout)
        try:
            result = subprocess.run(
                ['bd', 'init'],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print('  ✓ Beads initialized', file=sys.stdout)
            else:
                print(f'  Warning: Beads init failed: {result.stderr}', file=sys.stderr)
                print('  You may need to run: bd init', file=sys.stderr)
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f'  Warning: Could not initialize Beads: {e}', file=sys.stderr)
            print('  You may need to run: bd init', file=sys.stderr)
    
    # Required files
    required_files = [
        {'src': 'scripts/ralph/ralph.py', 'dest': 'scripts/ralph/ralph.py', 'executable': True},
        {'src': 'scripts/ralph/cursor/prompt.cursor.md', 'dest': 'scripts/ralph/cursor/prompt.cursor.md', 'executable': False},
    ]
    if not no_cursorignore:
        required_files.append(
            {'src': '.cursorignore', 'dest': '.cursorignore', 'executable': False},
        )

    created = []
    skipped = []

    for file_info in required_files:
        src_path = TEMPLATES_DIR / file_info['src']
        dest_path = repo_root / file_info['dest']
        dest_dir = dest_path.parent

        # Verify source file exists
        if not src_path.exists():
            print(f'Warning: Source template file not found: {src_path}', file=sys.stderr)
            print(f'  Expected location: {TEMPLATES_DIR}', file=sys.stderr)
            print(f'  Package root: {PACKAGE_ROOT}', file=sys.stderr)
            print(f'  This may indicate a corrupted or incomplete installation.', file=sys.stderr)
            print(f'  The file {file_info["dest"]} will be skipped.', file=sys.stderr)
            skipped.append(file_info['dest'])
            continue

        # Create subdirectory if needed
        if not dest_dir.exists():
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                print(f'Error: Failed to create directory {dest_dir}: {e}', file=sys.stderr)
                print(f'  Skipping file: {file_info["dest"]}', file=sys.stderr)
                skipped.append(file_info['dest'])
                continue

        if dest_path.exists() and not force:
            skipped.append(file_info['dest'])
            continue

        try:
            shutil.copy2(src_path, dest_path)
            if file_info['executable']:
                dest_path.chmod(0o755)
            created.append(file_info['dest'])
        except (PermissionError, OSError) as e:
            print(f'Error: Failed to copy file {file_info["dest"]}: {e}', file=sys.stderr)
            print(f'  Source: {src_path}', file=sys.stderr)
            skipped.append(file_info['dest'])

    # Optionally copy commands into project (legacy; default is global ~/.cursor/commands)
    if copy_project_commands:
        commands_src_dir = PACKAGE_ROOT / '.cursor' / 'commands'
        if commands_src_dir.exists():
            cursor_commands_dir = repo_root / '.cursor' / 'commands'
            for command_file in commands_src_dir.iterdir():
                if command_file.is_file() and command_file.suffix == '.md':
                    dest_command_file = cursor_commands_dir / command_file.name

                    if not cursor_commands_dir.exists():
                        try:
                            cursor_commands_dir.mkdir(parents=True, exist_ok=True)
                        except (PermissionError, OSError) as e:
                            print(f'Warning: Failed to create directory {cursor_commands_dir}: {e}', file=sys.stderr)
                            skipped.append(f'.cursor/commands/{command_file.name}')
                            continue

                    if dest_command_file.exists() and not force:
                        skipped.append(f'.cursor/commands/{command_file.name}')
                    else:
                        try:
                            shutil.copy2(command_file, dest_command_file)
                            created.append(f'.cursor/commands/{command_file.name}')
                        except (PermissionError, OSError) as e:
                            print(f'Warning: Failed to copy command file {command_file.name}: {e}', file=sys.stderr)
                            skipped.append(f'.cursor/commands/{command_file.name}')

    # Optional: .cursor/cli.json
    if cursor_cli:
        cursor_cli_file = repo_root / '.cursor' / 'cli.json'
        cursor_dir = cursor_cli_file.parent
        if not cursor_dir.exists():
            try:
                cursor_dir.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                print(f'Warning: Failed to create directory {cursor_dir}: {e}', file=sys.stderr)
                skipped.append('.cursor/cli.json')
            else:
                if cursor_cli_file.exists() and not force:
                    skipped.append('.cursor/cli.json')
                else:
                    # Create a basic template
                    cli_template = {
                        "mcpServers": {
                            "cursor-ide-browser": {
                                "command": "node",
                                "args": []
                            }
                        }
                    }
                    try:
                        with open(cursor_cli_file, 'w', encoding='utf-8') as f:
                            json.dump(cli_template, f, indent=2)
                            f.write('\n')
                        created.append('.cursor/cli.json')
                    except (PermissionError, OSError) as e:
                        print(f'Warning: Failed to create .cursor/cli.json: {e}', file=sys.stderr)
                        skipped.append('.cursor/cli.json')

    # Print summary
    print('\n' + '='*60)
    print('Ralph Initialization Summary')
    print('='*60)
    if created:
        print(f'\n✓ Created {len(created)} file(s):')
        for f in created:
            print(f'  • {f}')
    if skipped:
        print(f'\n⊘ Skipped {len(skipped)} file(s) (already exist):')
        for f in skipped:
            print(f'  • {f}')
        print('\n  Tip: Use --force to overwrite existing files')
    
    if created:
        print('\n' + '='*60)
        print('✓ Ralph initialized successfully!')
        print('='*60)
        print('\nNext steps:')
        print('  1. Bootstrap global Cursor commands (once per machine):')
        print('       python3 <path-to-ralph-cursor>/bin/ralph.py install-cursor')
        print('  2. In this repo: run `ralph setup --project .` or use the /ralph-setup slash command for .gitignore + Beads')
        print('  3. Create a PRD (e.g. tasks/prd-feature-name.md) and Beads issues (see prd-to-beads in ~/.cursor/commands)')
        print('  4. Portable loop: ralph run --project "$(pwd)"')
        print('     Legacy: ralph run (uses ./scripts/ralph/ralph.py in this repo)')
        print('\nFor more information, run: ralph --help')
    else:
        print('\n' + '='*60)
        print('⊘ No files were created (all files already exist)')
        print('='*60)
        print('\nTip: Use --force to overwrite existing files')


def _strip_run_project_flag(args):
    """Extract --project DIR from run argv; return (project_dir_or_none, remaining_args)."""
    project = None
    out = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--project' and i + 1 < len(args):
            project = args[i + 1]
            i += 2
            continue
        if arg.startswith('--project='):
            project = arg.split('=', 1)[1]
            i += 1
            continue
        out.append(arg)
        i += 1
    return project, out


def handle_run(args):
    """
    Handle the 'run' command.

    With --project DIR: runs PACKAGE_ROOT/scripts/ralph/ralph.py with cwd=DIR (portable).
    Otherwise: runs repo-local scripts/ralph/ralph.py (legacy).
    """
    project_raw, forward_args = _strip_run_project_flag(args)

    if project_raw is not None:
        project_dir = Path(project_raw).expanduser().resolve()
        if not project_dir.is_dir():
            print(f'Error: --project is not a directory: {project_raw}', file=sys.stderr)
            sys.exit(1)
        beads_dir = project_dir / '.beads'
        if not beads_dir.exists():
            print('Error: Beads not initialized in --project directory.', file=sys.stderr)
            print(f'  Missing: {beads_dir}', file=sys.stderr)
            print('  Run: bd init', file=sys.stderr)
            print('  (in that repository)', file=sys.stderr)
            sys.exit(1)
        runner_script = PACKAGE_ROOT / 'scripts' / 'ralph' / 'ralph.py'
        if not runner_script.is_file():
            print('Error: Bundled runner not found (incomplete ralph-cursor checkout):', file=sys.stderr)
            print(f'  {runner_script}', file=sys.stderr)
            sys.exit(1)
        cwd = str(project_dir)
    else:
        repo_root = Path.cwd()
        runner_script = repo_root / 'scripts' / 'ralph' / 'ralph.py'
        cwd = str(repo_root)

        if not runner_script.exists():
            print('Error: Ralph is not initialized in this repository.', file=sys.stderr)
            print('', file=sys.stderr)
            print('The required file is missing:', file=sys.stderr)
            print(f'  {runner_script}', file=sys.stderr)
            print('', file=sys.stderr)
            print('To fix this:', file=sys.stderr)
            print('  1. Portable: ralph run --project /path/to/repo (needs .beads there)', file=sys.stderr)
            print('  2. Legacy: ralph init then ralph run', file=sys.stderr)
            sys.exit(1)

    runner_script_resolved = runner_script.resolve()
    if not runner_script_resolved.is_file():
        print('Error: Runner script path is not a file:', file=sys.stderr)
        print(f'  {runner_script}', file=sys.stderr)
        sys.exit(1)

    try:
        if not runner_script_resolved.suffix == '.py':
            print('Error: Runner script does not have .py extension:', file=sys.stderr)
            print(f'  {runner_script}', file=sys.stderr)
            sys.exit(1)
    except Exception:
        pass

    for arg in forward_args:
        if '\x00' in arg:
            print('Error: Invalid argument (contains null byte)', file=sys.stderr)
            sys.exit(1)

    try:
        result = subprocess.run(
            ['python3', str(runner_script_resolved)] + forward_args,
            cwd=cwd,
        )
        sys.exit(result.returncode)
    except FileNotFoundError:
        print('Error: python3 is not available in your PATH.', file=sys.stderr)
        print('', file=sys.stderr)
        print('Please ensure Python 3 is installed and available.', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'Error: Failed to execute runner script: {e}', file=sys.stderr)
        print(f'  Script: {runner_script}', file=sys.stderr)
        sys.exit(1)


def handle_install_cursor(args):
    """Copy package .cursor/commands into ~/.cursor/commands/ and write package_root config."""
    flags = parse_flags(args)
    force = flags.get('--force', False)

    commands_src = PACKAGE_ROOT / '.cursor' / 'commands'
    if not commands_src.is_dir():
        print('Error: Source commands directory not found:', file=sys.stderr)
        print(f'  {commands_src}', file=sys.stderr)
        sys.exit(1)

    home = Path.home()
    dest = home / '.cursor' / 'commands'
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        print(f'Error: Cannot create {dest}: {e}', file=sys.stderr)
        sys.exit(1)

    copied = []
    skipped = []
    for src_file in sorted(commands_src.glob('*.md')):
        if not src_file.is_file():
            continue
        dest_file = dest / src_file.name
        if dest_file.exists() and not force:
            skipped.append(src_file.name)
            continue
        try:
            shutil.copy2(src_file, dest_file)
            copied.append(src_file.name)
        except (OSError, PermissionError) as e:
            print(f'Warning: Could not copy {src_file.name}: {e}', file=sys.stderr)
            skipped.append(src_file.name)

    config_dir = home / '.config' / 'ralph-cursor'
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        root_file = config_dir / 'package_root'
        root_file.write_text(str(PACKAGE_ROOT.resolve()) + '\n', encoding='utf-8')
    except (OSError, PermissionError) as e:
        print(f'Warning: Could not write package_root config: {e}', file=sys.stderr)

    skill_src = PACKAGE_ROOT / 'extras' / 'ralph-portable' / 'SKILL.md'
    if skill_src.is_file():
        skill_dest_dir = home / '.cursor' / 'skills-cursor' / 'ralph-portable'
        try:
            skill_dest_dir.mkdir(parents=True, exist_ok=True)
            skill_dest = skill_dest_dir / 'SKILL.md'
            if not skill_dest.exists() or force:
                shutil.copy2(skill_src, skill_dest)
                print(f'Installed skill: {skill_dest}')
        except (OSError, PermissionError) as e:
            print(f'Warning: Could not install skill: {e}', file=sys.stderr)

    print('Ralph Cursor commands installed to:', dest)
    if copied:
        print('  Copied:', ', '.join(copied))
    if skipped:
        print('  Skipped (exists, use --force):', ', '.join(skipped))
    print('Package root recorded at:', config_dir / 'package_root')
    print('Restart Cursor or reload window if commands do not appear yet.')


def handle_setup(args):
    """Merge Ralph .gitignore block into a project (--project, default cwd)."""
    flags = parse_flags(args)
    if flags.get('--skip-gitignore'):
        print('Skipped .gitignore update (--skip-gitignore).')
        return

    project = flags.get('--project')
    if project:
        repo = Path(project).expanduser().resolve()
    else:
        repo = Path.cwd().resolve()

    if not repo.is_dir():
        print(f'Error: not a directory: {repo}', file=sys.stderr)
        sys.exit(1)

    apply_ralph_gitignore_block(repo)
    print(f'Updated {repo / ".gitignore"} with Ralph ignore block.')


def handle_uninstall(args):
    """
    Handle the 'uninstall' command.
    
    Finds Ralph installation in PATH and removes it.
    """
    # Find ralph in PATH
    ralph_path_str = shutil.which('ralph')
    
    if not ralph_path_str:
        print('Ralph is not installed in your PATH.', file=sys.stdout)
        print('', file=sys.stdout)
        print('If you installed Ralph manually, you may need to remove it yourself.', file=sys.stdout)
        sys.exit(0)
    
    ralph_path = Path(ralph_path_str).resolve()
    
    # Check if it exists
    if not ralph_path.exists():
        print('Ralph installation found but file does not exist:', file=sys.stdout)
        print(f'  {ralph_path_str}', file=sys.stdout)
        print('', file=sys.stdout)
        print('The installation may have already been removed.', file=sys.stdout)
        sys.exit(0)
    
    # Check if it's a directory (shouldn't happen, but handle gracefully)
    if ralph_path.is_dir():
        print('Error: Ralph installation path is a directory, not a file:', file=sys.stderr)
        print(f'  {ralph_path_str}', file=sys.stderr)
        print('', file=sys.stderr)
        print('This is unexpected. Please manually remove the directory if needed.', file=sys.stderr)
        sys.exit(1)
    
    # Security: Verify this is actually a Python script (basic validation)
    # Security: Verify the file is a Python script to prevent removing wrong files
    # This is a basic check - if PATH is compromised, this provides some protection
    try:
        if ralph_path.is_file():
            # Check if it starts with Python shebang (basic verification)
            with open(ralph_path, 'rb') as f:
                first_line = f.read(100)  # Read first 100 bytes
                if not first_line.startswith(b'#!/usr/bin/env python3') and not first_line.startswith(b'#!/usr/bin/python3'):
                    print('Warning: The file found in PATH does not appear to be a Python script.', file=sys.stderr)
                    print(f'  Found: {ralph_path_str}', file=sys.stderr)
                    print('', file=sys.stderr)
                    print('This may not be the Ralph CLI. For safety, uninstall was aborted.', file=sys.stderr)
                    print('', file=sys.stderr)
                    print('If you are sure this is the correct file, remove it manually.', file=sys.stderr)
                    sys.exit(1)
    except (PermissionError, OSError) as e:
        print('Warning: Could not verify file contents:', file=sys.stderr)
        print(f'  {e}', file=sys.stderr)
        print('', file=sys.stderr)
        print('Uninstall was aborted for safety.', file=sys.stderr)
        sys.exit(1)
    
    # Remove the file or symlink
    try:
        ralph_path.unlink()
        print('✓ Removed Ralph installation:', file=sys.stdout)
        print(f'  {ralph_path_str}', file=sys.stdout)
    except PermissionError:
        print('Error: Permission denied when trying to remove:', file=sys.stderr)
        print(f'  {ralph_path_str}', file=sys.stderr)
        print('', file=sys.stderr)
        print('Next steps:', file=sys.stderr)
        print('  1. Try running with sudo: sudo ralph uninstall', file=sys.stderr)
        print('  2. Or manually remove: rm', ralph_path_str, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'Error: Failed to remove installation: {e}', file=sys.stderr)
        print(f'  {ralph_path_str}', file=sys.stderr)
        sys.exit(1)


def handle_version(args):
    """
    Handle the 'version' command.
    
    Displays version information from VERSION file or git tag.
    """
    version = None
    version_file = PACKAGE_ROOT / 'VERSION'
    if version_file.exists():
        try:
            version = version_file.read_text(encoding='utf-8').strip()
            # If file is empty or whitespace-only, treat as missing
            if not version:
                version = None
        except Exception:
            pass
    if not version:
        try:
            result = subprocess.run(['git', 'describe', '--tags', '--always'], cwd=str(PACKAGE_ROOT), capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                version = result.stdout.strip()
        except Exception:
            pass
    if not version:
        version = '1.0.0'
    
    # Security: Sanitize version string to prevent terminal escape sequence injection
    # Remove control characters and limit length
    import re
    version_clean = version.lstrip('v')
    # Remove control characters (0x00-0x1F, 0x7F) except newline/tab
    version_clean = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', version_clean)
    # Limit length to prevent extremely long strings
    if len(version_clean) > 50:
        version_clean = version_clean[:50]
    
    print(f'Ralph CLI v{version_clean}')

def _print_available_commands():
    """Print available commands list."""
    print('Available commands:', file=sys.stderr)
    print('  install-cursor  Install global Cursor slash commands (~/.cursor/commands/)', file=sys.stderr)
    print('  init            Initialize Ralph in the current repository', file=sys.stderr)
    print('  setup           Merge Ralph .gitignore block into a project', file=sys.stderr)
    print('  run             Run Ralph agent loop', file=sys.stderr)
    print('  uninstall       Uninstall Ralph symlink from your PATH', file=sys.stderr)
    print('  version         Display version information', file=sys.stderr)


def _suggest_command(command):
    """Suggest a command based on user input."""
    if 'install' in command.lower() or 'cursor' in command.lower():
        print('  Try: ralph install-cursor', file=sys.stderr)
    elif 'init' in command.lower() or command.lower() == 'i':
        print('  Try: ralph init', file=sys.stderr)
    elif 'setup' in command.lower():
        print('  Try: ralph setup --project .', file=sys.stderr)
    elif 'run' in command.lower() or command.lower() == 'r':
        print('  Try: ralph run', file=sys.stderr)
    elif 'uninstall' in command.lower() or command.lower() == 'u':
        print('  Try: ralph uninstall', file=sys.stderr)
    elif 'version' in command.lower() or command.lower() == 'v':
        print('  Try: ralph version', file=sys.stderr)
    else:
        print('  Try: ralph install-cursor  (bootstrap Cursor commands)', file=sys.stderr)
        print('  Try: ralph init  (legacy in-repo runner)', file=sys.stderr)
        print('  Try: ralph run   (agent loop)', file=sys.stderr)
        print('  Try: ralph uninstall  (remove PATH symlink)', file=sys.stderr)
        print('  Try: ralph version  (check version)', file=sys.stderr)


def print_help():
    """Print help message."""
    help_text = """Ralph CLI - Autonomous AI agent loop installer and runner

Commands:
  install-cursor    Copy Ralph slash commands to ~/.cursor/commands/ (bootstrap)
  init              Initialize Ralph in the current repository (legacy runner)
  setup             Merge Ralph .gitignore block into a project
  run               Run Ralph agent loop
  uninstall         Remove `ralph` from PATH (symlink only)
  version           Display version information

install-cursor:
  ralph install-cursor [--force]
  Copies .md commands from this package to ~/.cursor/ and records package path in
  ~/.config/ralph-cursor/package_root. Optional: installs extras/ralph-portable skill.

Init:
  ralph init [--force] [--cursor-cli] [--copy-project-commands] [--no-cursorignore]

Setup:
  ralph setup [--project DIR] [--skip-gitignore]
  Default DIR is the current working directory.

Run:
  ralph run [--project DIR] [max_iterations] [--cursor-timeout SECONDS] [--model MODEL]

  --project DIR     Portable mode: bundled runner, cwd=DIR (requires .beads there)
  max_iterations    Maximum iterations (default: 10)
  --cursor-timeout  Timeout for cursor worker in seconds (default: 1800)
  --model           Model for cursor worker (default: auto)

Uninstall / Version:
  ralph uninstall
  ralph version
  ralph --version

Examples:
  python3 /path/to/ralph-cursor/bin/ralph.py install-cursor
  ralph setup --project .
  ralph run --project /path/to/repo 10
  ralph run 20
  ralph init --no-cursorignore
"""
    print(help_text)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print('Error: No command provided.', file=sys.stderr)
        print('', file=sys.stderr)
        print('Usage: ralph <command> [options]', file=sys.stderr)
        print('', file=sys.stderr)
        _print_available_commands()
        print('', file=sys.stderr)
        print('Run "ralph --help" for more information.', file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    # Handle help and version flags
    if command in ('-h', '--help'):
        print_help()
        sys.exit(0)
    
    if command in ('-v', '--version'):
        handle_version(args)
        sys.exit(0)

    if command == 'init':
        handle_init(args)
    elif command == 'install-cursor':
        handle_install_cursor(args)
    elif command == 'setup':
        handle_setup(args)
    elif command == 'run':
        handle_run(args)
    elif command == 'uninstall':
        handle_uninstall(args)
    elif command == 'version':
        handle_version(args)
    else:
        print(f'Error: Unknown command "{command}".', file=sys.stderr)
        print('', file=sys.stderr)
        _print_available_commands()
        print('', file=sys.stderr)
        print('Did you mean one of these?', file=sys.stderr)
        _suggest_command(command)
        print('', file=sys.stderr)
        print('Run "ralph --help" for detailed usage information.', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
