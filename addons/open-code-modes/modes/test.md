# Test Mode

**Trigger:** `test` or `/test`

Testing-first mode. Focuses on tests and verification before or alongside implementation. Writes tests first, then makes them pass.

## Why This Behavior

AI assistants tend to write implementation first and treat tests as an afterthought — or skip them entirely unless prompted. Test mode inverts that: it makes the AI think about expected behavior before writing a single line of production code. This catches edge cases and unclear requirements early, when they're cheap to fix. For bug fixes, writing a test first proves the bug exists and that the fix actually resolves it — no more "it should work now."

## What It Covers

- Define expected behavior through tests before writing code
- Cover happy paths, error paths, edge cases, and boundary conditions
- Write tests that are maintainable, fast, and deterministic
- Run test suites to verify changes actually pass
- Flag untested code paths and gaps in coverage
- For bug fixes: write a test that reproduces the bug, confirm it fails, then fix

## What It Changes

- Prioritizes test creation over implementation
- Tests become the specification — they define what correct behavior looks like
- Failing test = bug confirmed; passing test = fix verified
- Thinks about edge cases and error handling from the start
- Won't mark a task done until tests pass

## When to Use

- Writing new functionality — write tests before or alongside the code
- Bug fixes — reproduce the bug in a test first, then fix
- Refactoring — ensure test coverage before changing behavior
- Code review — verify that submitted code has adequate tests
- Any time "make sure this works" is part of the ask

## Example

> test Add input validation to the signup form. Write tests for all edge cases first.
