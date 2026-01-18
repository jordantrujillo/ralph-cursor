#!/usr/bin/env python3
"""
Ralph CLI - Autonomous AI agent loop installer and runner

Commands:
ralph init [--force] [--cursor-rules] [--cursor-cli]
ralph run [max_iterations] [--cursor-timeout SECONDS] [--model MODEL]

Init options:
--force: Overwrite existing files
--cursor-rules: Also install .cursor/rules/ralph-prd.mdc
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
    cursor_rules = flags.get('--cursor-rules', False)
    cursor_cli = flags.get('--cursor-cli', False)

    repo_root = Path.cwd()
    target_dir = repo_root / 'scripts' / 'ralph'

    # Create scripts/ralph directory
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f'Created: {target_dir}')

    # Required files
    required_files = [
        {'src': 'scripts/ralph/ralph.py', 'dest': 'scripts/ralph/ralph.py', 'executable': True},
        {'src': 'scripts/ralph/prd.yml.example', 'dest': 'scripts/ralph/prd.yml.example', 'executable': False},
        {'src': 'scripts/ralph/cursor/prompt.cursor.md', 'dest': 'scripts/ralph/cursor/prompt.cursor.md', 'executable': False},
        {'src': 'scripts/ralph/cursor/prompt.convert-to-prd-yml.md', 'dest': 'scripts/ralph/cursor/prompt.convert-to-prd-yml.md', 'executable': False},
        {'src': 'scripts/ralph/cursor/convert-to-prd-yml.sh', 'dest': 'scripts/ralph/cursor/convert-to-prd-yml.sh', 'executable': True},
    ]

    created = []
    skipped = []

    for file_info in required_files:
        src_path = TEMPLATES_DIR / file_info['src']
        dest_path = repo_root / file_info['dest']
        dest_dir = dest_path.parent

        # Verify source file exists
        if not src_path.exists():
            print(f'Warning: Source file not found: {src_path}', file=sys.stderr)
            print(f'  Looking in: {TEMPLATES_DIR}', file=sys.stderr)
            print(f'  Package root: {PACKAGE_ROOT}', file=sys.stderr)
            skipped.append(file_info['dest'])
            continue

        # Create subdirectory if needed
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)

        if dest_path.exists() and not force:
            skipped.append(file_info['dest'])
            continue

        shutil.copy2(src_path, dest_path)
        if file_info['executable']:
            dest_path.chmod(0o755)
        created.append(file_info['dest'])

    # Copy skills from skills/ to .cursor/skills/
    skills_src_dir = PACKAGE_ROOT / 'skills'
    if skills_src_dir.exists():
        cursor_skills_dir = repo_root / '.cursor' / 'skills'
        for skill_dir in skills_src_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / 'SKILL.md'
                if skill_file.exists():
                    dest_skill_dir = cursor_skills_dir / skill_dir.name
                    dest_skill_file = dest_skill_dir / 'SKILL.md'
                    
                    # Create destination directory
                    if not dest_skill_dir.exists():
                        dest_skill_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Check if file exists and handle force flag
                    if dest_skill_file.exists() and not force:
                        skipped.append(f'.cursor/skills/{skill_dir.name}/SKILL.md')
                    else:
                        shutil.copy2(skill_file, dest_skill_file)
                        created.append(f'.cursor/skills/{skill_dir.name}/SKILL.md')

    # Optional: .cursor/rules/ralph-prd.mdc
    if cursor_rules:
        cursor_rules_dir = repo_root / '.cursor' / 'rules'
        cursor_rules_file = cursor_rules_dir / 'ralph-prd.mdc'
        if not cursor_rules_dir.exists():
            cursor_rules_dir.mkdir(parents=True, exist_ok=True)
        if cursor_rules_file.exists() and not force:
            skipped.append('.cursor/rules/ralph-prd.mdc')
        else:
            src_rules = PACKAGE_ROOT / '.cursor' / 'rules' / 'ralph-prd.mdc'
            if src_rules.exists():
                shutil.copy2(src_rules, cursor_rules_file)
                created.append('.cursor/rules/ralph-prd.mdc')

    # Optional: .cursor/cli.json
    if cursor_cli:
        cursor_cli_file = repo_root / '.cursor' / 'cli.json'
        cursor_dir = cursor_cli_file.parent
        if not cursor_dir.exists():
            cursor_dir.mkdir(parents=True, exist_ok=True)
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
            with open(cursor_cli_file, 'w') as f:
                json.dump(cli_template, f, indent=2)
                f.write('\n')
            created.append('.cursor/cli.json')

    # Print summary
    print('\nSummary:')
    if created:
        print(f'\nCreated {len(created)} file(s):')
        for f in created:
            print(f' - {f}')
    if skipped:
        print(f'\nSkipped {len(skipped)} file(s) (already exist, use --force to overwrite):')
        for f in skipped:
            print(f' - {f}')
    print('\nRalph initialized! Run `ralph run` to start.')


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
        print('Error: Ralph not initialized in this repository.', file=sys.stderr)
        print('Run `ralph init` first to set up Ralph.', file=sys.stderr)
        sys.exit(1)

    # Execute the runner script, passing through all arguments
    # scripts/ralph/ralph.py accepts: [max_iterations] [--cursor-timeout SECONDS] [--model MODEL]
    result = subprocess.run(
        ['python3', str(runner_script)] + args,
        cwd=str(repo_root)
    )
    sys.exit(result.returncode)


def print_help():
    """Print help message."""
    help_text = """Ralph CLI - Autonomous AI agent loop installer and runner

Commands:
  init              Initialize Ralph in the current repository
  run               Run Ralph agent loop

Init:
  ralph init [--force] [--cursor-rules] [--cursor-cli]
  
  Options:
    --force         Overwrite existing files
    --cursor-rules  Also install .cursor/rules/ralph-prd.mdc
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

The run command executes scripts/ralph/ralph.py which uses Cursor CLI as the worker.

Examples:
  ralph init
  ralph init --force --cursor-rules --cursor-cli
  ralph run
  ralph run 20
  ralph run 10 --cursor-timeout 3600 --model claude-3.5-sonnet
"""
    print(help_text)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print('Usage: ralph <init|run> [options]', file=sys.stderr)
        print('Run "ralph --help" for more information.', file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    # Handle help flags
    if command in ('-h', '--help'):
        print_help()
        sys.exit(0)

    if command == 'init':
        handle_init(args)
    elif command == 'run':
        handle_run(args)
    else:
        print(f'Unknown command: {command}', file=sys.stderr)
        print('Usage: ralph <init|run> [options]', file=sys.stderr)
        print('Run "ralph --help" for more information.', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
