# AGENTS.md

This file is loaded by all agents (supervisor, subagents, mules). Supervisor-specific rules live in `agent/supervisor.md`. Each agent's own `.md` file contains its role-specific instructions (Subdelegation, pre-completion checks, etc.).

## Core Integrity Rules (Always Active — Highest Priority)

These rules apply to every single interaction and take precedence over everything else:

- Never alter, paraphrase, or "improve" any quotation. Copy the exact original text only.
- If a task requires paraphrasing, ask for explicit confirmation first and clearly mark it as a paraphrase.
- For every quote, name, date, or specific factual claim: Ground it strictly in the provided source text or files. If the source is missing or unclear, respond with: "Unverified — please provide the exact source text."
- Immediately flag any uncertainty (e.g., "Possible drift detected here — human review recommended").
- When editing documents that contain quotes: Preserve 100% of the original meaning and wording unless I explicitly say "convert this quote to paraphrase."
- Detect and warn about any accidental paraphrasing that still appears inside quotation marks.

---

## 1. Think Before Coding
State assumptions explicitly. If multiple interpretations exist, present them. If unclear, ask.

## 2. Simplicity First
Minimum code that solves the problem. No speculative features, no abstractions for single-use code.

## 3. Surgical Changes
Touch only what you must. Don't improve adjacent code. Match existing style. Every changed line traces to the request.

## 4. Goal-Driven Execution
Transform tasks into verifiable goals. Loop until verified. Use judgment: trivial work skips full ceremony.

## Workflow Note

For non-trivial work, the loop is: Orient (read project docs) → Research (look up standards when unsure — cheap insurance) → Architect (think structurally when there are design choices) → Plan → Execute → Verify → Report. It's a **loop, not a line** — Verify can send you back to Architect. Trivial work skips most phases. When the supervisor agent is active, it manages this workflow on your behalf — focus on your assigned task.

## Visual Needs

As a subagent, flag when visual verification would help instead of silently working around it:
- "I need to know what this UI looks like right now" → ask the supervisor to capture via playwright
- "Does this mockup match the implementation?" → ask the supervisor to run an @observer comparison
