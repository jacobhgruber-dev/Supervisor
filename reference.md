# Full Reference — Agents, Subagents, Modes & Commands

A comprehensive catalog of everything available across the base setup, 3-tier upgrade, and all addons. Not everything here applies to every setup — skim the headings and read what's relevant to what you've installed. As you add more pieces (modes, Claude tiers), more sections become relevant.

**Tip:** Keep this somewhere handy: `cp reference.md ~/Desktop/opencode-reference.md`

---

## The Supervisor System

The Supervisor is a primary agent that orchestrates work through specialized subagents. It plans, delegates, reviews, fixes, and commits. You talk to the Supervisor. It manages the team.

| Component | Model | Purpose |
|-----------|-------|---------|
| **Supervisor** (primary) | DeepSeek V4 Pro Max | Orchestration — plans, delegates, reviews, commits |
| **27 subagents** (3 tiers) | DeepSeek V4 Pro Max / Claude Sonnet 4.6 Max / Claude Opus 4.8 Max | Implementation, research, debugging, design, review, security, planning, editing, quote auditing — 9 roles at each tier |
| **Observer** (built in) | Claude Sonnet 4.6 | Reads pasted screenshots / UI states / error images and returns structured text |
| **9 behavioral modes** (addon) | N/A — changes agent behavior, not model | Trigger words that shift how the agent thinks for one request |

---

## Subagent Tiers

The Supervisor ships with 27 agents across 3 tiers — 9 roles at each tier. The junior tier (DeepSeek V4 Pro Max) is the default workhorse. Mid (Claude Sonnet) and senior (Claude Opus) agents are also present in the repo and activate as soon as you configure an Anthropic API key.

| Subagent | Use For | Steps | Permissions |
|----------|---------|-------|-------------|
| `worker` | Implementation — features, tests, migrations, frontend | 40 | Full (edit, bash, web, playwright) |
| `researcher` | Web research, multi-source synthesis, API/library docs | 40 | Full |
| `debugger` | Runtime errors, test failures, root cause analysis | 35 | Full (edit, bash, web, playwright) |
| `architect` | Design questions, refactoring plans, tradeoff analysis | 25 | Edit + web + playwright (no bash) |
| `reviewer` | Code review — quality, bugs, style, pre-commit pass | 30 | Read-only + bash |
| `security` | Vulnerability scanning — secrets, injections, unsafe patterns | 30 | Read-only + bash + web + playwright |
| `planner` | Task breakdown, sequencing, milestone planning | 25 | Read-only |
| `editor` | Grammar, spelling, punctuation, readability | 25 | Read + edit |
| `quote-auditor` | Quotation verification against sources | 25 | Read-only + bash |

### When to Use

| You want to... | Deploy |
|---------------|--------|
| Build a feature / fix a bug | `worker` |
| Research a topic or library | `researcher` |
| Investigate a crash or error | `debugger` |
| Design a new system or choose approach | `architect` |
| Review code before merging | `reviewer` |
| Check code for security holes | `security` |
| Break down a large task into steps | `planner` |
| Polish documentation or prose | `editor` |
| Verify quotes match their sources | `quote-auditor` |

---

## Tier Breakdown

The 3-tier system is fully configured in the repo. The naming convention:

| Tier | Model | Naming | Default Behavior |
|------|-------|--------|-----------------|
| Junior | DeepSeek V4 Pro Max | `junior-worker`, etc. | Default — automatic spawning |
| Mid | Claude Sonnet 4.6 Max | `worker`, etc. (bare name) | Explicitly invoked |
| Senior | Claude Opus 4.8 Max | `senior-worker`, etc. | Highest stakes only |

This gives you 27 subagent files across 9 roles × 3 tiers. See `tier-system-reference.md` for the complete spec table and agent specifications.

### Quick Cost Guide

| Tier | Model | Relative Cost | Best For |
|------|-------|--------------|----------|
| Junior | DeepSeek V4 Pro Max | $ | 80% of all tasks |
| Mid | Claude Sonnet 4.6 Max | $$ | Complex reasoning, deeper reviews |
| Senior | Claude Opus 4.8 Max | $$$$ | Production-critical, highest stakes |

---

## Behavioral Modes (Addon)

Slash commands that change how the agent thinks for a single request. Modes don't change the model — they change the behavior. Works with any agent (supervisor or subagent). Most reinforce the Karpathy principles; `/architect` sometimes overrides them for fresh first-principles design.

| Mode | Trigger | What It Does |
|------|---------|--------------|
| **Architect** | `/architect` | Design forces, tradeoffs, refactor scope, cross-cutting concerns, API shape. Fresh-from-scratch when invited; otherwise ground in codebase and design incrementally. |
| **Refine** | `/refine` | Surgical + gentle improvements. Precise, small cleanups — nothing speculative. |
| **Plan** | `/plan` | Step-by-step planning. Options, risks, dependencies, and accessibility notes before code. |
| **Debug** | `/debug` | Bug investigation. Form hypotheses, test systematically, find root cause. |
| **Test** | `/test` | Testing-first. Write tests, then make them pass. |
| **Explain** | `/explain` | Teaching mode. Simple, beginner-friendly — assumes no prior context. |
| **Review** | `/review` | Senior code review. Balanced, severity-tiered feedback. |
| **Security** | `/security` | Security audit across 7 categories. Thinks like an attacker. |
| **Verify Quotes** | `/verifyquotes` `/auditquotes` | Quotation audit. Line-by-line, character-by-character verification against sources. Detects paraphrasing, flags every uncertainty. |

### How Modes Work

Include any slash command anywhere in your message. The agent shifts behavior for that one response, then returns to normal. Modes don't stack.

```
# Before a big feature:
/architect Design a notification system supporting email, push, and in-app.

# Chasing a bug:
/debug Checkout button works in Chrome but not Safari. Investigate.

# Before merging:
/review Look at src/services/payment.ts before I open the PR.

# Learning a codebase:
/explain How does the auth middleware work in this Express app?
```

Setup: copy `addons/open-code-modes/AGENTS.md` to `~/.config/opencode/AGENTS.md`.

---

## Custom Commands (Optional)

OpenCode lets you register your own slash-commands under the `"command"` key in `opencode.json`. The base repo ships **without** any — they're personal to each user's workflow — but they're easy to add. A command is just a name plus a `template` (the instructions the agent follows when you invoke it).

Examples of what people build: `/transcribe` to run an audio-to-text pipeline, `/deploy` to push a release, `/changelog` to summarize recent commits. Whatever you do often, you can wrap in a command.

To create one, add an entry to your `opencode.json`:

```json
"command": {
  "my-command": {
    "description": "What this command does",
    "template": "Detailed instructions the agent follows when the command is invoked."
  }
}
```

---

## System Architecture

```
You (the User)
      |
      v
Supervisor Agent (primary, DeepSeek V4 Pro Max)
      |
      +---> worker / junior-worker / senior-worker     (implementation)
      +---> architect / junior-architect / senior-architect  (design)
      +---> planner / junior-planner / senior-planner  (sequencing)
      +---> reviewer / junior-reviewer / senior-reviewer  (code review)
      +---> debugger / junior-debugger / senior-debugger  (runtime errors)
      +---> security / junior-security / senior-security  (vulnerabilities)
      +---> researcher / junior-researcher / senior-researcher  (information)
      +---> editor / junior-editor / senior-editor  (proofreading, read + edit)
      +---> quote-auditor / junior-quote-auditor / senior-quote-auditor  (quotes)
      |
      +---> observer           (visual analysis, Claude Sonnet 4.6)

(Optional addon: grok-worker — alternative model, Grok 4.3 via xAI.)

Behavioral Modes (overlay on any agent):
  /architect | /refine | /plan | /debug | /test | /explain | /review | /security | /verifyquotes | /auditquotes
```

---

## Quick Lookup — Match Task to Agent

| Task | Agent |
|------|-------|
| "Build a REST API endpoint" | `worker` |
| "Design a new microservice architecture" | `architect` |
| "Plan the phases for this project" | `planner` |
| "Review this PR before I merge" | `reviewer` |
| "The login is broken in production" | `debugger` |
| "Audit the payment code for vulnerabilities" | `security` |
| "Research best practices for React state management" | `researcher` |
| "Proofread this blog post" | `editor` |
| "Check that all quotes in this article are verbatim" | `quote-auditor` |
| "Read the screenshot I just pasted" | `observer` |
| "Any task — I want Grok's model" | `grok-worker` *(optional addon)* |
