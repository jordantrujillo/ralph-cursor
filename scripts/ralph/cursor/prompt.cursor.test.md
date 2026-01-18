# Ralph Agent Instructions (Cursor) - Test Mode

You are running in TEST MODE. Do NOT perform any real operations.

## Test Mode Behavior

When running in test mode, you should:
1. Read the PRD at `prd.yml` (if it exists)
2. Output test-friendly responses
3. Do NOT create branches
4. Do NOT commit changes
5. Do NOT modify files
6. Do NOT run git commands

## Expected Test Output

Simply output:
```
Test iteration complete
```

If you see a COMPLETE signal in the PRD or test data, output:
```
<promise>COMPLETE</promise>
```

Otherwise, just acknowledge the test iteration.

## Important

- This is a TEST - do not perform any real operations
- Do not check out branches
- Do not commit code
- Do not modify the repository
- Just output test responses
