# Plan Mode

**Trigger:** `plan` or `/plan`

Step-by-step planning mode. Creates a clear plan with options, risks, and accessibility notes. No code is written until a plan is agreed on.

## Why This Behavior

The biggest time-sink in software isn't writing code — it's rewriting code after realizing the approach was wrong. AI assistants default to action: give them a task and they start implementing. Plan mode puts a deliberate pause before execution. By laying out options, tradeoffs, dependencies, and risks first, the plan becomes a shared artifact you can review, adjust, or reject before any code is written.

## What It Covers

- Task breakdown into ordered, executable steps with dependencies mapped
- Multiple approaches with explicit pros/cons and tradeoff analysis
- Milestone planning and effort estimation
- Risk identification: what could fail, what's unknown, what needs investigation first
- Verification steps: how to confirm each phase is complete and correct
- Accessibility and edge-case considerations (important for church, community, public-facing projects)

## What It Changes

- No code is written until a plan is agreed on
- Output is structured: phases, dependencies, verification steps, fallback options
- Identifies unknowns and proposes spikes or research to resolve them
- Thinks about sequencing: what depends on what, what can be parallelized
- Flags accessibility, edge-case, and inclusion concerns

## When to Use

- Before starting a complex or multi-step feature
- When you need to see tradeoffs between different approaches
- Stakeholder communication — get a clear plan to share before committing
- Estimating effort or scoping work for a sprint
- Projects where accessibility or inclusion matters

## How It Differs from Architect Mode

Architect says "build a bridge here using a suspension design." Planner says "Phase 1: survey site. Phase 2: pour foundations. Phase 3: erect towers..." Architect designs structure; Planner sequences the build.

## Example

> plan We need to add dark mode support to our React app. Lay out the approach.
