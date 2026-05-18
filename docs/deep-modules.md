# Deep modules vs shallow modules

Matt's skills borrow this from John Ousterhout's *A Philosophy of Software Design*.

A **module** is anything with an interface and an implementation—a function, class, package, or tier-spanning slice. **Depth** is measured at the **interface**: how much behavior a caller (or test) gets per unit of interface they must learn.

## Definitions

**Deep module** = small interface + lots of implementation behind it. Callers learn little and get a lot of behavior.

**Shallow module** = large interface + thin implementation (often a pass-through). Callers must learn almost as much as reading the implementation. Avoid when you can deepen instead.

```
Deep:     [ small API ] ──► complex logic hidden inside
Shallow:  [ large API ] ──► thin wrapper / delegate
```

Visually (from the TDD skill):

```
┌─────────────────────┐
│   Small Interface   │  ← few methods, simple params
├─────────────────────┤
│                     │
│  Deep Implementation│  ← complex logic hidden
│                     │
└─────────────────────┘

┌─────────────────────────────────┐
│       Large Interface           │  ← many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← mostly passes through
└─────────────────────────────────┘
```

## Interface is more than types

The **interface** is everything a caller must know to use the module correctly: signatures, invariants, ordering constraints, error modes, required configuration, and performance characteristics—not just the type-level API.

**Depth is a property of the interface, not the implementation.** A deep module can be built from many small, mockable, swappable parts internally; they stay private. It can have **internal seams** (for its own tests) separate from the **external seam** at its public interface.

## Why it matters in these skills

### TDD (`tdd`)

Tests should exercise behavior through the **public interface**. Deep modules give a stable, high-leverage test surface; shallow ones force tests to chase implementation or mock large graphs.

When planning, ask:

- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity inside?

After a cycle, shallow modules are refactor candidates: **combine or deepen**.

### PRDs and planning (`to-prd`, `to-issues`)

Sketch major modules and look for **deep modules**—lots of functionality behind a simple, testable interface that rarely changes.

### Architecture (`improve-codebase-architecture`)

Surface places where the interface is nearly as complex as the implementation. Propose **deepening**: pull complexity behind a simpler API so callers and tests get more **leverage** and maintainers get more **locality** (change in one place, fixed everywhere).

At network boundaries: define a **port** (interface) at the seam; the deep module owns the logic; **adapters** (HTTP, in-memory, queue) satisfy the port in production vs tests.

## Deletion test

Imagine deleting the module:

- If complexity **vanishes**, it was not hiding anything (pass-through) → likely **shallow**.
- If complexity **reappears across many callers**, it was earning its keep → likely **deep**.

## Shallow smells

- Many methods or heavy parameters for little real logic
- Wrappers that mostly forward to something else
- Tests that must poke internals or mock half the system to get confidence
- Interface nearly as hard to learn as the implementation

## Deepening

Move complexity **behind** a smaller, clearer interface. Combine shallow pass-throughs, or introduce a port + adapters so one module owns the logic while transport varies.

**One-line summary:** a **deep** module offers much behavior behind a small interface; a **shallow** module makes callers learn almost as much as the code inside.

## Related skills

- [`tdd`](../skills/engineering/tdd/SKILL.md) — plan and refactor toward deep modules
- [`tdd/deep-modules.md`](../skills/engineering/tdd/deep-modules.md) — short reference used during TDD
- [`improve-codebase-architecture`](../skills/engineering/improve-codebase-architecture/SKILL.md) — find and propose deepening opportunities
- [`improve-codebase-architecture/LANGUAGE.md`](../skills/engineering/improve-codebase-architecture/LANGUAGE.md) — full vocabulary (module, seam, adapter, leverage, locality)
