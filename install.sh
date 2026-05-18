#!/bin/bash
# Deprecated: Ralph no longer uses this script as the primary installer.
# Bootstrap global Cursor commands and config with:
#
#   python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bin/ralph.py" install-cursor
#
# Optional: add the CLI to PATH (example):
#   ln -sf "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bin/ralph.py" "$HOME/.local/bin/ralph"

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "install.sh is deprecated."
echo "Run:"
echo "  python3 \"$ROOT/bin/ralph.py\" install-cursor"
echo ""
echo "Then open Cursor and use /ralph-setup (or other Ralph commands) from any workspace."
