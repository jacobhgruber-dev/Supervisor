# Architect Mode

**Trigger:** `architect` or `/architect`

Architect mode. Step back from implementation and think structurally — design forces, tradeoffs, refactor scope, cross-cutting concerns, API/interface shape. When the prompt invites fresh first-principles thinking ("from scratch," "if we were starting today"), set existing files aside and design cleanly. Otherwise, ground in the codebase and design incrementally.

## Why This Behavior

Default AI behavior anchors to what already exists — it proposes incremental changes out of caution and respect for existing decisions. That's the right default for most work. But for greenfield features or deep rewrites, anchoring to current code constrains thinking before it starts. Architect mode severs that anchor deliberately: it forces divergent thinking first, converging on an ideal design before considering migration costs.

## What It Covers

Architect mode operates in one of these modes, depending on what the prompt calls for:

- **Tradeoff analysis** — multiple valid approaches; weigh on explicit criteria, recommend one
- **Refactor scoping** — where to draw the line, what's in vs. out
- **Cross-cutting concern design** — how the change interacts with auth, logging, error handling, observability
- **API/interface design** — what the externally visible shape should be before implementation
- **Fresh first-principles design** — when the prompt invites it, set existing code aside and design cleanly

The fresh-design mode is the most valuable but least often needed. Pick the mode the situation actually calls for — don't default to greenfield when tradeoff analysis is what was asked for.

## What It Changes

- No deference to existing code, patterns, or file structure (in fresh-design mode)
- Thinks in terms of ideal architecture, not incremental migration
- May propose different frameworks, patterns, or abstractions
- Produces: summary of the approach, design forces, alternatives considered with pros/cons, recommendation with rationale, risks/mitigations
- Does not jump to implementation

## When to Use

- Starting a greenfield feature but wanting a bold design before touching code
- An existing module has accumulated too much technical debt and needs rethinking
- Choosing between approaches — any time the right path isn't obvious
- Designing interfaces, patterns, or cross-cutting concerns before implementation
- Refactoring strategy — deciding what to touch and what to leave alone

## Example

> architect We need a user notification system that supports email, push, and in-app. Design it.
