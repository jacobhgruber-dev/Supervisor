# Full Reference — Agents, Subagents, Modes & Commands

A comprehensive catalog of everything available across the base setup, 3-tier upgrade, and all addons. Not everything here applies to every setup — skim the headings and read what's relevant to what you've installed. As you add more pieces (modes, Ollama, Claude tiers), more sections become relevant.

**Tip:** Keep this somewhere handy: `cp reference.md ~/Desktop/opencode-reference.md`

---

## The Supervisor System

The Supervisor is a primary agent that orchestrates work through specialized subagents. It plans, delegates, reviews, fixes, and commits. You talk to the Supervisor. It manages the team.

| Component | Model | Purpose |
|-----------|-------|---------|
| **Supervisor** (primary) | DeepSeek V4 Pro Max | Orchestration — plans, delegates, reviews, commits |
| **9 subagents** (base) | DeepSeek V4 Pro Max | Implementation, research, debugging, design, review, security, planning, editing, quote auditing |
| **2 local subagents** (addon) | Qwen3 Coder 14B / Gemma 4 (e4b) via Ollama | On-device coding and reasoning, private, zero-cost |
| **9 behavioral modes** (addon) | N/A — changes agent behavior, not model | Trigger words that shift how the agent thinks for one request |

---

## Subagents — Base Tier (DeepSeek V4 Pro Max)

All nine run on DeepSeek. One API key covers everything.

| Subagent | Use For | Steps | Permissions |
|----------|---------|-------|-------------|
| `worker` | Implementation — features, tests, migrations, frontend | 40 | Full (edit, bash, web) |
| `researcher` | Web research, multi-source synthesis, API/library docs | 40 | Full |
| `debugger` | Runtime errors, test failures, root cause analysis | 35 | Full (edit, bash) |
| `architect` | Design questions, refactoring plans, tradeoff analysis | 25 | Edit + web (no bash) |
| `reviewer` | Code review — quality, bugs, style, pre-commit pass | 30 | Read-only + bash |
| `security` | Vulnerability scanning — secrets, injections, unsafe patterns | 30 | Read-only + bash + web |
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

## Upgrading to 3-Tier (Claude Sonnet & Opus)

If you add an Anthropic API key, the naming convention becomes:

| Tier | Model | Naming | Default Behavior |
|------|-------|--------|-----------------|
| Junior | DeepSeek V4 Pro Max | `junior-worker`, etc. | Default — automatic spawning |
| Mid | Claude Sonnet 4.6 Max | `worker`, etc. (bare name) | Explicitly invoked |
| Senior | Claude Opus 4.8 Max | `senior-worker`, etc. | Highest stakes only |

This gives you 27 subagent files across 9 roles × 3 tiers. See `agents/UPGRADING.md` in the repo for the complete spec table and setup instructions.

### Quick Cost Guide

| Tier | Model | Relative Cost | Best For |
|------|-------|--------------|----------|
| Junior | DeepSeek V4 Pro Max | $ | 80% of all tasks |
| Mid | Claude Sonnet 4.6 Max | $$ | Complex reasoning, deeper reviews |
| Senior | Claude Opus 4.8 Max | $$$$ | Production-critical, highest stakes |

---

## Local Subagents — Ollama (Addon)

Run entirely on-device. No API calls, no cost, full privacy. Requires Ollama installed.

| Subagent | Model | Use For | Steps | Permissions |
|----------|-------|---------|-------|-------------|
| `local-coder` | Qwen3 Coder 14B | Coding tasks — write, edit, debug, refactor | 16 | Full |
| `local-reasoner` | Gemma 4 (e4b) | Analysis, planning, evaluation | 14 | Read-only + web |

### When to Use Local Agents

- Privacy-sensitive code or documents
- Straightforward tasks where you don't want to burn API credits
- Offline work (once models are downloaded)
- Quick boilerplate, formatting, or small fixes

### Recommended Ollama Models

| Model | Quality | Speed | RAM Needed | Best For |
|-------|---------|-------|-----------|----------|
| `freehuntx/qwen3-coder:14b` | Good | Fast | 10 GB | Everyday coding (start here) |
| `qwen3.6:27b` | High | Moderate | 22 GB | Complex reasoning, analysis |
| `qwen3.6:27b-coding-nvfp4` | High | Moderate | 18 GB | Coding specialist (27B) |
| `gemma4:e4b` | Good | Fast | 10 GB | Reasoning, planning |
| `batiai/qwen3.6-27b:q4` | Good | Fast | 18 GB | Smaller quant of 27B |
| `batiai/qwen3.6-27b:q3` | Decent | Fast | 14 GB | Smallest quant of 27B |

Install: `brew install ollama` then `ollama pull <model-name>`

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

## Custom Commands (Jacob's Setup)

These are registered in `opencode.json` under the `"command"` key. They're workflow-specific and not included in the base repo, but you can create your own using the same pattern.

| Command | Purpose |
|---------|---------|
| `/transcribe` | Transcribe audio with whisper (fast) or faster-whisper (high quality) |
| `/anna` | Search and download books from Anna's Archive |
| `/audio` | Search and download audiobooks from AudiobookBay |

To create a custom command, add an entry to your `opencode.json`:

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
      +---> local-coder        (on-device coding, Ollama)
      +---> local-reasoner     (on-device reasoning, Ollama)
      |
      +---> grok-worker        (alternative model, Grok 4.3 via xAI)

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
| "Write a simple utility — I want privacy" | `local-coder` |
| "Analyze this proprietary algorithm — don't send to cloud" | `local-reasoner` |
| "Any task — I want Grok's model" | `grok-worker` |
