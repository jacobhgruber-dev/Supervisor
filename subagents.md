<!-- Not an agent file — do not copy to ~/.config/opencode/agents/ -->
# Subagents — Quick Reference

41 agent files across 9 roles at 4 tiers  •  junior: DeepSeek V4 Pro  •  mid: Claude Sonnet 4.6  •  senior: Claude Opus 4.8  •  mule: various models (see tier-system-reference.md)

For full tier specifications, see [tier-system-reference.md](tier-system-reference.md).
For the full system reference including modes, local agents, and commands, see [reference.md](reference.md).

---

## How the Supervisor Works

The Supervisor is a primary agent in opencode that orchestrates work through specialized subagents. It plans, delegates, reviews outputs, fixes issues, and commits — all while keeping its own context window clean. You (the user) interact with the Supervisor; it manages the subagents behind the scenes.

Key principle: **Delegate everything.** The Supervisor reads docs for orientation, then spawns subagents for all substantive work. It only self-executes mechanical operations like commits and pushes.

---

## Subagents — 9 Roles

### How tiers work

This repo ships with all 4 tiers of agents already configured — 41 agent files across 9 roles. The junior tier (`junior-*`) runs on DeepSeek V4 Pro and is the default workhorse. The mid tier (bare names like `worker`, `architect`) and senior tier (`senior-*`) run on Claude Sonnet and Opus respectively. These files are already present in the repo — they activate as soon as you connect an Anthropic key with `opencode auth login`. See `tier-system-reference.md` for the complete spec table with exact models, step counts, and permissions per role per tier.

---

### 1. Architect — System Design & Novel Approaches

Designs new ways to do things. Greenfield thinking, tradeoff analysis.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `architect` | Claude Sonnet 5 | 25 | `#3B82F6` | Edit + web + playwright (no bash) |

**When to use**: Designing new systems, choosing between approaches, refactoring strategy, pattern selection.

---

### 2. Planner — Execution Strategy & Sequencing

Takes a design and sequences the work. Complements architect (what → how → when). Includes quality tooling steps in estimates (ruff, mypy, shellcheck, hypothesis, radon).

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `planner` | Claude Sonnet 5 | 25 | `#C4B5FD` | Read-only |

**When to use**: Task breakdown, dependency mapping, milestone planning, effort estimation.

**How it differs from architect**: Architect says "build a bridge here using a suspension design." Planner says "Phase 1: survey site. Phase 2: pour foundations. Phase 3: ..."

---

### 3. Code Reviewer — Bug Detection & Code Quality

Finds bugs, logic errors, style issues, and security concerns in code. Runs automated analysis: ruff, mypy, shellcheck, radon, lizard, trivy. Suggests hypothesis and coverage for test quality. Knows when cosmic-ray is warranted.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `reviewer` | Claude Sonnet 5 | 30 | `#FCA5A5` | Read-only + bash |

**When to use**: Pre-merge review, PR feedback, catching edge cases and logic flaws.

---

### 4. Debugger — Runtime Failure Investigation

Chases bugs that are happening right now — error messages, stack traces, production issues. Uses diagnostic tools: mypy for type errors, py-spy/scalene for performance, trivy for dependency CVEs, shellcheck for bash bugs, rg for fast code search.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `debugger` | Claude Sonnet 5 | 35 | `#FB7185` | Full (edit, bash, web, playwright) |

**When to use**: Something broke. Error logs, crash reports, mysterious behavior.

**How it differs from reviewer**: Reviewer catches bugs before they ship. Debugger chases bugs that are already happening.

---

### 5. Security Auditor — Vulnerability Assessment

Finds security holes — injections, exposed secrets, unsafe configs, supply chain risks.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `security` | Claude Sonnet 5 | 30 | `#DC2626` | Read-only + bash + web + playwright |

**When to use**: Security review before deployment, scanning for exposed secrets, hardening.

**How it differs from reviewer**: Reviewer cares about correctness. Security auditor only cares about exploits.

---

### 6. Editor — Content Quality & Writing

Improves writing — structure, clarity, tone, grammar.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `editor` | Claude Sonnet 5 | 25 | `#FDE68A` | Read + edit |

**When to use**: Blog posts, documentation, transcripts, any written content that needs polish.

---

### 7. Researcher — Information Gathering & Synthesis

Finds, verifies, and synthesizes information from multiple sources.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `researcher` | Claude Sonnet 5 | 40 | `#6EE7B7` | Full |

**When to use**: "Research how X works," "compare Y and Z," "find best practices for W."

---

### 8. Quote Auditor — Quotation Integrity & Attribution

Verifies that quotes match their sources exactly. Detects paraphrasing disguised as quotation.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `quote-auditor` | Claude Sonnet 5 | 25 | `#FDBA74` | Read-only |

**When to use**: Verifying transcript quotes, fact-checking article claims, legal/journalistic accuracy.

---

### 9. Worker — General Purpose

The go-to for any task that doesn't fit a specialized role. Full access to edit files and run commands. Runs pre-completion checks: ruff, mypy, shellcheck, radon, coverage, trivy. Knows document parsing (pymupdf, python-docx, beautifulsoup4). Uses rg for search and gh for GitHub operations.

| Agent | Model | Steps | Color | Permissions |
|-------|-------|-------|-------|-------------|
| `worker` | Claude Sonnet 5 | 40 | `#A5B4FC` | Full |

**When to use**: Implementation, feature building, test writing, migrations, any general task.

---

## Bonus: Alternative Model Worker (Optional Addon)

When you want a specific model's strengths, the optional `grok-worker` addon adds a full-access worker on xAI's Grok 4.3. It lives outside the core agent set so it never auto-loads.

| Agent | Model | Setup | Permissions |
|-------|-------|-------|------------|
| `grok-worker` | Grok 4.3 (xAI) | Add an xAI key through Desktop Settings → Providers, then copy one file. | Full |

See [`addons/grok-worker/README.md`](addons/grok-worker/README.md) for setup. No auth plugin required.

---

## Mule Tier — Leaf Workers (Built In)

The repo also ships with **12 mule-tier agents** — safe-to-spawn leaf workers that can never spawn further subagents. This eliminates recursion risk: any agent that spawns a mule is guaranteed the work terminates there.

Mules are subagent infrastructure — architects, workers, debuggers, and reviewers spawn them internally for bounded sub-tasks. The supervisor never spawns mules directly.

| Mule | Model | Best for |
|---|---|---|
| `worker-mule` | DeepSeek V4 Pro | Implementation, file edits, bash commands |
| `architect-mule` | DeepSeek V4 Pro | Design sub-problems, refactor scoping |
| `researcher-mule` | DeepSeek V4 Pro | Web research, documentation lookup |
| `debugger-mule` | DeepSeek V4 Pro | Hypothesis testing, diagnostics |
| `reviewer-mule` | DeepSeek V4 Pro | Diff-level code review |
| `security-mule` | DeepSeek V4 Pro | Vulnerability scanning |
| `planner-mule` | DeepSeek V4 Pro | Task breakdown, sequencing |
| `editor-mule` | DeepSeek V4 Pro | Documentation polish |
| `quote-auditor-mule` | DeepSeek V4 Pro | Source verification |
| `gemini-mule` | Gemini 2.5 Flash | Long-context, multimodal, web research |
| `grok-mule` | Grok 4.3 | Coding, reasoning, creative |
| `claude-mule` | Claude Sonnet 4.6 | Nuanced reasoning, careful analysis, code review |

See [tier-system-reference.md](tier-system-reference.md) for full mule tier specifications.

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
| Any task with Grok's model | `grok-worker` *(optional addon)* |

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

- **Edit permissions by role:** Worker, researcher, debugger, architect, and editor have `edit: allow` — they can create or modify code files. Planner, reviewer, security, and quote auditor are read-only (`edit: deny`) — they analyze and recommend. For bash: worker, researcher, debugger, reviewer, and security have `bash: allow`; architect, planner, editor, and quote auditor have `bash: deny`. For web access (webfetch, websearch, playwright): worker, researcher, debugger, architect, and security have full web access; reviewer, editor, planner, and quote auditor do not. Tiers differ only in model, never in permissions.
- **Architect vs Planner**: Architect invents new approaches. Planner sequences existing designs into action steps.
- **Reviewer vs Debugger**: Reviewer finds bugs in code you're about to merge. Debugger investigates bugs that are already happening.
- **Reviewer vs Security**: Reviewer cares about correctness. Security only cares about exploits.
- **Editor vs Quote Auditor**: Editor improves writing quality. Quote Auditor verifies factual/attribution accuracy.
