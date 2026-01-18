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

# Check if ralph.py exists
if [ ! -f "$RALPH_SCRIPT" ]; then
    echo -e "${RED}Error: $RALPH_SCRIPT not found${NC}" >&2
    exit 1
fi

# Determine install location
# Prefer ~/.local/bin for user installs, fall back to /usr/local/bin for system installs
if [ -w "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
    INSTALL_DIR="$HOME/.local/bin"
    USE_SYMLINK=true
elif [ -w "/usr/local/bin" ]; then
    INSTALL_DIR="/usr/local/bin"
    USE_SYMLINK=true
else
    echo -e "${RED}Error: No writable directory found. Tried:${NC}" >&2
    echo "  - $HOME/.local/bin" >&2
    echo "  - /usr/local/bin" >&2
    echo "" >&2
    echo "Please create one of these directories or run with sudo for system-wide install." >&2
    exit 1
fi

INSTALL_PATH="$INSTALL_DIR/$INSTALL_NAME"

# Check if already installed
if [ -f "$INSTALL_PATH" ] || [ -L "$INSTALL_PATH" ]; then
    echo -e "${YELLOW}Warning: $INSTALL_PATH already exists${NC}"
    read -p "Overwrite? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    rm -f "$INSTALL_PATH"
fi

# Install the script
echo "Installing Ralph CLI..."
if [ "$USE_SYMLINK" = true ]; then
    # Create symlink to preserve updates
    ln -s "$RALPH_SCRIPT" "$INSTALL_PATH"
    echo -e "${GREEN}Created symlink: $INSTALL_PATH -> $RALPH_SCRIPT${NC}"
else
    # Copy the file
    cp "$RALPH_SCRIPT" "$INSTALL_PATH"
    echo -e "${GREEN}Copied to: $INSTALL_PATH${NC}"
fi

# Make executable
chmod +x "$INSTALL_PATH"
echo -e "${GREEN}Made executable${NC}"

# Check if install directory is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo -e "${YELLOW}Warning: $INSTALL_DIR is not in your PATH${NC}"
    echo ""
    echo "Add this to your ~/.bashrc, ~/.zshrc, or ~/.profile:"
    echo -e "${GREEN}export PATH=\"\$PATH:$INSTALL_DIR\"${NC}"
    echo ""
    echo "Then run: source ~/.bashrc  # (or ~/.zshrc)"
    echo ""
else
    echo ""
    echo -e "${GREEN}✓ Installation complete!${NC}"
    echo ""
    echo "You can now run: $INSTALL_NAME init"
    echo "              or: $INSTALL_NAME run"
    echo ""
    
    # Test if it works
    if command -v "$INSTALL_NAME" >/dev/null 2>&1; then
        echo "Testing installation..."
        "$INSTALL_NAME" --help 2>/dev/null || "$INSTALL_NAME" 2>/dev/null || true
    fi
fi
