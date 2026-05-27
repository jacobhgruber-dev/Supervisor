# Architect Mode

**Trigger:** `architect` or `/architect`

Full creative redesign mode. Ignores existing files. Thinks from scratch: "If we were starting from scratch today, how would we build this entire module to be world-class?"

## Why This Behavior

Without architect mode, an AI naturally anchors to what already exists — it proposes incremental changes to the current codebase out of caution and respect for existing decisions. That's the right default for most work. But for greenfield features or deep rewrites, anchoring to current code constrains thinking before it starts. Architect mode severs that anchor deliberately: it forces the AI to do divergent thinking first, converging on an ideal design before considering migration costs. You get the best design the AI is capable of, not the most comfortable change.

## When to Use

- You're starting a greenfield feature but want a bold design before touching code
- An existing module has accumulated too much technical debt and needs rethinking
- You want the AI to explore alternatives without being anchored to current implementation

## What It Changes

- No deference to existing code, patterns, or file structure
- Thinks in terms of ideal architecture, not incremental migration
- May propose different frameworks, patterns, or abstractions
- Designs for the future, not constrained by the past

## Example

> architect We need a user notification system that supports email, push, and in-app. Design it.
