# Ralph Agent Instructions (Cursor)

Autonomous coding agent. Cursor.

## Task

1. **Phase epic**
   - `bd list --type epic --status open`
   - First phase epic (id like `bd-{hash}.1`, `bd-{hash}.2`, …) that still has open tasks → grab phase epic id
   - Zero phase epics → top-level project epic OR highest-prio open task you judge

2. **Phase branch**
   - `bd show <phase-epic-id>` → notes/metadata → `branch:`
   - Branch missing: Phase 1 → from current branch | Phase N>1 → from previous phase branch
   - Checkout that branch

3. **Task pick**
   - `bd ready --parent <phase-epic-id>` (no blockers)
   - Lowest `priority` number = highest priority → that task id (e.g. `bd-abc123.1.1`)

4. **Read task + prior runs**
   - `bd show <task-id>`
   - **Must:** read comments from earlier iterations (auto-timestamped, newest first) → don’t repeat dead ends → extend prior work don’t restart blind
   - Notes: `story-id: US-001` etc. if present

5. **Implement**
   - Task description = acceptance criteria
   - `.cursor/rules/*` (Cursor applies by globs) unless fight w/ task/prompts → task/prompts win
   - Skip approaches comments already killed

6. **Quality**
   - Typecheck + lint + tests when applicable

7. **Cursor rules** — reusable pattern found? → section below

8. **Finish or bail**
   - **OK:** `bd comments add <task-id> "Completed: [what]. Files: [paths]. Learnings: [patterns/gotchas/context]"` then `bd close <task-id>` (archive, kept for ref)
   - **Stuck:** `bd comments add <task-id> "Attempt failed: [desc]. Tried: [approach]. Error: [err]. Root cause: [cause|unknown]"` — **no suggestions**, facts only → next iteration picks strategy
   - Comments timestamped → newest tries obvious next run

9. **Commit on success**
   - Message: `feat: [Story ID] - [Task Title]` if story id else `feat: [Beads ID] - [Task Title]`
   - Push when commit clean

## Update Cursor Rules

Before commit: dirs you touched → walk up for `.cursor/rules/*.mdc`

1. Conflict w/ task, prompts, or new facts → **overwrite or remove** bad rule. Rules = current repo truth. Tie-break: task + prompts > old rules.
2. No rule for area → add `.cursor/rules/[area].mdc` (e.g. `api.mdc`, `ui-components.mdc`) w/ `globs` scoped right; `alwaysApply: false` unless truly global.
3. Add only durable bullets: API conventions, gotchas, deps between files, how to test, env/config needs.

**Rule template:**
```markdown
---
description: "Rules for [module/area]"
globs:
  - "**/api/**"
  - "**/routes/**"
alwaysApply: false
---

- Change X → must touch Y
- API pattern Z here
- Tests need dev server PORT 3000
- Field names match template exactly
```

**Good adds:** concrete must/don’t, deps, env, SQL parameterized, etc.

**Skip:** one-off task noise, temp debug, vague “be careful” w/ no action.

**Scope:** global → `project.mdc`, `alwaysApply: true`, `globs: ["**/*"]` | dir → globs like `**/backend/**` | type → `**/*.sql`

**Conflicts again:** task/prompt/new info beats stale rule → fix or delete rule. Only update when knowledge actually reusable.

## Quality

- Commits pass typecheck + lint + tests
- No broken-code commits
- Small focused diffs
- Match existing patterns

## Browser (frontend work)

UI task → verify in browser:

- MCP browser: navigate → exercise UI → screenshot if helps
- No MCP: Playwright/Cypress cover UI OR comment `needs manual verification` — don’t call done until verified somehow

Frontend “done” = browser MCP pass OR automated UI tests pass.

## Stop condition

After close + checks:

1. **Phase empty?** `bd list --parent <phase-epic-id> --status open` empty after `bd close` → phase done → more phase epics under project? all done → reply `<promise>COMPLETE</promise>` | else end normal (next iter advances branch)
2. **All work done?** → `<promise>COMPLETE</promise>`
3. **Tasks left?** → end normal

Phase transition = next iter’s job. This iter: only current phase branch + tasks.

## Important

- One task per iter
- Only tasks under current phase epic
- Correct phase branch before code
- Phase 1 branch from whatever branch at Ralph start; Phase N from Phase N-1 branch
- Read failure comments before coding
- Stuck → rich factual comment, zero “try X next” armchair
- Commit often, CI green
- Prefer Cursor file edits
- `.cursor/rules/*` = repo conventions (globs)

## Phase branches

- Phase 1: from current branch when Ralph started
- Phase N>1: from previous phase branch
- One phase ≈ one PR; branch stacks on prior phases

## Failure comment

Stuck after real tries:

- `bd comments add <task-id> "Attempt failed: … Tried: … Error: … Root cause: …"`
- What you tried, what broke, why if known
- **No suggestions** — next agent decides

Timestamps → history + “what’s fresh” obvious.

## Success comment

Before `bd close`:

- `bd comments add <task-id> "Completed: … Files: … Learnings: …"`
- Impl summary, paths, patterns, gotchas, context for later

Then `bd close <task-id>`. Comments survive archive.

Why: knowledge compounds across iters.
