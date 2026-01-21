#!/usr/bin/env python3
"""
Ralph CLI - Autonomous AI agent loop installer and runner

Commands:
ralph init [--force] [--cursor-cli]
ralph run [max_iterations] [--cursor-timeout SECONDS] [--model MODEL]

Init options:
--force: Overwrite existing files
--cursor-cli: Also install .cursor/cli.json template

Run options:
max_iterations: Maximum number of iterations (default: 10)
--cursor-timeout: Timeout for cursor worker in seconds (default: 1800, from RALPH_CURSOR_TIMEOUT env)
--model: Model to use for cursor worker (default: 'auto', from RALPH_MODEL env)

The run command executes scripts/ralph/ralph.py which uses Cursor CLI as the worker.
"""

import os
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
        print('  Please install Beads: https://github.com/beads-org/beads', file=sys.stderr)
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
        {'src': 'scripts/ralph/cursor/convert-to-beads.sh', 'dest': 'scripts/ralph/cursor/convert-to-beads.sh', 'executable': True},
        {'src': 'scripts/ralph/migrate-prd-to-beads.py', 'dest': 'scripts/ralph/migrate-prd-to-beads.py', 'executable': True},
    ]

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

    # Copy commands from .cursor/commands/ to .cursor/commands/
    commands_src_dir = PACKAGE_ROOT / '.cursor' / 'commands'
    if commands_src_dir.exists():
        cursor_commands_dir = repo_root / '.cursor' / 'commands'
        for command_file in commands_src_dir.iterdir():
            if command_file.is_file() and command_file.suffix == '.md':
                dest_command_file = cursor_commands_dir / command_file.name
                
                # Create destination directory
                if not cursor_commands_dir.exists():
                    try:
                        cursor_commands_dir.mkdir(parents=True, exist_ok=True)
                    except (PermissionError, OSError) as e:
                        print(f'Warning: Failed to create directory {cursor_commands_dir}: {e}', file=sys.stderr)
                        skipped.append(f'.cursor/commands/{command_file.name}')
                        continue
                
                # Check if file exists and handle force flag
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
        print('  1. Create a PRD markdown file (e.g., tasks/prd-feature-name.md)')
        print('  2. Convert PRD to Beads issues:')
        print('     ./scripts/ralph/cursor/convert-to-beads.sh tasks/prd-feature-name.md')
        print('  3. Or migrate existing prd.yml:')
        print('     python3 scripts/ralph/migrate-prd-to-beads.py scripts/ralph/prd.yml')
        print('  4. Run: ralph run')
        print('\nFor more information, run: ralph --help')
    else:
        print('\n' + '='*60)
        print('⊘ No files were created (all files already exist)')
        print('='*60)
        print('\nTip: Use --force to overwrite existing files')


def handle_run(args):
    """
    Handle the 'run' command.
    
    Passes arguments to scripts/ralph/ralph.py which accepts:
    - max_iterations (positional, default: 10)
    - --cursor-timeout SECONDS (default: 1800, from RALPH_CURSOR_TIMEOUT env)
    - --model MODEL (default: 'auto', from RALPH_MODEL env)
    """
    repo_root = Path.cwd()
    runner_script = repo_root / 'scripts' / 'ralph' / 'ralph.py'

    if not runner_script.exists():
        print('Error: Ralph is not initialized in this repository.', file=sys.stderr)
        print('', file=sys.stderr)
        print('The required file is missing:', file=sys.stderr)
        print(f'  {runner_script}', file=sys.stderr)
        print('', file=sys.stderr)
        print('To fix this:', file=sys.stderr)
        print('  1. Run: ralph init', file=sys.stderr)
        print('  2. This will create the necessary files in scripts/ralph/', file=sys.stderr)
        print('  3. Then you can run: ralph run', file=sys.stderr)
        sys.exit(1)

    # Security: Verify the runner script is actually a Python file
    # This prevents executing malicious files if the path is compromised
    runner_script_resolved = runner_script.resolve()
    if not runner_script_resolved.is_file():
        print('Error: Runner script path is not a file:', file=sys.stderr)
        print(f'  {runner_script}', file=sys.stderr)
        sys.exit(1)
    
    # Security: Basic validation - ensure it's a Python script
    try:
        if not runner_script_resolved.suffix == '.py':
            print('Error: Runner script does not have .py extension:', file=sys.stderr)
            print(f'  {runner_script}', file=sys.stderr)
            sys.exit(1)
    except Exception:
        pass  # If we can't check, continue (defensive)

    # Security: Validate args don't contain obviously malicious patterns
    # Since we use list form (not shell=True), subprocess properly escapes args
    # But we add basic validation for defense in depth
    for arg in args:
        # Check for null bytes (would be rejected by subprocess anyway, but explicit is better)
        if '\x00' in arg:
            print('Error: Invalid argument (contains null byte)', file=sys.stderr)
            sys.exit(1)

    # Execute the runner script, passing through all arguments
    # scripts/ralph/ralph.py accepts: [max_iterations] [--cursor-timeout SECONDS] [--model MODEL]
    # Security: Using list form (not shell=True) prevents command injection
    try:
        result = subprocess.run(
            ['python3', str(runner_script_resolved)] + args,
            cwd=str(repo_root)
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
    print('  init       Initialize Ralph in the current repository', file=sys.stderr)
    print('  run        Run Ralph agent loop', file=sys.stderr)
    print('  uninstall   Uninstall Ralph from your system', file=sys.stderr)
    print('  version    Display version information', file=sys.stderr)


def _suggest_command(command):
    """Suggest a command based on user input."""
    if 'init' in command.lower() or 'i' in command.lower():
        print('  Try: ralph init', file=sys.stderr)
    elif 'run' in command.lower() or 'r' in command.lower():
        print('  Try: ralph run', file=sys.stderr)
    elif 'uninstall' in command.lower() or 'u' in command.lower():
        print('  Try: ralph uninstall', file=sys.stderr)
    elif 'version' in command.lower() or 'v' in command.lower():
        print('  Try: ralph version', file=sys.stderr)
    else:
        print('  Try: ralph init  (to set up Ralph)', file=sys.stderr)
        print('  Try: ralph run   (to run the agent loop)', file=sys.stderr)
        print('  Try: ralph uninstall  (to remove Ralph)', file=sys.stderr)
        print('  Try: ralph version  (to check version)', file=sys.stderr)


def print_help():
    """Print help message."""
    help_text = """Ralph CLI - Autonomous AI agent loop installer and runner

Commands:
  init              Initialize Ralph in the current repository
  run               Run Ralph agent loop
  uninstall         Uninstall Ralph from your system
  version           Display version information

Init:
  ralph init [--force] [--cursor-cli]
  
  Options:
    --force         Overwrite existing files
    --cursor-cli    Also install .cursor/cli.json template

Run:
  ralph run [max_iterations] [--cursor-timeout SECONDS] [--model MODEL]
  
  Arguments:
    max_iterations  Maximum number of iterations (default: 10)
  
  Options:
    --cursor-timeout SECONDS  Timeout for cursor worker in seconds 
                              (default: 1800, from RALPH_CURSOR_TIMEOUT env)
    --model MODEL            Model to use for cursor worker 
                              (default: 'auto', from RALPH_MODEL env)

Uninstall:
  ralph uninstall
  
  Removes Ralph installation from your PATH.

Version:
  ralph version
  ralph --version
  
  Displays the installed version of Ralph CLI.

The run command executes scripts/ralph/ralph.py which uses Cursor CLI as the worker.

Examples:
  ralph init
  ralph init --force --cursor-cli
  ralph run
  ralph run 20
  ralph run 10 --cursor-timeout 3600 --model claude-3.5-sonnet
  ralph uninstall
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
