# OpenCode Modes — Behavioral Mode Switching

9 slash-command-triggered modes that change how the AI agent thinks and operates. Use `/architect`, `/debug`, `/review`, or any slash command — the agent shifts behavior for that single request, then returns to normal.

## What You Get

| Mode | Trigger | What It Does |
|------|---------|--------------|
| Architect | `/architect` | Design forces, tradeoffs, refactor scope, cross-cutting concerns, API shape. Fresh-from-scratch when invited; otherwise ground in the codebase and design incrementally. |
| Refine | `/refine` | Surgical + gentle improvements. Precise, small cleanups — nothing speculative. |
| Plan | `/plan` | Step-by-step planning. Options, risks, dependencies, and accessibility notes laid out before code. |
| Debug | `/debug` | Bug investigation. Form hypotheses, test systematically, find root cause before fixing. |
| Test | `/test` | Testing-first mode. Write tests to define correct behavior, then make them pass. |
| Explain | `/explain` | Teaching mode. Simple, beginner-friendly explanations — assumes no prior context. |
| Review | `/review` | Senior code review. Balanced, severity-tiered feedback like an experienced developer. |
| Security | `/security` | Security audit across 7 categories. Thinks like an attacker — finds vulnerabilities, not bugs. |
| Verify Quotes | `/verifyquotes` `/auditquotes` | Quotation audit. Line-by-line, character-by-character verification against sources. Detects paraphrasing, flags every uncertainty. |

## Setup

**Nothing to copy.** Mode switching is built into the Supervisor system. The slash commands are defined in `agent/supervisor.md`, which the Supervisor agent loads automatically. The root `AGENTS.md` provides behavioral guidelines for all agents. This folder is reference documentation only — the individual mode descriptions in `modes/` explain what each slash command does.

## How It Works

Include any slash command anywhere in your message. The agent adopts that mode for one response only. After responding, it returns to normal behavior. Modes don't stack.

```
# Before a big feature:
/architect We need a notification system supporting email, push, and in-app. Design it.

# Chasing a bug:
/debug Users report the checkout button works in Chrome but not Safari.

# Polishing docs:
/refine The error handling section in the README could be clearer.

# Before merging:
/review Look at src/services/payment.ts and any issues before I open the PR.
```

## Individual Modes

Each mode also lives in `modes/` as a standalone file with detailed explanations — why the behavior exists, what it covers, when to use it, and what it changes. Copy individual modes into your own system prompt or AGENTS.md if you only want a few.
