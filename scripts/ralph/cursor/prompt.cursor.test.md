# Ralph Agent Instructions (Cursor) - Test Mode

TEST MODE. No real operations.

## Test Mode Behavior

1. Read `prd.yml` (if exists)
2. Output test responses
3. No branch creation
4. No commits
5. No file modifications
6. No git commands

## Expected Test Output

Output:
```
Test iteration complete
```

COMPLETE signal in PRD/test data? Output:
```
<promise>COMPLETE</promise>
```

Otherwise, acknowledge test iteration.

## Important

- TEST mode - no real operations
- No branch checkout
- No commits
- No repo modifications
- Output test responses only
