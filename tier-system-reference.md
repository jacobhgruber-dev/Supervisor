# Tier System Reference

The Supervisor ships with a complete 3-tier agent system. All 9 roles are available at every tier out of the box.

| Tier | Model | Role | Naming Convention |
|------|-------|------|-------------------|
| **Junior** | DeepSeek V4 Pro | Default workhorse, most tasks | `junior-worker`, `junior-architect`, etc. |
| **Mid** | Claude Sonnet 4.6 | Complex reasoning, deeper reviews | `worker`, `architect`, etc. (no prefix) |
| **Senior** | Claude Opus 4.8 | Highest stakes, production-critical | `senior-worker`, `senior-architect`, etc. |

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
description: General-purpose subagent powered by Claude Sonnet 4.6. Mid-tier worker for tasks needing deeper reasoning than DeepSeek. Full edit and bash access.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 40
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
description: Software architect for design decisions, refactoring plans, and system structure. Powered by Claude Sonnet 4.6.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 25
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
description: Planner for breaking down tasks into ordered steps, identifying dependencies, and estimating effort. Powered by Claude Sonnet 4.6.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 25
color: "#A78BFA"
permission:
  edit: deny
  bash: deny
---
```

#### `reviewer.md` (Sonnet)

```
---
description: Code reviewer for bugs, logic errors, and code quality. Powered by Claude Sonnet 4.6.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 30
color: "#F87171"
permission:
  edit: deny
  bash: allow
---
```

#### `debugger.md` (Sonnet)

```
---
description: Debugger for runtime errors, stack traces, and unexpected behavior. Powered by Claude Sonnet 4.6.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 35
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
description: Security auditor for vulnerability scanning — secrets, injections, unsafe dependencies, and common attack vectors. Powered by Claude Sonnet 4.6.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 30
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
description: Content editor for clarity, flow, and readability. Powered by Claude Sonnet 4.6.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 25
color: "#FBBF24"
permission:
  edit: deny
  bash: deny
---
```

#### `researcher.md` (Sonnet)

```
---
description: Researcher for topic exploration, source gathering, and structured answers. Powered by Claude Sonnet 4.6.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 40
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
description: Quote auditor for verifying quotations against their sources. Powered by Claude Sonnet 4.6.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 25
color: "#FB923C"
permission:
  edit: deny
  bash: allow
---
```

### Senior-Tier Agents (Claude Opus)

#### `senior-worker.md` (Opus)

```
---
description: Senior general-purpose subagent powered by Claude Opus 4.8. The most capable model available — use for the hardest problems.
mode: subagent
model: anthropic/claude-opus-4-8
variant: max
steps: 40
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
model: anthropic/claude-opus-4-8
variant: max
steps: 25
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
model: anthropic/claude-opus-4-8
variant: max
steps: 25
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
model: anthropic/claude-opus-4-8
variant: max
steps: 30
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
model: anthropic/claude-opus-4-8
variant: max
steps: 35
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
model: anthropic/claude-opus-4-8
variant: max
steps: 30
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
model: anthropic/claude-opus-4-8
variant: max
steps: 25
color: "#EAB308"
permission:
  edit: deny
  bash: deny
---
```

#### `senior-researcher.md` (Opus)

```
---
description: Senior researcher for deep multi-source investigation, complex topic synthesis, and strategic recommendations.
mode: subagent
model: anthropic/claude-opus-4-8
variant: max
steps: 40
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
model: anthropic/claude-opus-4-8
variant: max
steps: 25
color: "#F97316"
permission:
  edit: deny
  bash: allow
---
```

## Full Spec Reference Table

Complete configuration for all 9 roles across all 3 tiers:

| Role | Tier | File Name | Model | Steps | Edit | Bash | Web/Playwright |
|------|------|-----------|-------|-------|------|------|-----|
| **Worker** | Junior | `junior-worker.md` | `deepseek/deepseek-v4-pro` | 40 | ✅ | ✅ | ✅ |
| | Mid | `worker.md` | `anthropic/claude-sonnet-4-6` | 40 | ✅ | ✅ | ✅ |
| | Senior | `senior-worker.md` | `anthropic/claude-opus-4-8` | 40 | ✅ | ✅ | ✅ |
| **Architect** | Junior | `junior-architect.md` | `deepseek/deepseek-v4-pro` | 25 | ✅ | ❌ | ✅ |
| | Mid | `architect.md` | `anthropic/claude-sonnet-4-6` | 25 | ✅ | ❌ | ✅ |
| | Senior | `senior-architect.md` | `anthropic/claude-opus-4-8` | 25 | ✅ | ❌ | ✅ |
| **Planner** | Junior | `junior-planner.md` | `deepseek/deepseek-v4-pro` | 25 | ❌ | ❌ | ❌ |
| | Mid | `planner.md` | `anthropic/claude-sonnet-4-6` | 25 | ❌ | ❌ | ❌ |
| | Senior | `senior-planner.md` | `anthropic/claude-opus-4-8` | 25 | ❌ | ❌ | ❌ |
| **Reviewer** | Junior | `junior-reviewer.md` | `deepseek/deepseek-v4-pro` | 30 | ❌ | ✅ | ❌ |
| | Mid | `reviewer.md` | `anthropic/claude-sonnet-4-6` | 30 | ❌ | ✅ | ❌ |
| | Senior | `senior-reviewer.md` | `anthropic/claude-opus-4-8` | 30 | ❌ | ✅ | ❌ |
| **Debugger** | Junior | `junior-debugger.md` | `deepseek/deepseek-v4-pro` | 35 | ✅ | ✅ | ✅ |
| | Mid | `debugger.md` | `anthropic/claude-sonnet-4-6` | 35 | ✅ | ✅ | ✅ |
| | Senior | `senior-debugger.md` | `anthropic/claude-opus-4-8` | 35 | ✅ | ✅ | ✅ |
| **Security** | Junior | `junior-security.md` | `deepseek/deepseek-v4-pro` | 30 | ❌ | ✅ | ✅ |
| | Mid | `security.md` | `anthropic/claude-sonnet-4-6` | 30 | ❌ | ✅ | ✅ |
| | Senior | `senior-security.md` | `anthropic/claude-opus-4-8` | 30 | ❌ | ✅ | ✅ |
| **Editor** | Junior | `junior-editor.md` | `deepseek/deepseek-v4-pro` | 25 | ✅ | ❌ | ❌ |
| | Mid | `editor.md` | `anthropic/claude-sonnet-4-6` | 25 | ✅ | ❌ | ❌ |
| | Senior | `senior-editor.md` | `anthropic/claude-opus-4-8` | 25 | ✅ | ❌ | ❌ |
| **Researcher** | Junior | `junior-researcher.md` | `deepseek/deepseek-v4-pro` | 40 | ✅ | ✅ | ✅ |
| | Mid | `researcher.md` | `anthropic/claude-sonnet-4-6` | 40 | ✅ | ✅ | ✅ |
| | Senior | `senior-researcher.md` | `anthropic/claude-opus-4-8` | 40 | ✅ | ✅ | ✅ |
| **Quote Auditor** | Junior | `junior-quote-auditor.md` | `deepseek/deepseek-v4-pro` | 25 | ❌ | ❌ | ❌ |
| | Mid | `quote-auditor.md` | `anthropic/claude-sonnet-4-6` | 25 | ❌ | ❌ | ❌ |
| | Senior | `senior-quote-auditor.md` | `anthropic/claude-opus-4-8` | 25 | ❌ | ❌ | ❌ |

## Model IDs Quick Reference

| Provider | Model ID in frontmatter | npm Package |
|----------|------------------------|-------------|
| DeepSeek | `deepseek/deepseek-v4-pro` | `@ai-sdk/deepseek` |
| Anthropic (Sonnet) | `anthropic/claude-sonnet-4-6` | `@ai-sdk/anthropic` |
| Anthropic (Opus) | `anthropic/claude-opus-4-8` | `@ai-sdk/anthropic` |
| xAI (Grok) | `xai/grok-4.3` | `@ai-sdk/xai` |

## Agent Directory Layout

**Every** markdown agent — the primary Supervisor and all subagents — installs into the same folder, `~/.config/opencode/agents/` (plural). That's the only location OpenCode loads markdown agents from. This reference doc is **not** an agent and lives at the repo root, not in that folder.

```
~/.config/opencode/agents/
├── supervisor.md             # Primary agent (mode: primary)
│
├── junior-worker.md          # DeepSeek (junior)
├── junior-architect.md
├── junior-planner.md
├── junior-reviewer.md
├── junior-debugger.md
├── junior-security.md
├── junior-editor.md
├── junior-researcher.md
├── junior-quote-auditor.md
│
├── worker.md                 # Claude Sonnet (mid)
├── architect.md
├── planner.md
├── reviewer.md
├── debugger.md
├── security.md
├── editor.md
├── researcher.md
├── quote-auditor.md
│
├── senior-worker.md          # Claude Opus (senior)
├── senior-architect.md
├── senior-planner.md
├── senior-reviewer.md
├── senior-debugger.md
├── senior-security.md
├── senior-editor.md
├── senior-researcher.md
├── senior-quote-auditor.md
│
└── observer.md               # Multimodal Observer (Claude Sonnet)
```

(The optional `grok-worker` addon installs one more file here when you opt in — see `addons/grok-worker/`.)

## How the Naming Convention Works

The Supervisor uses these names to pick the right agent:

- `junior-*` → DeepSeek (cheap, default, automatic spawning)
- `*` (no prefix) → Claude Sonnet (explicitly invoked for harder tasks)
- `senior-*` → Claude Opus (highest stakes, user explicitly asks for it)

When you say "send this to the architect," the Supervisor picks `architect` (Sonnet). When you say "use the junior architect," it picks `junior-architect` (DeepSeek). For automatic/unprompted spawning, the Supervisor defaults to `junior-*` to keep costs predictable.

## Cost Comparison

| Tier | Model | Approx. Relative Cost | Best For |
|------|-------|----------------------|----------|
| Junior | DeepSeek V4 Pro | $ | 80% of all tasks |
| Mid | Claude Sonnet 4.6 | $$ | Complex reasoning, deeper reviews |
| Senior | Claude Opus 4.8 | $$$$ | Production-critical, highest stakes |

## Starting Simple

The repo ships with all 3 tiers already configured — 27 agent files across 9 roles. Scaling down is just about which API keys you configure:

1. **DeepSeek only (junior tier)** — one key, one model, works for everything. The mid and senior agent files sit unused until you add their API keys.
2. **Add Anthropic (mid tier)** — connect your Anthropic key with `opencode auth login` and the bare-name agents (`worker`, `architect`, etc.) become available with Sonnet.
3. **Add Opus (senior tier)** — the `senior-*` agents become available once both Anthropic models are configured.
4. **Full 3-tier** — all 27 agents active, automatic escalation from junior to mid/senior when warranted.
