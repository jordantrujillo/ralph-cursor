---
name: ralph-portable
description: >
  Ralph autonomous loop on any repo: bootstrap install-cursor, Beads, gitignore
  block, run --project. Use when user asks portable Ralph, ralph-cursor setup, or
  ~/.cursor/commands Ralph workflow.
---

# Ralph portable

## Bootstrap (once per machine)

```bash
python3 /path/to/ralph-cursor/bin/ralph.py install-cursor
```

Installs `~/.cursor/commands/*.md`, optional skill copy, `~/.config/ralph-cursor/package_root`.

## Per repo

- `bd init` if no `.beads/`
- `python3 "$(tr -d '\n' < ~/.config/ralph-cursor/package_root)/bin/ralph.py" setup --project .` → `.gitignore` marker block (`.beads/`, PRD glob, legacy `scripts/ralph/` paths; **`AGENTS.md` / `CLAUDE.md`** only when untracked — typical after `bd init`)
- PRD → issues: slash `/prd-to-beads` or read `~/.cursor/commands/prd-to-beads.md`

## Loop

```bash
python3 "$(tr -d '\n' < ~/.config/ralph-cursor/package_root)/bin/ralph.py" run --project "$(pwd)"
```

Legacy: `ralph init` in repo then `ralph run` uses local `scripts/ralph/ralph.py`.
