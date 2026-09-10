<!-- Not an agent file — do not copy to ~/.config/opencode/agents/ -->
# Tier System Reference

The Supervisor ships with a complete 3-tier escalation system (plus a built-in mule tier — see [Mule Tier](#mule-tier-built-in) below). All 9 roles are available at every escalation tier out of the box.

For the quick-reference guide to the 9 base subagents, see [subagents.md](subagents.md).
For the complete catalog including modes, commands, and local agents, see [reference.md](reference.md).

| Tier | Model | Role | Naming Convention |
|------|-------|------|-------------------|
| **Junior** | DeepSeek Flash | Default workhorse, most tasks | `junior-worker`, `junior-architect`, etc. |
| **Mid** | Claude Sonnet 5 | Complex reasoning, deeper reviews | `worker`, `architect`, etc. (no prefix) |
| **Senior** | Claude Opus 5 | Highest stakes, production-critical | `senior-worker`, `senior-architect`, etc. |

## Why 3 Tiers?

The naming convention creates a natural escalation path:

1. **Junior (DeepSeek)** — the default. Spawned automatically for most work. Cheap, capable, handles 80%+ of tasks.
2. **Mid (Sonnet)** — explicitly invoked for tasks needing deeper reasoning: complex PR reviews, tricky refactors, nuanced security analysis.
3. **Senior (Opus)** — reserved for when it really matters: deployment-critical code, distributed system debugging, architecture for new services.

The Supervisor's default policy is to spawn junior-tier agents automatically and escalate only when the user asks or the task warrants it. This keeps costs predictable while still having the big guns available.

## Agent Specifications by Tier

These are the frontmatter specs for each agent. The prompt content (the body of each `.md` file) is the same across tiers — only the model and description change.

### Mid-Tier Agents (Claude Sonnet)

#### `worker.md` (Sonnet)

```
---
description: General-purpose subagent powered by Claude Sonnet 5. Mid-tier worker for tasks needing deeper reasoning than DeepSeek. Full edit and bash access.
mode: subagent
model: anthropic/claude-sonnet-5
variant: max
color: "#818CF8"
permission:
  edit: allow
  bash: allow
  webfetch: allow
  websearch: allow
  playwright_*: allow
---
```

#### `architect.md` (Sonnet)

```
---
description: Software architect for design decisions, refactoring plans, and system structure. Powered by Claude Sonnet 5.
mode: subagent
model: anthropic/claude-sonnet-5
variant: max
color: "#7B61FF"
permission:
  edit: allow
  bash: deny
  webfetch: allow
  websearch: allow
  playwright_*: allow
---
```

#### `planner.md` (Sonnet)

```
---
description: Planner for breaking down tasks into ordered steps, identifying dependencies, and estimating effort. Powered by Claude Sonnet 5.
mode: subagent
model: anthropic/claude-sonnet-5
variant: max
color: "#A78BFA"
permission:
  edit: deny
  bash: deny
---
```

#### `reviewer.md` (Sonnet)

```
---
description: Code reviewer for bugs, logic errors, and code quality. Powered by Claude Sonnet 5.
mode: subagent
model: anthropic/claude-sonnet-5
variant: max
color: "#F87171"
permission:
  edit: deny
  bash: allow
---
```

#### `debugger.md` (Sonnet)

```
---
description: Debugger for runtime errors, stack traces, and unexpected behavior. Powered by Claude Sonnet 5.
mode: subagent
model: anthropic/claude-sonnet-5
variant: max
color: "#EF4444"
permission:
  edit: allow
  bash: allow
  webfetch: allow
  websearch: allow
  playwright_*: allow
---
```

#### `security.md` (Sonnet)

```
---
description: Security auditor for vulnerability scanning — secrets, injections, unsafe dependencies, and common attack vectors. Powered by Claude Sonnet 5.
mode: subagent
model: anthropic/claude-sonnet-5
variant: max
color: "#B91C1C"
permission:
  edit: deny
  bash: allow
  webfetch: allow
  websearch: allow
  playwright_*: allow
---
```

#### `editor.md` (Sonnet)

```
---
description: Content editor for clarity, flow, and readability. Powered by Claude Sonnet 5.
mode: subagent
model: anthropic/claude-sonnet-5
variant: max
color: "#FDE68A"
permission:
  edit: allow
  bash: deny
---
```

#### `researcher.md` (Sonnet)

```
---
description: Researcher for topic exploration, source gathering, and structured answers. Powered by Claude Sonnet 5.
mode: subagent
model: anthropic/claude-sonnet-5
variant: max
color: "#34D399"
permission:
  edit: allow
  bash: allow
  webfetch: allow
  websearch: allow
  playwright_*: allow
---
```

#### `quote-auditor.md` (Sonnet)

```
---
description: Quote auditor for verifying quotations against their sources. Powered by Claude Sonnet 5.
mode: subagent
model: anthropic/claude-sonnet-5
variant: max
color: "#FB923C"
permission:
  edit: deny
  bash: deny
---
```

### Senior-Tier Agents (Claude Opus)

#### `senior-worker.md` (Opus)

```
---
description: Senior general-purpose subagent powered by Claude Opus 5. The most capable model available — use for the hardest problems.
mode: subagent
model: anthropic/claude-opus-5
variant: max
color: "#6366F1"
permission:
  edit: allow
  bash: allow
  webfetch: allow
  websearch: allow
  playwright_*: allow
---
```

#### `senior-architect.md` (Opus)

```
---
description: Senior-level system architect. Deep architectural reasoning, complex tradeoff analysis, and high-stakes design decisions. Use ONLY for the hardest problems.
mode: subagent
model: anthropic/claude-opus-5
variant: max
color: "#B026FF"
permission:
  edit: allow
  bash: deny
  webfetch: allow
  websearch: allow
---
```

#### `senior-planner.md` (Opus)

```
---
description: Senior planner for complex multi-phase execution strategy, dependency mapping, risk assessment, and milestone planning.
mode: subagent
model: anthropic/claude-opus-5
variant: max
color: "#8B5CF6"
permission:
  edit: deny
  bash: deny
---
```

#### `senior-reviewer.md` (Opus)

```
---
description: Senior code reviewer. Deep bug detection, architectural misuse, and subtle logic flaws. Use for critical code before deployment.
mode: subagent
model: anthropic/claude-opus-5
variant: max
color: "#FF4444"
permission:
  edit: deny
  bash: allow
---
```

#### `senior-debugger.md` (Opus)

```
---
description: Senior debugger for the hardest bugs — race conditions, memory leaks, distributed system failures, heisenbugs.
mode: subagent
model: anthropic/claude-opus-5
variant: max
color: "#DC2626"
permission:
  edit: allow
  bash: allow
  webfetch: allow
  websearch: allow
  playwright_*: allow
---
```

#### `senior-security.md` (Opus)

```
---
description: Senior security auditor for comprehensive vulnerability assessment — injection attacks, auth flaws, secret exposure, supply chain risks, and zero-day patterns.
mode: subagent
model: anthropic/claude-opus-5
variant: max
color: "#991B1B"
permission:
  edit: deny
  bash: allow
  webfetch: allow
  websearch: allow
  playwright_*: allow
---
```

#### `senior-editor.md` (Opus)

```
---
description: Senior editor for content strategy, structural revision, and high-stakes writing. Final polish before publication.
mode: subagent
model: anthropic/claude-opus-5
variant: max
color: "#EAB308"
permission:
  edit: allow
  bash: deny
---
```

#### `senior-researcher.md` (Opus)

```
---
description: Senior researcher for deep multi-source investigation, complex topic synthesis, and strategic recommendations.
mode: subagent
model: anthropic/claude-opus-5
variant: max
color: "#10B981"
permission:
  edit: allow
  bash: allow
  webfetch: allow
  websearch: allow
  playwright_*: allow
---
```

#### `senior-quote-auditor.md` (Opus)

```
---
description: Senior quotation auditor for line-by-line source verification, paraphrasing detection, and attribution accuracy. Use for critical content — legal, academic, journalistic, or public-facing writing.
mode: subagent
model: anthropic/claude-opus-5
variant: max
color: "#F97316"
permission:
  edit: deny
  bash: deny
---
```

## Full Spec Reference Table

Complete configuration for all 9 roles across all 3 escalation tiers:

| Role | Tier | File Name | Model | Steps | Edit | Bash | Web/Playwright |
|------|------|-----------|-------|-------|------|------|-----|
| **Worker** | Junior | `junior-worker.md` | `deepseek/deepseek-flash` | 50 | ✅ | ✅ | ✅ |
| | Mid | `worker.md` | `anthropic/claude-sonnet-5` | — | ✅ | ✅ | ✅ |
| | Senior | `senior-worker.md` | `anthropic/claude-opus-5` | — | ✅ | ✅ | ✅ |
| **Architect** | Junior | `junior-architect.md` | `deepseek/deepseek-flash` | 25 | ✅ | ❌ | ✅ |
| | Mid | `architect.md` | `anthropic/claude-sonnet-5` | — | ✅ | ❌ | ✅ |
| | Senior | `senior-architect.md` | `anthropic/claude-opus-5` | — | ✅ | ❌ | ✅ |
| **Planner** | Junior | `junior-planner.md` | `deepseek/deepseek-flash` | 25 | ❌ | ❌ | ❌ |
| | Mid | `planner.md` | `anthropic/claude-sonnet-5` | — | ❌ | ❌ | ❌ |
| | Senior | `senior-planner.md` | `anthropic/claude-opus-5` | — | ❌ | ❌ | ❌ |
| **Reviewer** | Junior | `junior-reviewer.md` | `deepseek/deepseek-flash` | 30 | ❌ | ✅ | ❌ |
| | Mid | `reviewer.md` | `anthropic/claude-sonnet-5` | — | ❌ | ✅ | ❌ |
| | Senior | `senior-reviewer.md` | `anthropic/claude-opus-5` | — | ❌ | ✅ | ❌ |
| **Debugger** | Junior | `junior-debugger.md` | `deepseek/deepseek-flash` | 35 | ✅ | ✅ | ✅ |
| | Mid | `debugger.md` | `anthropic/claude-sonnet-5` | — | ✅ | ✅ | ✅ |
| | Senior | `senior-debugger.md` | `anthropic/claude-opus-5` | — | ✅ | ✅ | ✅ |
| **Security** | Junior | `junior-security.md` | `deepseek/deepseek-flash` | 30 | ❌ | ✅ | ✅ |
| | Mid | `security.md` | `anthropic/claude-sonnet-5` | — | ❌ | ✅ | ✅ |
| | Senior | `senior-security.md` | `anthropic/claude-opus-5` | — | ❌ | ✅ | ✅ |
| **Editor** | Junior | `junior-editor.md` | `deepseek/deepseek-flash` | 25 | ✅ | ❌ | ❌ |
| | Mid | `editor.md` | `anthropic/claude-sonnet-5` | — | ✅ | ❌ | ❌ |
| | Senior | `senior-editor.md` | `anthropic/claude-opus-5` | — | ✅ | ❌ | ❌ |
| **Researcher** | Junior | `junior-researcher.md` | `deepseek/deepseek-flash` | 40 | ✅ | ✅ | ✅ |
| | Mid | `researcher.md` | `anthropic/claude-sonnet-5` | — | ✅ | ✅ | ✅ |
| | Senior | `senior-researcher.md` | `anthropic/claude-opus-5` | — | ✅ | ✅ | ✅ |
| **Quote Auditor** | Junior | `junior-quote-auditor.md` | `deepseek/deepseek-flash` | 25 | ❌ | ❌ | ❌ |
| | Mid | `quote-auditor.md` | `anthropic/claude-sonnet-5` | — | ❌ | ❌ | ❌ |
| | Senior | `senior-quote-auditor.md` | `anthropic/claude-opus-5` | — | ❌ | ❌ | ❌ |

Mid and senior agents (Anthropic models) are uncapped (`—`): Anthropic rejects the max-steps wrap-up (assistant-role prefill), so those agents must not set `steps`. Junior DeepSeek agents keep their step caps.

## Model IDs Quick Reference

| Provider | Model ID in frontmatter | npm Package |
|----------|------------------------|-------------|
| DeepSeek | `deepseek/deepseek-flash` | `@ai-sdk/openai-compatible` (via models.dev) |
| Anthropic (Sonnet) | `anthropic/claude-sonnet-5` | `@ai-sdk/anthropic` |
| Anthropic (Opus) | `anthropic/claude-opus-5` | `@ai-sdk/anthropic` |
| Google (gemini-mule) | `google/gemini-3.7-flash` | `@ai-sdk/google` |
| Google (Observer) | `google/gemini-3.7-flash` | `@ai-sdk/google` |
| Google (gemini-worker) | `google/gemini-3.7-flash` | `@ai-sdk/google` |
| Anthropic (Observer fallback) | `anthropic/claude-sonnet-5` | `@ai-sdk/anthropic` |
| xAI (Grok) | `xai/grok-4.5` | `@ai-sdk/xai` |

## Agent Directory Layout

OpenCode loads agent markdown from both `~/.config/opencode/agent/` and `~/.config/opencode/agents/` (glob `{agent,agents}/**/*.md`). The standard install puts the Supervisor in `agent/` and all subagents in `agents/`. What makes the Supervisor primary is `mode: primary` in frontmatter. This reference doc is **not** an agent and lives at the repo root — do not copy it into either agent folder.

```
~/.config/opencode/
├── agent/
│   └── supervisor.md         # Primary agent (mode: primary)
│
└── agents/
    ├── junior-worker.md      # DeepSeek (junior)
    ├── junior-architect.md
    ├── junior-planner.md
    ├── junior-reviewer.md
    ├── junior-debugger.md
    ├── junior-security.md
    ├── junior-editor.md
    ├── junior-researcher.md
    ├── junior-quote-auditor.md
    │
     ├── worker.md             # Claude Sonnet (mid)
     ├── architect.md
     ├── planner.md
     ├── reviewer.md
     ├── debugger.md
     ├── designer.md
     ├── security.md
     ├── editor.md
     ├── researcher.md
     ├── quote-auditor.md
    │
    ├── senior-worker.md      # Claude Opus (senior)
    ├── senior-architect.md
    ├── senior-planner.md
    ├── senior-reviewer.md
    ├── senior-debugger.md
    ├── senior-security.md
    ├── senior-editor.md
    ├── senior-researcher.md
    ├── senior-quote-auditor.md
    │
    ├── worker-mule.md        # Mule tier
    ├── architect-mule.md
    ├── researcher-mule.md
    ├── debugger-mule.md
    ├── reviewer-mule.md
    ├── security-mule.md
    ├── planner-mule.md
    ├── editor-mule.md
    ├── quote-auditor-mule.md
     ├── gemini-mule.md
     ├── grok-mule.md
     ├── claude-mule.md
     ├── designer-mule.md
     │
     ├── observer.md           # Multimodal Observer (Gemini 3.7 Flash — primary)
     ├── observer-claude.md    # Observer fallback (Claude Sonnet 5 — used when only Anthropic is configured)
    │
    ├── gemini-worker.md      # Alternative-model worker (Gemini 3.7 Flash)
    ├── grok-worker.md        # Alternative-model worker (Grok 4.5)
    ├── designer.md           # UI/UX design (Grok 4.5, native image vision)
    ├── local-coder.md        # Ollama placeholder (configure before use)
    └── local-reasoner.md     # Ollama placeholder (configure before use)
```

(`grok-worker.md` ships in `agents/` — the copy OpenCode loads. The `addons/grok-worker/` folder keeps activation notes only. `local-coder` and `local-reasoner` are Ollama placeholders, not production-ready.)

## Config Requirement: `subagent_depth: 3`

For the mule tier to work, your `opencode.json` must set `"subagent_depth": 3`. This allows chains like Supervisor → subagent → mule (depth 3). The shipped `opencode.template.json` already includes this field. If you write your own config from scratch, make sure to add it — the default depth of `1` blocks nested agent spawns and prevents subagents from spawning mules.

## How the Naming Convention Works

The Supervisor uses these names to pick the right agent:

- `junior-*` → DeepSeek (cheap, default, automatic spawning)
- `*` (no prefix) → Claude Sonnet (explicitly invoked for harder tasks)
- `senior-*` → Claude Opus (highest stakes, user explicitly asks for it)

When you say "send this to the architect," the Supervisor picks `architect` (Sonnet). When you say "use the junior architect," it picks `junior-architect` (DeepSeek). For automatic/unprompted spawning, the Supervisor defaults to `junior-*` to keep costs predictable.

## Cost Comparison

| Tier | Model | Approx. Relative Cost | Best For |
|------|-------|----------------------|----------|
| Junior | DeepSeek Flash | $ | 80% of all tasks |
| Mid | Claude Sonnet 5 | $$ | Complex reasoning, deeper reviews |
| Senior | Claude Opus 5 | $$$$ | Production-critical, highest stakes |

## Starting Simple

The repo ships with all 4 tiers already configured — 47 agent files in `agents/` (plus the Supervisor primary agent — 48 total) across 9 roles. Scaling down is just about which API keys you configure:

1. **DeepSeek only (junior tier + most mules)** — one key, one model, works for everything. The mid and senior agent files sit unused until you add their API keys.
2. **Add Anthropic (mid + senior tiers + claude-mule)** — connect your Anthropic key with `opencode auth login` and the bare-name agents (`worker`, `architect`, etc.) + all `senior-*` agents + `claude-mule` become available.
3. **Add Google (Observer + Gemini)** — connect your Google key and `observer` + `gemini-mule` + `gemini-worker` activate.
4. **Add xAI (Grok)** — connect your xAI key and `grok-mule` + `grok-worker` + `designer` + `designer-mule` activate.
5. **Full 4-tier, all providers** — all 47 subagents active (48 agents with the Supervisor), automatic escalation from junior to mid/senior when warranted.

---

## Mule Tier (Built In)

Beyond the 3 escalation tiers, the repo also ships with **13 mule-tier agents** — safe-to-spawn leaf workers whose defining invariant is that **mules can never spawn further agents** (`task: {"*": "deny"}`). This guarantees termination: any agent that spawns a mule knows the work ends there.

Mules are subagent infrastructure. The supervisor never spawns mules directly — they exist for architects, workers, debuggers, and reviewers to spawn internally for bounded sub-tasks.

All 13 mule agents use the `mode: subagent` frontmatter with `task: {"*": "deny"}`. Eleven use 30-step limits; `gemini-mule` and `claude-mule` are uncapped — Google's and Anthropic's APIs reject the max-steps wrap-up request (an assistant-role prefill), so those caps must never trigger. Nine are DeepSeek Flash (`worker-mule`, `architect-mule`, `researcher-mule`, `debugger-mule`, `reviewer-mule`, `security-mule`, `planner-mule`, `editor-mule`, `quote-auditor-mule`). Four are cross-provider: `gemini-mule` (Gemini 3.7 Flash), `grok-mule` (Grok 4.5), `claude-mule` (Claude Sonnet 5), and `designer-mule` (Grok 4.5).

> ⚠️ **Mules require `subagent_depth >= 3`.** The Supervisor spawns a subagent (depth 2), which spawns a mule (depth 3). Without `"subagent_depth": 3` in `opencode.json`, the mule spawn will be silently blocked.
