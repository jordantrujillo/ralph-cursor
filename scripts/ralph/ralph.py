#!/usr/bin/env python3
"""
Ralph Wiggum - Long-running AI agent loop
Usage: ./ralph.py [max_iterations] [--cursor-timeout SECONDS] [--model MODEL] [--debug]
or set RALPH_MODEL environment variable
Default model is 'auto' if not specified
Uses Cursor CLI as the worker
--debug enables real-time output streaming for debugging
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
    def __init__(self, max_iterations=10, cursor_timeout=1800, model="auto", debug=False):
        self.max_iterations = max_iterations
        self.cursor_timeout = cursor_timeout
        self.model = model
        self.debug = debug
        self.running_processes = []
        self.interrupted = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Get script directory
        self.script_dir = Path(__file__).parent.resolve()
        self.archive_dir = self.script_dir / "archive"
        self.last_branch_file = self.script_dir / ".last-branch"
        self.log_dir = self.script_dir / "logs"
        
        # Get project root (repository root)
        repo_root = Path.cwd()
        self.signal_file = repo_root / ".ralph-compact-signal"
        self.task_file = repo_root / ".ralph-current-task"
        
        # Check for Beads CLI availability
        if not self._command_exists("bd"):
            raise FileNotFoundError(
                "Beads CLI (bd) not found in PATH. "
                "Please install Beads: https://github.com/steveyegge/beads"
            )
        
        # Check if Beads is initialized in the repository
        repo_root = Path.cwd()
        beads_dir = repo_root / ".beads"
        if not beads_dir.exists():
            raise FileNotFoundError(
                "Beads not initialized in repository. "
                "Please run: bd init"
            )
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C and other termination signals"""
        print("\n\nReceived interrupt signal. Cleaning up...", file=sys.stderr)
        self.interrupted = True
        # Only kill processes if the list exists (defensive check)
        if hasattr(self, 'running_processes'):
            self._kill_all_processes()
        # Don't call sys.exit here - let the main loop handle cleanup and exit
    
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
        """Get top-level branch name from Beads project epic metadata.
        
        Note: This returns the feature-level branchName, not phase-specific branches.
        Phase-specific branches are handled by the Cursor prompt.
        """
        repo_root = Path.cwd()
        
        # Find the project epic (top-level epic without a parent)
        try:
            result = subprocess.run(
                ['bd', 'list', '--type', 'epic', '--status', 'open'],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(repo_root)
            )
            if result.returncode != 0:
                return None
            
            # Parse output to find top-level epic (no parent)
            # bd list outputs issue IDs, we need to check each one
            epic_ids = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            
            # First pass: find the project epic (epic without a parent)
            project_epic_id = None
            for epic_id in epic_ids:
                show_result = subprocess.run(
                    ['bd', 'show', epic_id],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    cwd=str(repo_root)
                )
                if show_result.returncode == 0:
                    output = show_result.stdout
                    # Check if this epic has a parent (look for "Parent:" line)
                    has_parent = any(line.strip().lower().startswith('parent:') for line in output.split('\n'))
                    if not has_parent:
                        # This is a top-level epic (project epic)
                        project_epic_id = epic_id
                        break
            
            # If no project epic found, return None
            if not project_epic_id:
                return None
            
            # Second pass: get branch metadata from project epic
            show_result = subprocess.run(
                ['bd', 'show', project_epic_id],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(repo_root)
            )
            if show_result.returncode == 0:
                output = show_result.stdout
                for line in output.split('\n'):
                    if line.strip().startswith('branch:'):
                        branch = line.split(':', 1)[1].strip()
                        return branch if branch else None
            
            return None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        except Exception:
            # Log unexpected errors but don't crash
            return None
    
    def _archive_previous_run(self):
        """Archive previous run if branch changed
        
        Note: With Beads, archiving is handled by Beads itself (closed issues are archived).
        This method only archives branch tracking information if the branch changed.
        """
        if not self.last_branch_file.exists():
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
            # Archive the previous run's branch tracking
            date = datetime.now().strftime("%Y-%m-%d")
            # Strip "ralph/" prefix from branch name for folder
            folder_name = last_branch.replace("ralph/", "")
            
            # Security: Sanitize folder_name to prevent path traversal attacks
            # Only allow alphanumeric, dash, and underscore characters (no dots to prevent ..)
            import re
            folder_name = re.sub(r'[^a-zA-Z0-9\-_]', '_', folder_name)
            
            archive_folder = self.archive_dir / f"{date}-{folder_name}"
            
            print(f"Previous run branch: {last_branch}")
            print(f"Current run branch: {current_branch}")
            print(f"Note: With Beads, completed tasks are automatically archived when closed.")
            
            # Beads handles its own archiving, so we don't need to archive Beads files
            # The archive folder is kept for reference but won't contain prd.yml or progress.txt
    
    def _track_current_branch(self):
        """Track current branch"""
        current_branch = self._get_branch_name()
        if current_branch:
            try:
                self.last_branch_file.write_text(current_branch, encoding='utf-8')
            except (OSError, PermissionError) as e:
                print(f"Warning: Failed to track current branch: {e}", file=sys.stderr)
    
    
    def _find_cursor_binary(self):
        """Find the cursor binary, checking cursor-agent, then agent"""
        for binary in ["cursor-agent", "agent"]:
            if self._command_exists(binary):
                return binary
        # Raise error if neither binary is found
        raise FileNotFoundError("Neither 'cursor-agent' nor 'agent' binary found in PATH")
    
    def _run_cursor_iteration(self, prompt_file, iteration=None):
        """Run a single Cursor iteration"""
        proc = None
        log_file = None
        signal_monitor_thread = None
        try:
            # Clear any existing compaction signal before starting
            self._clear_compaction_signal()
            
            # Clear task file (agent will write it when it selects a task)
            try:
                if self.task_file.exists():
                    self.task_file.unlink()
            except (OSError, PermissionError):
                pass
            # Security: Validate prompt_file path to prevent path traversal
            prompt_file_path = Path(prompt_file)
            if not prompt_file_path.is_absolute():
                prompt_file_path = self.script_dir / prompt_file_path
            prompt_file_path = prompt_file_path.resolve()
            
            # Ensure the prompt file is within the script directory to prevent path traversal
            try:
                prompt_file_path.relative_to(self.script_dir.resolve())
            except ValueError:
                raise ValueError(f"Prompt file path outside script directory: {prompt_file_path}")
            
            if not prompt_file_path.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_file_path}")
            
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                prompt_text = f.read()
            
            # Security: Validate model parameter to prevent command injection
            # Model should only contain alphanumeric, dash, underscore, and dot
            if not all(c.isalnum() or c in ['-', '_', '.'] for c in self.model):
                raise ValueError(f"Invalid model name: {self.model}")
            
            # Build cursor command (prompt text will be passed as argument, matching bash behavior)
            # Security: Using list form of subprocess.Popen (not shell=True) prevents command injection
            cursor_binary = self._find_cursor_binary()
            cmd = [
                cursor_binary,
                "--model", self.model,
                "--print",
                "--force",
                "--approve-mcps",
            ]
            
            # Add streaming options for debug mode
            if self.debug:
                cmd.extend([
                    "--output-format", "stream-json",
                    "--stream-partial-output"
                ])
            
            cmd.append(prompt_text)
            
            # Check if timeout command is available
            use_timeout_cmd = self._command_exists("timeout")
            
            # Set up environment for unbuffered output in debug mode
            env = os.environ.copy()
            if self.debug:
                env['PYTHONUNBUFFERED'] = '1'
            
            if use_timeout_cmd:
                # Use timeout command (matches bash script behavior)
                cmd = ["timeout", str(self.cursor_timeout)] + cmd
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,  # Close stdin (non-interactive)
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1 if self.debug else -1,  # Line buffered in debug, default otherwise
                    env=env
                )
            else:
                # Fallback: use Python timeout
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,  # Close stdin (non-interactive)
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1 if self.debug else -1,  # Line buffered in debug, default otherwise
                    env=env
                )
            
            self.running_processes.append(proc)
            
            # Set up signal file monitoring thread
            import threading
            compaction_detected = threading.Event()
            
            def monitor_signal():
                """Monitor for compaction signal file"""
                while proc.poll() is None and not self.interrupted and not compaction_detected.is_set():
                    if self._check_compaction_signal():
                        compaction_detected.set()
                        print("\n[RALPH] Context compaction detected - restarting with fresh context...", file=sys.stderr)
                        # Kill the cursor process
                        try:
                            proc.terminate()
                            # Wait briefly for graceful shutdown
                            try:
                                proc.wait(timeout=2)
                            except subprocess.TimeoutExpired:
                                proc.kill()
                                proc.wait()
                        except Exception as e:
                            print(f"Warning: Error killing process: {e}", file=sys.stderr)
                        # Delete signal file immediately after killing
                        try:
                            if self.signal_file.exists():
                                self.signal_file.unlink()
                        except (OSError, PermissionError) as e:
                            print(f"Warning: Failed to delete signal file: {e}", file=sys.stderr)
                        break
                    time.sleep(0.5)  # Check every 500ms
            
            signal_monitor_thread = threading.Thread(target=monitor_signal, daemon=True)
            signal_monitor_thread.start()
            
            # Set up log file for debug mode
            if self.debug and iteration is not None:
                # Create logs directory if it doesn't exist
                self.log_dir.mkdir(parents=True, exist_ok=True)
                # Create log file with timestamp and iteration number
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                log_file_path = self.log_dir / f"iteration-{iteration:03d}-{timestamp}.log"
                log_file = open(log_file_path, 'w', encoding='utf-8')
                print(f"Debug: Logging output to {log_file_path}", file=sys.stderr)
            
            # Get output with timeout handling
            stdout = ""
            try:
                if self.debug:
                    # Real-time streaming mode for debugging using cursor-agent's stream-json
                    import threading
                    import json
                    output_lines = []
                    
                    def read_output():
                        """Read and parse stream-json output and write to log file"""
                        try:
                            for line in proc.stdout:
                                # Check for interrupt flag
                                if self.interrupted:
                                    break
                                if not line.strip():
                                    continue
                                output_lines.append(line)
                                try:
                                    # Parse JSON line and extract text content
                                    data = json.loads(line)
                                    # Extract text from various possible fields
                                    text = ""
                                    if isinstance(data, dict):
                                        # Look for common text fields in stream-json format
                                        text = data.get("text", "") or data.get("content", "") or data.get("delta", "")
                                        if not text and "choices" in data:
                                            # Handle OpenAI-style format
                                            for choice in data.get("choices", []):
                                                delta = choice.get("delta", {})
                                                text = delta.get("content", "")
                                                if text:
                                                    break
                                    elif isinstance(data, str):
                                        text = data
                                    
                                    if text:
                                        # Write text to log file
                                        if log_file:
                                            log_file.write(text)
                                            log_file.flush()
                                    else:
                                        # If no text found, write the raw line
                                        if log_file:
                                            log_file.write(line)
                                            log_file.flush()
                                except json.JSONDecodeError:
                                    # If not JSON, write as-is
                                    output_lines.append(line)
                                    if log_file:
                                        log_file.write(line)
                                        log_file.flush()
                        except Exception:
                            pass
                    
                    # Start reading thread
                    reader_thread = threading.Thread(target=read_output, daemon=True)
                    reader_thread.start()
                    
                    # Wait for process with timeout, checking for interrupts and compaction signal
                    if use_timeout_cmd:
                        # timeout command handles timeout, but we need to poll to check for interrupts
                        while proc.poll() is None and not self.interrupted and not compaction_detected.is_set():
                            time.sleep(0.1)  # Small sleep to avoid busy-waiting
                        # If interrupted, kill the process (signal handler may have already done this)
                        if self.interrupted and proc.poll() is None:
                            proc.kill()
                            proc.wait()
                        # If compaction detected, process was already killed by monitor thread
                        if compaction_detected.is_set():
                            exit_code = 130  # Use 130 to indicate early termination
                        else:
                            exit_code = proc.returncode if proc.returncode is not None else 130
                            # Check for timeout exit code (124 is timeout command's exit code)
                            if exit_code == 124:
                                print(f"Warning: Cursor iteration timed out after {self.cursor_timeout} seconds", file=sys.stderr)
                            elif self.interrupted:
                                exit_code = 130
                    else:
                        # Use Python timeout with interrupt checking
                        try:
                            # Poll with small intervals to check for interrupts and compaction signal
                            start_time = time.time()
                            while proc.poll() is None and not self.interrupted and not compaction_detected.is_set():
                                elapsed = time.time() - start_time
                                if elapsed >= self.cursor_timeout:
                                    raise subprocess.TimeoutExpired(cmd, self.cursor_timeout)
                                time.sleep(0.1)  # Small sleep to avoid busy-waiting
                            # If interrupted, kill the process (signal handler may have already done this)
                            if self.interrupted and proc.poll() is None:
                                proc.kill()
                                proc.wait()
                            # If compaction detected, process was already killed by monitor thread
                            if compaction_detected.is_set():
                                exit_code = 130  # Use 130 to indicate early termination
                            else:
                                exit_code = proc.returncode if proc.returncode is not None else 130
                        except subprocess.TimeoutExpired:
                            print(f"Warning: Cursor iteration timed out after {self.cursor_timeout} seconds", file=sys.stderr)
                            proc.kill()
                            proc.wait()
                            exit_code = 124
                    
                    # Wait for reader thread to finish (with interrupt check)
                    if not self.interrupted:
                        reader_thread.join(timeout=1)
                    else:
                        # If interrupted, don't wait long for thread
                        reader_thread.join(timeout=0.1)
                    stdout = ''.join(output_lines)
                    
                    # Close log file (always close, even on interrupt)
                    if log_file:
                        log_file.close()
                        log_file = None
                else:
                    # Buffered mode (default) - collect all output after completion
                    # Note: communicate() blocks, but signal handler will kill the process
                    # which will cause communicate() to return
                    # We need to poll instead of using communicate() to check for compaction signal
                    if use_timeout_cmd:
                        # Poll with timeout checking
                        start_time = time.time()
                        while proc.poll() is None and not self.interrupted and not compaction_detected.is_set():
                            elapsed = time.time() - start_time
                            if elapsed >= self.cursor_timeout:
                                proc.kill()
                                break
                            time.sleep(0.1)
                        stdout, _ = proc.communicate()
                        if compaction_detected.is_set():
                            exit_code = 130  # Compaction detected
                        else:
                            exit_code = proc.returncode if proc.returncode is not None else 130
                            # Check for timeout exit code (124 is timeout command's exit code)
                            if exit_code == 124:
                                print(f"Warning: Cursor iteration timed out after {self.cursor_timeout} seconds", file=sys.stderr)
                    else:
                        try:
                            # Poll with timeout and compaction checking
                            start_time = time.time()
                            while proc.poll() is None and not self.interrupted and not compaction_detected.is_set():
                                elapsed = time.time() - start_time
                                if elapsed >= self.cursor_timeout:
                                    raise subprocess.TimeoutExpired(cmd, self.cursor_timeout)
                                time.sleep(0.1)
                            stdout, _ = proc.communicate()
                            if compaction_detected.is_set():
                                exit_code = 130  # Compaction detected
                            else:
                                exit_code = proc.returncode
                        except subprocess.TimeoutExpired:
                            print(f"Warning: Cursor iteration timed out after {self.cursor_timeout} seconds", file=sys.stderr)
                            proc.kill()
                            stdout, _ = proc.communicate()
                            exit_code = 124
                    
                    # Check if we were interrupted
                    if self.interrupted:
                        # Process was killed by signal handler, exit_code may not be accurate
                        exit_code = 130
                    
                    # Check if compaction was detected
                    if compaction_detected.is_set():
                        exit_code = 130  # Indicate early termination due to compaction
                    
                    # Print to stderr for viewing
                    print(stdout, file=sys.stderr, end='', flush=True)
            except subprocess.TimeoutExpired:
                print(f"Warning: Cursor iteration timed out after {self.cursor_timeout} seconds", file=sys.stderr)
                if proc is not None:
                    proc.kill()
                    if not self.debug:
                        stdout, _ = proc.communicate()
                    else:
                        stdout = ''.join(output_lines) if 'output_lines' in locals() else ""
                else:
                    stdout = ""
                exit_code = 124
                if log_file:
                    log_file.close()
                    log_file = None
            
            # Clean up signal file if it still exists (defensive cleanup)
            self._clear_compaction_signal()
            
            # If compaction was detected, return empty output to trigger restart
            if 'compaction_detected' in locals() and compaction_detected.is_set():
                return ""
            
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
            if log_file:
                log_file.close()
            # Clean up signal file on error
            self._clear_compaction_signal()
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
    
    def _check_compaction_signal(self):
        """Check if compaction signal file exists"""
        return self.signal_file.exists()
    
    def _clear_compaction_signal(self):
        """Remove compaction signal file if it exists"""
        try:
            if self.signal_file.exists():
                self.signal_file.unlink()
        except (OSError, PermissionError) as e:
            print(f"Warning: Failed to clear compaction signal file: {e}", file=sys.stderr)
    
    def _check_completion(self, output):
        """Check if output contains completion signal"""
        return "<promise>COMPLETE</promise>" in output
    
    def run(self):
        """Main run loop"""
        # Setup
        self._archive_previous_run()
        self._track_current_branch()
        
        print(f"Starting Ralph - Max iterations: {self.max_iterations}")
        print(f"Worker: Cursor")
        print(f"Model: {self.model}")
        print(f"Task tracker: Beads")
        if self.debug:
            print(f"Debug mode: Output will be logged to {self.log_dir}/")
        
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
            output = self._run_cursor_iteration(prompt_file, iteration=i)
            
            # Remove completed process from tracking
            self.running_processes = [p for p in self.running_processes if p.poll() is None]
            
            # Check if compaction signal was detected (empty output indicates restart)
            if output == "" and self._check_compaction_signal():
                print("")
                print(f"Context compaction detected in iteration {i}. Restarting with fresh context...")
                # Signal file should already be deleted by the monitor thread, but ensure it's gone
                self._clear_compaction_signal()
                # Continue to next iteration (fresh context)
                continue
            
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
            print(f"Check Beads for task status: bd list --status open")
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
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with real-time output streaming"
    )
    
    args = parser.parse_args()
    
    # Create and run agent
    agent = RalphAgent(
        max_iterations=args.max_iterations,
        cursor_timeout=args.cursor_timeout,
        model=args.model,
        debug=args.debug
    )
    
    sys.exit(agent.run())


if __name__ == "__main__":
    main()
