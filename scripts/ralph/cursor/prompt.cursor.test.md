# Ralph Agent Instructions (Cursor) — Test Mode

TEST MODE. Zero real side effects.

## Behavior

1. Read `prd.yml` if file exists
2. Emit test-only responses
3. No new branches
4. No commits
5. No file writes
6. No git

## Output

Default:
```
Test iteration complete
```

PRD/test data says COMPLETE signal? emit:
```
<promise>COMPLETE</promise>
```

Else: short ack that test iter ran.

## Rules

- TEST = no prod ops
- No checkout
- No commits
- No repo mutation
- Console/output only
