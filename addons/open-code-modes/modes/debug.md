# Debug Mode

**Trigger:** `debug` or `/debug`

Bug investigation mode. Carefully finds root causes with questions and checks.

## Why This Behavior

The default AI behavior under time pressure is to propose a fix immediately. This is dangerous — a symptom-level fix masks the real bug and often creates new ones. Debug mode simulates how an experienced engineer actually debugs: gather evidence, form hypotheses, test the cheapest hypothesis first, confirm before fixing. It also forces the AI to ask you clarifying questions (logs, environment, reproduction) rather than guessing, because the AI can't see your runtime. The most expensive fix is the wrong fix. This mode prevents that.

## When to Use

- A bug is reported but the cause isn't obvious
- You've already tried a fix and it didn't work
- Intermittent or environment-specific issues
- Production incidents needing fast diagnosis

## What It Changes

- Asks clarifying questions before jumping to fixes
- Gathers evidence: logs, reproduction steps, affected versions
- Forms and tests hypotheses systematically
- Explains the "why" behind the bug, not just the fix
- Prioritizes root cause over symptom patching

## Example

> debug Users report the checkout button works in Chrome but not Safari. Find the root cause.
