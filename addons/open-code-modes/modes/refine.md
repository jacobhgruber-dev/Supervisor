# Refine Mode

**Trigger:** `refine` or `/refine`

Surgical + gentle improvements. Stay precise. Suggest small cleanups: "Staying surgical — here is a slightly cleaner/more modern way..."

## Why This Behavior

AI assistants can be overly eager to refactor. Given working code, they'll sometimes propose rewrites that introduce new bugs, change behavior, or violate the original intent — all for the sake of "cleaner code." Refine mode counters this by setting the bar at surgical: only suggest changes that are clearly improvements with near-zero risk. It's the difference between "this could be better" and "here's a drop-in replacement that's strictly better." The mode protects working code from unnecessary churn while still allowing modernization.

## When to Use

- Code works but could be slightly cleaner or more idiomatic
- You want small, safe improvements without risk of breaking things
- After a feature is built, before it ships — final polish pass
- Modernizing older code incrementally

## What It Changes

- Suggests small, focused changes — never rewrites modules
- Prefers clarity and modernity over cleverness
- Makes suggestions, not demands
- Respects existing conventions even if not ideal

## Example

> refine The error handling in auth.ts works but feels clunky. Any small improvements?
