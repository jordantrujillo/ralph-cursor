# Ralph — set up this repository

Use this checklist for a **project you opened in Cursor** (any git repo). Ralph loop = Beads + Cursor CLI worker; slash commands for PRD live under `~/.cursor/commands/` after bootstrap.

---

## Agent instruction (when user runs this command)

**Do this automatically unless the user explicitly opts out:**

1. Workspace root = the open project (where `.git` / work lives).
2. After **`bd init`** (or if `.beads/` already exists), run **`ralph setup`** from a terminal **at workspace root** so **`.beads/`** is added to **`.gitignore`** (with the other Ralph lines). Untracked **`AGENTS.md`** / **`CLAUDE.md`** from Beads are included automatically; already-tracked copies are left out. Prefer the CLI — do not hand-edit unless `ralph setup` fails.

```bash
RALPH_ROOT=$(tr -d '\n' < ~/.config/ralph-cursor/package_root)
python3 "$RALPH_ROOT/bin/ralph.py" setup --project "$(pwd)"
```

3. Confirm **`.gitignore`** contains the `# >>> ralph-cursor` block, **`.beads/`**, and (when `bd init` created them as **untracked** files) **`AGENTS.md`** / **`CLAUDE.md`** entries added by `ralph setup`. If `install-cursor` was never run, tell the user to run it once from their ralph-cursor clone (see below).

Only skip writing gitignore if the user asked not to touch gitignore — then use `setup --project "$(pwd)" --skip-gitignore` and say so in the reply.

---

## Prerequisites (machine)

- [Beads](https://github.com/steveyegge/beads) `bd` on PATH
- Cursor CLI (`cursor-agent` or `agent`) installed and authenticated
- Python 3

---

## One-time bootstrap (per machine)

If global Ralph commands are missing from the `/` menu:

1. Keep a local clone of the **ralph-cursor** repository (this repo).
2. Run:

```bash
python3 /ABS/PATH/TO/ralph-cursor/bin/ralph.py install-cursor
```

That copies command files to `~/.cursor/commands/` and writes **`~/.config/ralph-cursor/package_root`** (single line = absolute path to the ralph-cursor repo root). Reload Cursor if commands do not appear.

---

## This repository

1. **Beads** — from repo root, if `.beads/` is missing:

```bash
bd init
```

2. **Gitignore (includes `.beads/`; Beads-only `AGENTS.md` / `CLAUDE.md`)** — **run this** so Beads data and PRD scratch paths are not committed. `ralph setup` merges the Ralph block; it also adds **`AGENTS.md`** and **`CLAUDE.md`** only when those files exist and are **not yet tracked by git** (typical right after `bd init`). If you already had committed copies before Beads, they stay out of the ignore list.

```bash
RALPH_ROOT=$(tr -d '\n' < ~/.config/ralph-cursor/package_root)
python3 "$RALPH_ROOT/bin/ralph.py" setup --project "$(pwd)"
```

To skip any `.gitignore` edit: add **`--skip-gitignore`** to that command.

3. **PRD → Beads** — use `/prd-to-beads` (or `generate-prd`) from the command palette after bootstrap.

4. **Run the loop** (portable; no `scripts/ralph/` in this repo required):

```bash
RALPH_ROOT=$(tr -d '\n' < ~/.config/ralph-cursor/package_root)
python3 "$RALPH_ROOT/bin/ralph.py" run --project "$(pwd)" 10
```

Optional: symlink `ralph` onto `PATH` pointing at `bin/ralph.py` so you can type `ralph run --project .`.

---

## Legacy layout

If this repo already has `./scripts/ralph/ralph.py` from `ralph init`, plain `ralph run` from that repo still works.
