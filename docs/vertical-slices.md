# Vertical slices

In Matt Pocock's skills, a **vertical slice** is a thin **tracer bullet**: one narrow path through **every integration layer**, not one layer across the whole feature.

## Vertical vs horizontal

| Horizontal (avoid) | Vertical (prefer) |
| ------------------ | ----------------- |
| All database work, then all API work, then all UI | One user-visible behavior, with schema → API → UI → tests together |
| Large batches; nothing demoable until the end | Each slice is **complete**, **verifiable**, and **demoable** on its own |

**Horizontal slicing** means finishing one layer (or one kind of work) for the entire feature before moving to the next. **Vertical slicing** means delivering the smallest shippable story that cuts through all layers.

## Where this shows up

### Planning work (`to-issues`)

Break a plan, spec, or PRD into **independently grabbable issues**. Each issue should:

- Cut **end-to-end** (for example schema, API, UI, tests)
- Describe **behavior**, not layer-by-layer tasks like "implement the service layer"
- Prefer **many thin slices** over a few thick ones
- Be **AFK** when an agent can implement and merge without human input, or **HITL** when a decision or review is required (prefer AFK where possible)

### Building with TDD (`tdd`)

Apply the same idea in a red–green–refactor loop:

```
Wrong (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

Right (vertical):
  RED→GREEN: test1 → impl1
  RED→GREEN: test2 → impl2
  RED→GREEN: test3 → impl3
  ...
```

Write **one** test that confirms **one** behavior, then the minimal code to pass. Repeat. The first passing test is the **tracer bullet**: it proves the full path works end-to-end before you widen the feature.

## Why vertical slices

Horizontal batches tend to produce tests and plans that chase **imagined** structure rather than real behavior. You often have no working system until everything is done, and work is hard to parallelize or hand off.

Vertical slices keep a **working thin path** at all times. You learn from real code, tests stay tied to observable behavior, and each issue or cycle can be picked up without owning the whole epic.

## One-line summary

A vertical slice is the smallest **shippable** unit of behavior through **all** layers—not the largest chunk of **one** layer.

## Related skills

- [`to-issues`](../skills/engineering/to-issues/SKILL.md) — break plans into vertical-slice issues
- [`tdd`](../skills/engineering/tdd/SKILL.md) — build with tracer-bullet vertical slices
