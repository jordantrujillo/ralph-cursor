#!/bin/bash
# Install script for Ralph CLI
# Installs bin/ralph.py to a directory in PATH

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RALPH_SCRIPT="$SCRIPT_DIR/bin/ralph.py"
INSTALL_NAME="ralph"

# Validate HOME variable
if [ -z "$HOME" ]; then
    echo -e "${RED}Error: HOME environment variable is not set${NC}" >&2
    echo "" >&2
    echo "Next steps:" >&2
    echo "  1. Set HOME environment variable: export HOME=\$HOME" >&2
    echo "  2. Or specify HOME explicitly: HOME=/path/to/home $0" >&2
    exit 1
fi

# Check if ralph.py exists
if [ ! -f "$RALPH_SCRIPT" ]; then
    echo -e "${RED}Error: $RALPH_SCRIPT not found${NC}" >&2
    echo "" >&2
    echo "Next steps:" >&2
    echo "  1. Ensure you're running this script from the Ralph project root directory" >&2
    echo "  2. Verify that bin/ralph.py exists in the project" >&2
    echo "  3. If the file is missing, check your git repository or re-download the project" >&2
    exit 1
fi

# Determine install location
# Prefer ~/.local/bin for user installs, fall back to /usr/local/bin for system installs
INSTALL_DIR=""
USE_SYMLINK=true

# Try to use ~/.local/bin first
if [ -w "$HOME/.local/bin" ] 2>/dev/null; then
    INSTALL_DIR="$HOME/.local/bin"
elif mkdir -p "$HOME/.local/bin" 2>/dev/null && [ -w "$HOME/.local/bin" ] 2>/dev/null; then
    INSTALL_DIR="$HOME/.local/bin"
elif [ -w "/usr/local/bin" ] 2>/dev/null; then
    INSTALL_DIR="/usr/local/bin"
else
    echo -e "${RED}Error: No writable installation directory found${NC}" >&2
    echo "" >&2
    echo "Tried the following directories:" >&2
    echo "  - $HOME/.local/bin" >&2
    echo "  - /usr/local/bin" >&2
    echo "" >&2
    echo "Next steps:" >&2
    echo "  1. Create ~/.local/bin directory: mkdir -p ~/.local/bin" >&2
    echo "  2. Or run with sudo for system-wide install: sudo $0" >&2
    echo "  3. Or manually set permissions on one of the directories above" >&2
    echo "" >&2
    echo "If you see 'Permission denied', you may need to:" >&2
    echo "  - Check directory permissions: ls -ld ~/.local/bin" >&2
    echo "  - Fix permissions: chmod 755 ~/.local/bin" >&2
    echo "  - Or use sudo for system-wide installation" >&2
    exit 1
fi

INSTALL_PATH="$INSTALL_DIR/$INSTALL_NAME"

# Check if already installed
if [ -f "$INSTALL_PATH" ] || [ -L "$INSTALL_PATH" ]; then
    # Check if symlink is broken
    if [ -L "$INSTALL_PATH" ] && [ ! -e "$INSTALL_PATH" ]; then
        echo -e "${YELLOW}Warning: $INSTALL_PATH exists as a broken symlink${NC}"
    else
        echo -e "${YELLOW}Warning: $INSTALL_PATH already exists${NC}"
    fi
    
    # Only prompt if running in interactive mode
    if [ -t 0 ]; then
        read -p "Overwrite? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Installation cancelled."
            exit 0
        fi
    else
        # Non-interactive mode: automatically overwrite
        echo "Non-interactive mode: overwriting existing installation"
    fi
    rm -f "$INSTALL_PATH"
fi

# Install the script
echo "Installing Ralph CLI..."
if [ "$USE_SYMLINK" = true ]; then
    # Create symlink to preserve updates
    if ! ln -s "$RALPH_SCRIPT" "$INSTALL_PATH" 2>/dev/null; then
        echo -e "${RED}Error: Failed to create symlink${NC}" >&2
        echo "" >&2
        echo "Details:" >&2
        echo "  Source: $RALPH_SCRIPT" >&2
        echo "  Target: $INSTALL_PATH" >&2
        echo "" >&2
        echo "Next steps:" >&2
        echo "  1. Check if target already exists: ls -l $INSTALL_PATH" >&2
        echo "  2. Remove existing file/symlink if needed: rm $INSTALL_PATH" >&2
        echo "  3. Check directory permissions: ls -ld $(dirname "$INSTALL_PATH")" >&2
        echo "  4. Ensure you have write permissions to the install directory" >&2
        exit 1
    fi
    echo -e "${GREEN}✓ Created symlink: $INSTALL_PATH -> $RALPH_SCRIPT${NC}"
else
    # Copy the file
    if ! cp "$RALPH_SCRIPT" "$INSTALL_PATH" 2>/dev/null; then
        echo -e "${RED}Error: Failed to copy file${NC}" >&2
        echo "" >&2
        echo "Details:" >&2
        echo "  Source: $RALPH_SCRIPT" >&2
        echo "  Target: $INSTALL_PATH" >&2
        echo "" >&2
        echo "Next steps:" >&2
        echo "  1. Check if target directory is writable: ls -ld $(dirname "$INSTALL_PATH")" >&2
        echo "  2. Check disk space: df -h $(dirname "$INSTALL_PATH")" >&2
        echo "  3. Try running with sudo: sudo $0" >&2
        exit 1
    fi
    echo -e "${GREEN}✓ Copied to: $INSTALL_PATH${NC}"
fi

# Make executable
if ! chmod +x "$INSTALL_PATH" 2>/dev/null; then
    echo -e "${RED}Error: Failed to make file executable${NC}" >&2
    echo "" >&2
    echo "Details:" >&2
    echo "  File: $INSTALL_PATH" >&2
    echo "" >&2
    echo "Next steps:" >&2
    echo "  1. Check file permissions: ls -l $INSTALL_PATH" >&2
    echo "  2. Try manually: chmod +x $INSTALL_PATH" >&2
    echo "  3. If that fails, you may need sudo: sudo chmod +x $INSTALL_PATH" >&2
    exit 1
fi
echo -e "${GREEN}✓ Made executable${NC}"

# Check and install dependencies
echo ""
echo "Checking dependencies..."

# Detect platform more reliably
DETECTED_PLATFORM=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    DETECTED_PLATFORM="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux"* ]]; then
    DETECTED_PLATFORM="linux"
else
    DETECTED_PLATFORM="unsupported"
fi

# List missing dependencies
MISSING_DEPS=()
DEP_INSTALL_COMMANDS=()
DEP_INSTALL_DESCRIPTIONS=()

# Check for yq
if ! command -v yq >/dev/null 2>&1; then
    MISSING_DEPS+=("yq")
    if [ "$DETECTED_PLATFORM" = "macos" ]; then
        DEP_INSTALL_COMMANDS+=("brew install yq")
        DEP_INSTALL_DESCRIPTIONS+=("Installing yq via Homebrew...")
    elif [ "$DETECTED_PLATFORM" = "linux" ]; then
        # Detect architecture for Linux
        ARCH=$(uname -m)
        if [ "$ARCH" = "x86_64" ]; then
            ARCH="amd64"
        elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
            ARCH="arm64"
        else
            ARCH="amd64"  # Default fallback
        fi
        DEP_INSTALL_COMMANDS+=("sudo wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_${ARCH} && sudo chmod +x /usr/local/bin/yq")
        DEP_INSTALL_DESCRIPTIONS+=("Downloading yq for Linux ($ARCH)...")
    else
        DEP_INSTALL_COMMANDS+=("# Unsupported platform - manual installation required")
        DEP_INSTALL_DESCRIPTIONS+=("Manual installation required for unsupported platform")
    fi
else
    echo -e "${GREEN}✓ yq is installed${NC}"
    # Verify yq works
    if yq --version >/dev/null 2>&1; then
        YQ_VERSION=$(yq --version 2>/dev/null | head -n1 || echo "unknown")
        echo -e "  Version: $YQ_VERSION"
    fi
fi

# Ask to install missing dependencies
if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Missing dependencies:${NC}"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "  - $dep"
    done
    echo ""
    
    # Provide platform-specific guidance for unsupported platforms
    if [ "$DETECTED_PLATFORM" = "unsupported" ]; then
        echo -e "${YELLOW}Platform not automatically supported: $OSTYPE${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Visit https://github.com/mikefarah/yq/releases to download yq for your platform"
        echo "  2. Or install via package manager:"
        echo "     - pip: pip install pyyaml"
        echo "     - npm: npm install -g yq"
        echo "     - Check your system's package manager for yq"
        echo ""
        echo "After installing yq, re-run this install script."
    else
        # Only prompt if running in interactive mode
        if [ -t 0 ]; then
            read -p "Would you like to install these dependencies? [y/N] " -n 1 -r
            echo
            INSTALL_DEPS=false
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                INSTALL_DEPS=true
            fi
        else
            # Non-interactive mode: skip dependency installation
            echo "Non-interactive mode: skipping dependency installation"
            INSTALL_DEPS=false
        fi
        
        if [ "$INSTALL_DEPS" = true ]; then
            echo ""
            echo -e "${YELLOW}Installing dependencies...${NC}"
            INSTALL_FAILED=0
            
            for i in "${!MISSING_DEPS[@]}"; do
                dep="${MISSING_DEPS[$i]}"
                cmd="${DEP_INSTALL_COMMANDS[$i]}"
                desc="${DEP_INSTALL_DESCRIPTIONS[$i]:-Installing $dep...}"
                
                echo ""
                echo -e "${YELLOW}[$((i+1))/${#MISSING_DEPS[@]}] $desc${NC}"
                
                if [[ "$cmd" == "#"* ]]; then
                    echo -e "${YELLOW}  Manual installation required:${NC}"
                    echo "  ${cmd#\# }"
                    INSTALL_FAILED=1
                else
                    # Show progress indicator
                    echo -e "  ${YELLOW}Running:${NC} $cmd"
                    
                    # Execute installation command
                    # Note: eval is used here because commands may contain && operators
                    # Commands are controlled by the script, so this is safe
                    if eval "$cmd" 2>&1; then
                        INSTALL_EXIT_CODE=$?
                    else
                        INSTALL_EXIT_CODE=$?
                    fi
                    
                    # Verify installation succeeded
                    if [ $INSTALL_EXIT_CODE -eq 0 ]; then
                        # Wait a moment for PATH to update
                        sleep 1
                        
                        # Verify the dependency is now available
                        if command -v "$dep" >/dev/null 2>&1; then
                            echo -e "  ${GREEN}✓ $dep installed successfully${NC}"
                            # Show version if available
                            if "$dep" --version >/dev/null 2>&1; then
                                VERSION=$("$dep" --version 2>/dev/null | head -n1 || echo "unknown")
                                echo -e "  ${GREEN}  Version: $VERSION${NC}"
                            fi
                        else
                            echo -e "  ${YELLOW}⚠ Installation command succeeded, but $dep not found in PATH${NC}"
                            echo -e "  ${YELLOW}  You may need to restart your terminal or run: source ~/.bashrc${NC}"
                        fi
                    else
                        echo -e "  ${RED}✗ Failed to install $dep (exit code: $INSTALL_EXIT_CODE)${NC}" >&2
                        echo "" >&2
                        echo "  Next steps:" >&2
                        echo "    1. Check the error message above" >&2
                        echo "    2. Try installing manually: $cmd" >&2
                        if [ "$DETECTED_PLATFORM" = "macos" ]; then
                            echo "    3. Ensure Homebrew is installed: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"" >&2
                        elif [ "$DETECTED_PLATFORM" = "linux" ]; then
                            echo "    3. Check if you have sudo permissions" >&2
                            echo "    4. Try alternative: wget -qO ~/.local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_${ARCH} && chmod +x ~/.local/bin/yq" >&2
                        fi
                        INSTALL_FAILED=1
                    fi
                fi
            done
            
            echo ""
            if [ $INSTALL_FAILED -eq 0 ]; then
                echo -e "${GREEN}✓ Dependency installation complete${NC}"
                
                # Final verification of all dependencies
                echo ""
                echo "Verifying installed dependencies..."
                ALL_DEPS_OK=true
                for dep in "${MISSING_DEPS[@]}"; do
                    if command -v "$dep" >/dev/null 2>&1; then
                        echo -e "${GREEN}✓ $dep is available${NC}"
                    else
                        echo -e "${YELLOW}⚠ $dep is not available in PATH${NC}"
                        ALL_DEPS_OK=false
                    fi
                done
                
                if [ "$ALL_DEPS_OK" = false ]; then
                    echo ""
                    echo -e "${YELLOW}Note: Some dependencies may not be in your PATH yet.${NC}"
                    echo "  Try restarting your terminal or running: source ~/.bashrc (or ~/.zshrc)"
                fi
            else
                echo -e "${YELLOW}⚠ Some dependencies failed to install${NC}"
                echo "  You can install them manually using the commands shown above"
            fi
        else
            echo ""
            echo -e "${YELLOW}Skipping dependency installation${NC}"
            echo ""
            echo "You can install them manually:"
            for i in "${!MISSING_DEPS[@]}"; do
                dep="${MISSING_DEPS[$i]}"
                cmd="${DEP_INSTALL_COMMANDS[$i]}"
                if [[ "$cmd" != "#"* ]]; then
                    echo "  $dep: $cmd"
                else
                    echo "  $dep: ${cmd#\# }"
                fi
            done
        fi
    fi
fi

# Detect current shell for PATH configuration
DETECTED_SHELL=""
SHELL_CONFIG_FILE=""

# Try to detect shell from $SHELL environment variable
if [ -n "$SHELL" ]; then
    if [[ "$SHELL" == *"zsh"* ]]; then
        DETECTED_SHELL="zsh"
        SHELL_CONFIG_FILE="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        DETECTED_SHELL="bash"
        # On macOS, bash typically uses .bash_profile, on Linux .bashrc
        if [ "$DETECTED_PLATFORM" = "macos" ]; then
            SHELL_CONFIG_FILE="$HOME/.bash_profile"
        else
            SHELL_CONFIG_FILE="$HOME/.bashrc"
        fi
    elif [[ "$SHELL" == *"fish"* ]]; then
        DETECTED_SHELL="fish"
        SHELL_CONFIG_FILE="$HOME/.config/fish/config.fish"
    fi
fi

# Fallback: try to detect from process name or common files
if [ -z "$DETECTED_SHELL" ]; then
    # Check for common shell config files that exist
    if [ -f "$HOME/.zshrc" ]; then
        DETECTED_SHELL="zsh"
        SHELL_CONFIG_FILE="$HOME/.zshrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        DETECTED_SHELL="bash"
        SHELL_CONFIG_FILE="$HOME/.bash_profile"
    elif [ -f "$HOME/.bashrc" ]; then
        DETECTED_SHELL="bash"
        SHELL_CONFIG_FILE="$HOME/.bashrc"
    elif [ -f "$HOME/.profile" ]; then
        DETECTED_SHELL="sh"
        SHELL_CONFIG_FILE="$HOME/.profile"
    else
        # Default fallback
        if [ "$DETECTED_PLATFORM" = "macos" ]; then
            DETECTED_SHELL="zsh"  # macOS default is zsh
            SHELL_CONFIG_FILE="$HOME/.zshrc"
        else
            DETECTED_SHELL="bash"
            SHELL_CONFIG_FILE="$HOME/.bashrc"
        fi
    fi
fi

# Check if install directory is in PATH
PATH_INCLUDES_INSTALL_DIR=false
# Handle case where PATH might be unset
if [ -n "${PATH:-}" ]; then
    if [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
        PATH_INCLUDES_INSTALL_DIR=true
    fi
fi

# Also check if command is available (works for both interactive and non-interactive shells)
COMMAND_AVAILABLE=false
if command -v "$INSTALL_NAME" >/dev/null 2>&1; then
    COMMAND_AVAILABLE=true
    PATH_INCLUDES_INSTALL_DIR=true  # If command works, PATH is effectively correct
fi

if [ "$PATH_INCLUDES_INSTALL_DIR" = false ]; then
    echo ""
    echo -e "${YELLOW}Warning: $INSTALL_DIR is not in your PATH${NC}"
    echo ""
    
    # Provide shell-specific guidance
    if [ -n "$DETECTED_SHELL" ] && [ -n "$SHELL_CONFIG_FILE" ]; then
        echo "Detected shell: $DETECTED_SHELL"
        echo "Config file: $SHELL_CONFIG_FILE"
        echo ""
        
        # Platform-specific guidance
        if [ "$DETECTED_PLATFORM" = "macos" ]; then
            echo "On macOS, you can add the PATH in one of these ways:"
            if [ "$DETECTED_SHELL" = "zsh" ]; then
                echo "  1. Add to ~/.zshrc (recommended for zsh)"
            elif [ "$DETECTED_SHELL" = "bash" ]; then
                echo "  1. Add to ~/.bash_profile (recommended for bash on macOS)"
            fi
            echo "  2. Add to ~/.profile (works for all shells)"
        else
            echo "On Linux, you can add the PATH in one of these ways:"
            if [ "$DETECTED_SHELL" = "zsh" ]; then
                echo "  1. Add to ~/.zshrc (recommended for zsh)"
            elif [ "$DETECTED_SHELL" = "bash" ]; then
                echo "  1. Add to ~/.bashrc (recommended for bash on Linux)"
            fi
            echo "  2. Add to ~/.profile (works for all shells)"
        fi
        echo ""
        
        # Offer to add PATH automatically
        if [ -f "$SHELL_CONFIG_FILE" ] && [ -w "$SHELL_CONFIG_FILE" ]; then
            # Check if PATH is already in config file
            if ! grep -q "PATH.*$INSTALL_DIR" "$SHELL_CONFIG_FILE" 2>/dev/null; then
                # Only prompt if running in interactive mode
                ADD_PATH=false
                if [ -t 0 ]; then
                    read -p "Would you like to add $INSTALL_DIR to your PATH automatically? [y/N] " -n 1 -r
                    echo
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        ADD_PATH=true
                    fi
                else
                    # Non-interactive mode: skip automatic PATH addition
                    ADD_PATH=false
                fi
                
                if [ "$ADD_PATH" = true ]; then
                    echo ""
                    echo "Adding PATH to $SHELL_CONFIG_FILE..."
                    echo "" >> "$SHELL_CONFIG_FILE"
                    echo "# Added by Ralph install script" >> "$SHELL_CONFIG_FILE"
                    # Use fish_add_path for fish shell, export PATH for others
                    if [ "$DETECTED_SHELL" = "fish" ]; then
                        echo "fish_add_path $INSTALL_DIR" >> "$SHELL_CONFIG_FILE"
                    else
                        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$SHELL_CONFIG_FILE"
                    fi
                    echo -e "${GREEN}✓ Added PATH to $SHELL_CONFIG_FILE${NC}"
                    echo ""
                    echo "To use Ralph immediately, run:"
                    echo -e "${GREEN}  source $SHELL_CONFIG_FILE${NC}"
                    echo ""
                    echo "Or restart your terminal."
                    echo ""
                else
                    echo ""
                    echo "Manual configuration:"
                    echo "Add this line to $SHELL_CONFIG_FILE:"
                    echo -e "${GREEN}export PATH=\"\$PATH:$INSTALL_DIR\"${NC}"
                    echo ""
                    echo "Then run:"
                    echo -e "${GREEN}  source $SHELL_CONFIG_FILE${NC}"
                    echo ""
                fi
            else
                echo "PATH already configured in $SHELL_CONFIG_FILE"
                echo "You may need to restart your terminal or run:"
                echo -e "${GREEN}  source $SHELL_CONFIG_FILE${NC}"
                echo ""
            fi
        else
            # Config file doesn't exist or isn't writable - provide manual instructions
            echo "Manual configuration:"
            if [ ! -f "$SHELL_CONFIG_FILE" ]; then
                echo "Create $SHELL_CONFIG_FILE and add:"
            else
                echo "Add this line to $SHELL_CONFIG_FILE:"
            fi
            echo -e "${GREEN}export PATH=\"\$PATH:$INSTALL_DIR\"${NC}"
            echo ""
            if [ "$DETECTED_SHELL" = "fish" ]; then
                echo "For fish shell, use:"
                echo -e "${GREEN}fish_add_path $INSTALL_DIR${NC}"
                echo ""
            fi
            echo "Then run:"
            if [ "$DETECTED_SHELL" = "zsh" ]; then
                echo -e "${GREEN}  source ~/.zshrc${NC}"
            elif [ "$DETECTED_SHELL" = "bash" ]; then
                if [ "$DETECTED_PLATFORM" = "macos" ]; then
                    echo -e "${GREEN}  source ~/.bash_profile${NC}"
                else
                    echo -e "${GREEN}  source ~/.bashrc${NC}"
                fi
            elif [ "$DETECTED_SHELL" = "fish" ]; then
                echo -e "${GREEN}  source ~/.config/fish/config.fish${NC}"
            else
                echo -e "${GREEN}  source $SHELL_CONFIG_FILE${NC}"
            fi
            echo ""
        fi
    else
        # Fallback: generic instructions
        echo "Add this to your shell configuration file (~/.bashrc, ~/.zshrc, or ~/.profile):"
        echo -e "${GREEN}export PATH=\"\$PATH:$INSTALL_DIR\"${NC}"
        echo ""
        echo "Then restart your terminal or run:"
        echo "  source ~/.bashrc  # (or ~/.zshrc, ~/.profile)"
        echo ""
    fi
else
    echo ""
    echo -e "${GREEN}✓ Installation complete!${NC}"
    echo ""
    echo "Ralph CLI has been successfully installed to: $INSTALL_PATH"
    echo ""
    echo "You can now run:"
    echo "  $INSTALL_NAME init"
    echo "  $INSTALL_NAME run"
    echo ""
    
    # Test if it works
    if command -v "$INSTALL_NAME" >/dev/null 2>&1; then
        echo "Testing installation..."
        if "$INSTALL_NAME" --help >/dev/null 2>&1 || "$INSTALL_NAME" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Installation verified - Ralph CLI is working!${NC}"
        else
            echo -e "${YELLOW}⚠ Installation complete, but verification test failed${NC}"
            if [ -n "$SHELL_CONFIG_FILE" ]; then
                echo "  You may need to restart your terminal or run: source $SHELL_CONFIG_FILE"
            else
                echo "  You may need to restart your terminal"
            fi
        fi
    fi
fi
