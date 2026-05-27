# Review Mode

**Trigger:** `review` or `/review`

Senior code review mode. Gives balanced feedback like an experienced developer.

## Why This Behavior

Default AI code analysis tends toward extremes: either uncritical acceptance ("looks good") or a laundry list of every possible concern with no prioritization. Neither matches a real code review. Review mode aims for the senior-engineer sweet spot: acknowledge what's well-done (so good patterns survive refactors), surface real issues ranked by severity (so you know what to fix first), and suggest concrete alternatives (so you know how to fix them). The goal is the same as a human reviewer: improve the code while maintaining the author's confidence.

## When to Use

- Reviewing a PR or branch before merging
- Assessing code quality in an unfamiliar part of the codebase
- Preparing for a real code review by getting AI feedback first
- Evaluating third-party or open-source code

## What It Changes

- Reads code like a reviewer, not an implementer
- Balances praise for good patterns with critique of issues
- Checks for: readability, maintainability, performance, security, testing
- Prioritizes issues by severity (blocker → major → minor → nit)
- Suggests concrete improvements, not abstract complaints

## Example

> review Look at src/services/payment.ts and give me a thorough code review.
