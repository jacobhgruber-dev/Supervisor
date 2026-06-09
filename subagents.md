# Subagents — Quick Reference

9 subagent roles  •  base tier: DeepSeek V4 Pro Max  •  upgrade path: Claude Sonnet/Opus (see agents/UPGRADING.md)

For the full system reference including modes, local agents, and commands, see [reference.md](reference.md).

---

## How the Supervisor Works

The Supervisor is a primary agent in opencode that orchestrates work through specialized subagents. It plans, delegates, reviews outputs, fixes issues, and commits — all while keeping its own context window clean. You (the user) interact with the Supervisor; it manages the subagents behind the scenes.

Key principle: **Delegate everything.** The Supervisor reads docs for orientation, then spawns subagents for all substantive work. It only self-executes mechanical operations like commits and pushes.

---

## Subagents — 9 Roles

### How tiers work

This repo ships with a single tier of agents powered by DeepSeek V4 Pro Max — a frontier model fully capable of professional work. One key, one model, nine specialized agents.

**If you have an Anthropic API key**, you can graduate to a 3-tier system with the naming convention `junior-*` (DeepSeek), bare name (Claude Sonnet), and `senior-*` (Claude Opus). This mirrors the production setup this repo was extracted from. See `agents/UPGRADING.md` for the complete 27-agent spec table with exact models, step counts, and permissions per role per tier.

---

### 1. Architect — System Design & Novel Approaches

Designs new ways to do things. Greenfield thinking, tradeoff analysis.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `architect` | DeepSeek V4 Pro Max | 25 | `#3B82F6` | Read-only + web |

**When to use**: Designing new systems, choosing between approaches, refactoring strategy, pattern selection.

---

### 2. Planner — Execution Strategy & Sequencing

Takes a design and sequences the work. Complements architect (what → how → when).

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `planner` | DeepSeek V4 Pro Max | 25 | `#C4B5FD` | Read-only |

**When to use**: Task breakdown, dependency mapping, milestone planning, effort estimation.

**How it differs from architect**: Architect says "build a bridge here using a suspension design." Planner says "Phase 1: survey site. Phase 2: pour foundations. Phase 3: ..."

---

### 3. Code Reviewer — Bug Detection & Code Quality

Finds bugs, logic errors, style issues, and security concerns in code.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `reviewer` | DeepSeek V4 Pro Max | 30 | `#FCA5A5` | Read-only + bash |

**When to use**: Pre-merge review, PR feedback, catching edge cases and logic flaws.

---

### 4. Debugger — Runtime Failure Investigation

Chases bugs that are happening right now — error messages, stack traces, production issues.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `debugger` | DeepSeek V4 Pro Max | 35 | `#FB7185` | Full (edit, bash) |

**When to use**: Something broke. Error logs, crash reports, mysterious behavior.

**How it differs from reviewer**: Reviewer catches bugs before they ship. Debugger chases bugs that are already happening.

---

### 5. Security Auditor — Vulnerability Assessment

Finds security holes — injections, exposed secrets, unsafe configs, supply chain risks.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `security` | DeepSeek V4 Pro Max | 30 | `#DC2626` | Read-only + bash + web |

**When to use**: Security review before deployment, scanning for exposed secrets, hardening.

**How it differs from reviewer**: Reviewer cares about correctness. Security auditor only cares about exploits.

---

### 6. Editor — Content Quality & Writing

Improves writing — structure, clarity, tone, grammar.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `editor` | DeepSeek V4 Pro Max | 25 | `#FDE68A` | Read + edit |

**When to use**: Blog posts, documentation, transcripts, any written content that needs polish.

---

### 7. Researcher — Information Gathering & Synthesis

Finds, verifies, and synthesizes information from multiple sources.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `researcher` | DeepSeek V4 Pro Max | 40 | `#6EE7B7` | Full |

**When to use**: "Research how X works," "compare Y and Z," "find best practices for W."

---

### 8. Quote Auditor — Quotation Integrity & Attribution

Verifies that quotes match their sources exactly. Detects paraphrasing disguised as quotation.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `quote-auditor` | DeepSeek V4 Pro Max | 25 | `#FDBA74` | Read-only + bash |

**When to use**: Verifying transcript quotes, fact-checking article claims, legal/journalistic accuracy.

---

### 9. Worker — General Purpose

The go-to for any task that doesn't fit a specialized role. Full access to edit files and run commands.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `worker` | DeepSeek V4 Pro Max | 40 | `#A5B4FC` | Full |

**When to use**: Implementation, feature building, test writing, migrations, any general task.

---

## Bonus: Alternative Model Workers

These use different model providers for when you want a specific model's strengths:

| Agent | Model | Setup | Permissions |
|-------|-------|-------|------------|
| `grok-worker` | Grok 4.3 (xAI) | Add xAI provider + API key to opencode.json | Full |

See `agents/grok-worker.md` for setup instructions.

---

## Quick Reference — When to Use What

| You want to... | Use |
|---------------|-----|
| Design a new system / choose approach | `architect` |
| Plan how to build something | `planner` |
| Review code before merging | `reviewer` |
| Figure out why something broke | `debugger` |
| Check code for security holes | `security` |
| Improve writing quality | `editor` |
| Research a topic | `researcher` |
| Verify quotes match sources | `quote-auditor` |
| Build a feature / fix a bug | `worker` |
| Any task with Grok's model | `grok-worker` |

---

## How to Invoke a Subagent

Subagents are invoked by the Supervisor agent using the Task tool. You (the user) trigger them by asking the Supervisor to delegate.

Say things like:

- "Use the architect to design a plan for..."
- "Have the reviewer look at this PR"
- "Ask the researcher to find best practices for X"
- "Send this to the worker for implementation"

The Supervisor spawns the subagent with your request. The subagent works independently (in its own context window, with its own model), then returns a final message. The Supervisor presents the result.

---

## Mode Switching (Slash Commands)

These slash commands change the main agent's behavior for a single request. Most reinforce the Karpathy principles; `/architect` sometimes overrides them for fresh first-principles design.

| Command | What it does |
|---------|-------------|
| `/architect` | Design forces, tradeoffs, refactor scope, cross-cutting concerns, API shape |
| `/plan` | Step-by-step planning with options, risks, and accessibility notes |
| `/debug` | Bug investigation — form hypotheses, test systematically |
| `/test` | Testing-first — write tests, then make them pass |
| `/review` | Senior code review — balanced, severity-tiered feedback |
| `/explain` | Teaching mode — simple, beginner-friendly explanations |
| `/refine` | Surgical + gentle improvements — precise, small cleanups |
| `/security` | Security audit across 7 categories — thinks like an attacker |
| `/verifyquotes` `/auditquotes` | Line-by-line, character-by-character quotation audit — detects paraphrasing |

---

## Key Design Decisions

- **Most specialized subagents are read-only** (`edit: deny`) — they analyze and recommend, never change code. **Exceptions:** `debugger` and `researcher` have full edit and bash access, `reviewer`, `security`, and `quote-auditor` have `bash: allow` for running diagnostic commands. Worker has full access. Tiers differ only in model, never in permissions.
- **Architect vs Planner**: Architect invents new approaches. Planner sequences existing designs into action steps.
- **Reviewer vs Debugger**: Reviewer finds bugs in code you're about to merge. Debugger investigates bugs that are already happening.
- **Reviewer vs Security**: Reviewer cares about correctness. Security only cares about exploits.
- **Editor vs Quote Auditor**: Editor improves writing quality. Quote Auditor verifies factual/attribution accuracy.
