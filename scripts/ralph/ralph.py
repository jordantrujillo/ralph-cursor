#!/usr/bin/env python3
"""
Ralph Wiggum - Long-running AI agent loop
Usage: ./ralph.py [max_iterations] [--cursor-timeout SECONDS] [--model MODEL]
or set RALPH_MODEL environment variable
Default model is 'auto' if not specified
Uses Cursor CLI as the worker
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


class RalphAgent:
    def __init__(self, max_iterations=10, cursor_timeout=1800, model="auto"):
        self.max_iterations = max_iterations
        self.cursor_timeout = cursor_timeout
        self.model = model
        self.running_processes = []
        self.interrupted = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Get script directory
        self.script_dir = Path(__file__).parent.resolve()
        self.prd_file = self.script_dir / "prd.yml"
        self.progress_file = self.script_dir / "progress.txt"
        self.archive_dir = self.script_dir / "archive"
        self.last_branch_file = self.script_dir / ".last-branch"
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C and other termination signals"""
        print("\n\nReceived interrupt signal. Cleaning up...", file=sys.stderr)
        self.interrupted = True
        # Only kill processes if the list exists (defensive check)
        if hasattr(self, 'running_processes'):
            self._kill_all_processes()
        sys.exit(130)  # Standard exit code for SIGINT
    
    def _kill_all_processes(self):
        """Kill all running subprocesses"""
        for proc in self.running_processes:
            if proc.poll() is None:  # Process is still running
                try:
                    print(f"Killing process {proc.pid}...", file=sys.stderr)
                    proc.terminate()
                    # Wait a bit for graceful shutdown
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # Force kill if it doesn't terminate
                        proc.kill()
                        proc.wait()
                except Exception as e:
                    print(f"Error killing process {proc.pid}: {e}", file=sys.stderr)
        self.running_processes.clear()
    
    def _get_branch_name(self):
        """Get top-level branch name from PRD file using yq or Python fallback.
        
        Note: This returns the feature-level branchName, not phase-specific branches.
        Phase-specific branches are handled by the Cursor prompt.
        """
        if not self.prd_file.exists():
            return None
        
        # Try yq first
        try:
            result = subprocess.run(
                ['yq', '-r', '.branchName // empty', str(self.prd_file)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                return branch if branch else None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Fallback to Python with yaml if yq not available
        try:
            import yaml
            with open(self.prd_file, 'r', encoding='utf-8') as f:
                prd_data = yaml.safe_load(f)
                return prd_data.get('branchName') if prd_data else None
        except (ImportError, FileNotFoundError, PermissionError, yaml.YAMLError):
            return None
        except Exception:
            # Log unexpected errors but don't crash
            return None
    
    def _archive_previous_run(self):
        """Archive previous run if branch changed"""
        if not self.prd_file.exists() or not self.last_branch_file.exists():
            return
        
        current_branch = self._get_branch_name()
        if not current_branch:
            return
        
        try:
            last_branch = self.last_branch_file.read_text(encoding='utf-8').strip()
        except FileNotFoundError:
            last_branch = ""
        except (OSError, PermissionError) as e:
            print(f"Warning: Failed to read last branch file: {e}", file=sys.stderr)
            last_branch = ""
        
        if current_branch and last_branch and current_branch != last_branch:
            # Archive the previous run
            date = datetime.now().strftime("%Y-%m-%d")
            # Strip "ralph/" prefix from branch name for folder
            folder_name = last_branch.replace("ralph/", "")
            archive_folder = self.archive_dir / f"{date}-{folder_name}"
            
            print(f"Archiving previous run: {last_branch}")
            try:
                archive_folder.mkdir(parents=True, exist_ok=True)
                
                if self.prd_file.exists():
                    result = subprocess.run(["cp", str(self.prd_file), str(archive_folder)], check=False, capture_output=True)
                    if result.returncode != 0:
                        print(f"Warning: Failed to archive PRD file: {result.stderr.decode('utf-8', errors='ignore')}", file=sys.stderr)
                if self.progress_file.exists():
                    result = subprocess.run(["cp", str(self.progress_file), str(archive_folder)], check=False, capture_output=True)
                    if result.returncode != 0:
                        print(f"Warning: Failed to archive progress file: {result.stderr.decode('utf-8', errors='ignore')}", file=sys.stderr)
            except (OSError, PermissionError) as e:
                print(f"Warning: Failed to create archive directory: {e}", file=sys.stderr)
            
            print(f"   Archived to: {archive_folder}")
            
            # Reset progress file for new run
            try:
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    f.write("# Ralph Progress Log\n")
                    f.write(f"Started: {datetime.now()}\n")
                    f.write("---\n")
            except (OSError, PermissionError) as e:
                print(f"Warning: Failed to reset progress file: {e}", file=sys.stderr)
    
    def _track_current_branch(self):
        """Track current branch"""
        current_branch = self._get_branch_name()
        if current_branch:
            try:
                self.last_branch_file.write_text(current_branch, encoding='utf-8')
            except (OSError, PermissionError) as e:
                print(f"Warning: Failed to track current branch: {e}", file=sys.stderr)
    
    def _initialize_progress_file(self):
        """Initialize progress file if it doesn't exist"""
        if not self.progress_file.exists():
            try:
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    f.write("# Ralph Progress Log\n")
                    f.write(f"Started: {datetime.now()}\n")
                    f.write("---\n")
            except (OSError, PermissionError) as e:
                print(f"Warning: Failed to initialize progress file: {e}", file=sys.stderr)
    
    def _find_cursor_binary(self):
        """Find the cursor binary, checking cursor-agent, then agent"""
        for binary in ["cursor-agent", "agent"]:
            if self._command_exists(binary):
                return binary
        # Raise error if neither binary is found
        raise FileNotFoundError("Neither 'cursor-agent' nor 'agent' binary found in PATH")
    
    def _run_cursor_iteration(self, prompt_file):
        """Run a single Cursor iteration"""
        proc = None
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_text = f.read()
            
            # Build cursor command (prompt text will be passed as argument, matching bash behavior)
            cursor_binary = self._find_cursor_binary()
            cmd = [
                cursor_binary,
                "--model", self.model,
                "--print",
                "--force",
                "--approve-mcps",
                prompt_text
            ]
            
            # Check if timeout command is available
            use_timeout_cmd = self._command_exists("timeout")
            
            if use_timeout_cmd:
                # Use timeout command (matches bash script behavior)
                cmd = ["timeout", str(self.cursor_timeout)] + cmd
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,  # Close stdin (non-interactive)
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            else:
                # Fallback: use Python timeout
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,  # Close stdin (non-interactive)
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            
            self.running_processes.append(proc)
            
            # Get output with timeout handling
            try:
                if use_timeout_cmd:
                    stdout, _ = proc.communicate()
                    exit_code = proc.returncode
                    # Check for timeout exit code (124 is timeout command's exit code)
                    if exit_code == 124:
                        print(f"Warning: Cursor iteration timed out after {self.cursor_timeout} seconds", file=sys.stderr)
                else:
                    stdout, _ = proc.communicate(timeout=self.cursor_timeout)
                    exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                print(f"Warning: Cursor iteration timed out after {self.cursor_timeout} seconds", file=sys.stderr)
                if proc is not None:
                    proc.kill()
                    stdout, _ = proc.communicate()
                else:
                    stdout = ""
                exit_code = 124
            
            # Also print to stderr for real-time viewing
            print(stdout, file=sys.stderr, end='')
            
            return stdout
        except Exception as e:
            print(f"Error running cursor: {e}", file=sys.stderr)
            if proc is not None and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=1)
                except (subprocess.TimeoutExpired, Exception):
                    try:
                        proc.kill()
                    except Exception:
                        pass
            return ""
    
    def _command_exists(self, command):
        """Check if a command exists in PATH"""
        try:
            subprocess.run(
                ["which", command],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_completion(self, output):
        """Check if output contains completion signal"""
        return "<promise>COMPLETE</promise>" in output
    
    def run(self):
        """Main run loop"""
        # Setup
        self._archive_previous_run()
        self._track_current_branch()
        self._initialize_progress_file()
        
        print(f"Starting Ralph - Max iterations: {self.max_iterations}")
        print(f"Worker: Cursor")
        print(f"Model: {self.model}")
        
        # Use Cursor prompt file (test mode if RALPH_TEST_MODE is set)
        if os.environ.get("RALPH_TEST_MODE") == "1":
            prompt_file = self.script_dir / "cursor" / "prompt.cursor.test.md"
        else:
            prompt_file = self.script_dir / "cursor" / "prompt.cursor.md"
        
        if not prompt_file.exists():
            print(f"Error: Prompt file not found: {prompt_file}", file=sys.stderr)
            sys.exit(1)
        
        # Main loop
        for i in range(1, self.max_iterations + 1):
            if self.interrupted:
                break
            
            print("")
            print("═══════════════════════════════════════════════════════")
            print(f"  Ralph Iteration {i} of {self.max_iterations} (Worker: Cursor)")
            print("═══════════════════════════════════════════════════════")
            
            # Run iteration
            output = self._run_cursor_iteration(prompt_file)
            
            # Remove completed process from tracking
            self.running_processes = [p for p in self.running_processes if p.poll() is None]
            
            # Check for completion signal
            if self._check_completion(output):
                print("")
                print("Ralph completed all tasks!")
                print(f"Completed at iteration {i} of {self.max_iterations}")
                return 0
            
            if self.interrupted:
                break
            
            print(f"Iteration {i} complete. Continuing...")
            time.sleep(2)
        
        if self.interrupted:
            print("\nRalph interrupted by user.", file=sys.stderr)
            return 130
        else:
            print("")
            print(f"Ralph reached max iterations ({self.max_iterations}) without completing all tasks.")
            print(f"Check {self.progress_file} for status.")
            return 1


def main():
    """Main entry point"""
    # Parse environment variables
    # Parse cursor_timeout with error handling
    try:
        cursor_timeout = int(os.environ.get("RALPH_CURSOR_TIMEOUT", "1800"))
        if cursor_timeout <= 0:
            print("Warning: RALPH_CURSOR_TIMEOUT must be positive, using default 1800", file=sys.stderr)
            cursor_timeout = 1800
    except (ValueError, TypeError):
        print("Warning: Invalid RALPH_CURSOR_TIMEOUT value, using default 1800", file=sys.stderr)
        cursor_timeout = 1800
    
    model = os.environ.get("RALPH_MODEL", "auto")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Ralph Wiggum - Long-running AI agent loop (uses Cursor CLI)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "max_iterations",
        type=int,
        nargs="?",
        default=10,
        help="Maximum number of iterations (default: 10)"
    )
    parser.add_argument(
        "--cursor-timeout",
        type=int,
        default=cursor_timeout,
        help="Timeout for cursor worker in seconds (default: 1800, from RALPH_CURSOR_TIMEOUT env)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=model,
        help="Model to use for cursor worker (default: 'auto', from RALPH_MODEL env)"
    )
    
    args = parser.parse_args()
    
    # Create and run agent
    agent = RalphAgent(
        max_iterations=args.max_iterations,
        cursor_timeout=args.cursor_timeout,
        model=args.model
    )
    
    sys.exit(agent.run())


if __name__ == "__main__":
    main()
