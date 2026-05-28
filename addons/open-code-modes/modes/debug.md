# Debug Mode

**Trigger:** `debug` or `/debug`

Bug investigation mode. Carefully finds root causes through hypothesis-driven investigation — questions and checks before fixes.

## Why This Behavior

The default AI behavior under time pressure is to propose a fix immediately. This is dangerous — a symptom-level fix masks the real bug and often creates new ones. Debug mode simulates how an experienced engineer actually debugs: gather evidence, form hypotheses, test the cheapest hypothesis first, confirm before fixing. It also forces clarifying questions (logs, environment, reproduction) rather than guessing, because the AI can't see your runtime.

## What It Covers

- Gathering evidence: logs, stack traces, reproduction steps, affected versions, environment details
- Forming and testing hypotheses systematically, cheapest first
- Tracing from symptom to root cause — not just "what broke" but "why it broke"
- Considering: race conditions, memory leaks, distributed system failures, heisenbugs, environmental factors
- Explaining the "why" behind the bug, not just the fix

## What It Changes

- Asks clarifying questions before jumping to fixes
- Builds hypothesis lists and designs tests to narrow them down
- Prioritizes root cause over symptom patching
- Doesn't write a fix until the cause is confirmed
- Explains the chain of causation clearly

## When to Use

- A bug is reported but the cause isn't obvious
- You've already tried a fix and it didn't work
- Intermittent or environment-specific issues
- Production incidents needing fast, accurate diagnosis
- Crash reports, error logs, mysterious behavior — anything where "it works on my machine" isn't enough

## Example

> debug Users report the checkout button works in Chrome but not Safari. Find the root cause.
