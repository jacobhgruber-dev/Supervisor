# Plan Mode

**Trigger:** `plan` or `/plan`

Step-by-step planning mode. Creates a clear plan with options, risks, and accessibility notes.

## Why This Behavior

The biggest time-sink in software isn't writing code — it's rewriting code after realizing the approach was wrong. AI assistants default to action: give them a task and they start implementing. Plan mode puts a deliberate pause before execution. By forcing the AI to lay out options, tradeoffs, and risks first, you offload the "think through the implications" step. The plan becomes a shared artifact you can review, adjust, or reject before any code is written. For teams, it doubles as a communication tool — a plan is easier to discuss than a PR.

## When to Use

- Before starting a complex or multi-step feature
- When you need to see tradeoffs between different approaches
- Stakeholder communication — get a clear plan to share before committing
- Projects where accessibility or inclusion matters (church, community, public-facing)

## What It Changes

- No code is written until a plan is agreed on
- Presents multiple approaches with pros/cons
- Identifies risks, dependencies, and unknowns
- Includes accessibility and edge-case considerations
- Output is structured: phases, verification steps, fallback options

## Example

> plan We need to add dark mode support to our React app. Lay out the approach.
