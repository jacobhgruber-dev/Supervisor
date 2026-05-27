# OpenCode Modes — Behavioral Mode Switching

9 keyword-triggered modes that change how the AI agent thinks and operates. Say `architect`, `debug`, `review`, or any trigger word — the agent shifts behavior for that single request, then returns to normal.

## What You Get

| Mode | Trigger | What It Does |
|------|---------|--------------|
| Architect | `architect` `/architect` | Full creative redesign — ignores existing code, thinks from scratch |
| Refine | `refine` `/refine` | Surgical improvements — small, safe cleanups only |
| Plan | `plan` `/plan` | Step-by-step planning with options, risks, and tradeoffs |
| Debug | `debug` `/debug` | Root-cause investigation — questions before fixes |
| Test | `test` `/test` | Testing-first — write tests before implementation |
| Explain | `explain` `/explain` | Teaching mode — simple, beginner-friendly explanations |
| Review | `review` `/review` | Senior code review — balanced, experienced feedback |
| Security | `security` `/security` | Security audit — vulnerabilities, data safety, input validation |
| Verify Quotes | `verifyquotes` `/verifyquotes` `auditquotes` `/auditquotes` | Quotation audit — line-by-line verification against sources |

## Setup

Copy the mode rules into your opencode config:

```bash
cp AGENTS.md ~/.config/opencode/
```

Or merge into an existing `AGENTS.md`. The modes are always active once the file is present.

## How It Works

Include any trigger word anywhere in your message. The agent adopts that mode for one response only. After responding, it returns to normal behavior. Modes don't stack — the last trigger word wins.

```
# Before a big feature:
architect We need a notification system supporting email, push, and in-app. Design it.

# Chasing a bug:
debug Users report the checkout button works in Chrome but not Safari.

# Polishing docs:
refine The error handling section in the README could be clearer.

# Before merging:
review Look at src/services/payment.ts and any issues before I open the PR.
```

## Individual Modes

Each mode also lives in `modes/` as a standalone file. Copy individual modes into your own system prompt or AGENTS.md if you only want a few.
