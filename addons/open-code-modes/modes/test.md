# Test Mode

**Trigger:** `test` or `/test`

Testing-first mode. Focuses on tests and verification.

## Why This Behavior

AI assistants tend to write implementation first and treat tests as an afterthought — or skip them entirely unless prompted. Test mode inverts that: it makes the AI think about expected behavior before writing a single line of production code. This catches edge cases and unclear requirements early, when they're cheap to fix. For bug fixes, writing a test first proves the bug exists and that the fix actually resolves it — no more "it should work now." The AI is naturally good at generating test cases; this mode makes sure that skill is used.

## When to Use

- Writing new functionality — write tests before or alongside the code
- Bug fixes — reproduce the bug in a test first, then fix
- Refactoring — ensure test coverage before changing behavior
- Code review — verify that submitted code has adequate tests

## What It Changes

- Prioritizes test creation over implementation
- Defines expected behavior through tests
- Runs test suites to verify changes
- Flags untested code paths and edge cases
- Failing test = bug confirmed; passing test = fix verified

## Example

> test Add input validation to the signup form. Write tests for all edge cases first.
