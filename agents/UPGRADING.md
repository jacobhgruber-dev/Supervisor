# Upgrading: The Full 3-Tier System

The default setup ships with one tier — DeepSeek V4 Pro Max for everything. That's a great starting point and handles most work at low cost.

If you have an Anthropic API key, you can graduate to a **3-tier system** where the model dictates the tier, and DeepSeek becomes your workhorse "junior" tier:

| Tier | Model | Role | Naming Convention |
|------|-------|------|-------------------|
| **Junior** | DeepSeek V4 Pro Max | Default workhorse, most tasks | `junior-worker`, `junior-architect`, etc. |
| **Mid** | Claude Sonnet 4.6 Max | Complex reasoning, deeper reviews | `worker`, `architect`, etc. (no prefix) |
| **Senior** | Claude Opus 4.7 Max | Highest stakes, production-critical | `senior-worker`, `senior-architect`, etc. |

## Why Go 3-Tier?

The naming convention creates a natural escalation path:

1. **Junior (DeepSeek)** — the default. Spawned automatically for most work. Cheap, capable, handles 80%+ of tasks.
2. **Mid (Sonnet)** — explicitly invoked for tasks needing deeper reasoning: complex PR reviews, tricky refactors, nuanced security analysis.
3. **Senior (Opus)** — reserved for when it really matters: deployment-critical code, distributed system debugging, architecture for new services.

The Supervisor's default policy is to spawn junior-tier agents automatically and escalate only when the user asks or the task warrants it. This keeps costs predictable while still having the big guns available.

## Step 1: Add the Anthropic Provider

Add this to your opencode.json `provider` section:

```json
"anthropic": {
  "npm": "@ai-sdk/anthropic",
  "name": "Anthropic (Claude)",
  "options": {
    "apiKey": "YOUR_ANTHROPIC_API_KEY"
  },
  "models": {
    "claude-sonnet-4-6": {
      "name": "Claude Sonnet 4.6 Max",
      "tools": true
    },
    "claude-opus-4-7": {
      "name": "Claude Opus 4.7 Max",
      "tools": true
    }
  }
}
```

Get your key at: https://console.anthropic.com

## Step 2: Rename Existing DeepSeek Agents to Junior Tier

Since your existing agents are DeepSeek, they become the junior tier. Rename them:

```bash
cd ~/.config/opencode/agents/

# Worker
mv worker.md junior-worker.md

# Specialized roles
mv architect.md junior-architect.md
mv planner.md junior-planner.md
mv reviewer.md junior-reviewer.md
mv debugger.md junior-debugger.md
mv security.md junior-security.md
mv editor.md junior-editor.md
mv researcher.md junior-researcher.md
mv quote-auditor.md junior-quote-auditor.md
```

Then update the `description` field in each file to say "junior" instead of just the role name. For example, in `junior-worker.md`, change:

```
description: General-purpose subagent powered by DeepSeek V4 Pro Max...
```

to:

```
description: Junior general-purpose subagent powered by DeepSeek V4 Pro Max...
```

The model, steps, permissions, and prompt content stay the same — they were already correct for the junior tier.

## Step 3: Add Mid-Tier Agents (Claude Sonnet)

Create these files. The prompt content is the same as the corresponding junior agent — copy from the junior file and just update the frontmatter.

### `worker.md` (Sonnet)

```
---
description: General-purpose subagent powered by Claude Sonnet 4.6 Max. Mid-tier worker for tasks needing deeper reasoning than DeepSeek. Full edit and bash access.
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
---
```

### `architect.md` (Sonnet)

```
---
description: Software architect for design decisions, refactoring plans, and system structure. Powered by Claude Sonnet 4.6 Max.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 25
color: "#7B61FF"
permission:
  edit: deny
  bash: deny
  webfetch: allow
  websearch: allow
---
```

### `planner.md` (Sonnet)

```
---
description: Planner for breaking down tasks into ordered steps, identifying dependencies, and estimating effort. Powered by Claude Sonnet 4.6 Max.
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

### `reviewer.md` (Sonnet)

```
---
description: Code reviewer for bugs, logic errors, and code quality. Powered by Claude Sonnet 4.6 Max.
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

### `debugger.md` (Sonnet)

```
---
description: Debugger for runtime errors, stack traces, and unexpected behavior. Powered by Claude Sonnet 4.6 Max.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 35
color: "#EF4444"
permission:
  edit: allow
  bash: allow
---
```

### `security.md` (Sonnet)

```
---
description: Security auditor for vulnerability scanning — secrets, injections, unsafe dependencies, and common attack vectors. Powered by Claude Sonnet 4.6 Max.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 25
color: "#B91C1C"
permission:
  edit: deny
  bash: allow
  webfetch: allow
  websearch: allow
---
```

### `editor.md` (Sonnet)

```
---
description: Content editor for clarity, flow, and readability. Powered by Claude Sonnet 4.6 Max.
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

### `researcher.md` (Sonnet)

```
---
description: Researcher for topic exploration, source gathering, and structured answers. Powered by Claude Sonnet 4.6 Max.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 35
color: "#34D399"
permission:
  edit: allow
  bash: allow
  webfetch: allow
  websearch: allow
---
```

### `quote-auditor.md` (Sonnet)

```
---
description: Quote auditor for verifying quotations against their sources. Powered by Claude Sonnet 4.6 Max.
mode: subagent
model: anthropic/claude-sonnet-4-6
variant: max
steps: 25
color: "#FB923C"
permission:
  edit: deny
  bash: deny
---
```

## Step 4: Add Senior-Tier Agents (Claude Opus)

Create these with the `senior-` prefix. Same prompt content as the base agents — just different frontmatter.

### `senior-worker.md` (Opus)

```
---
description: Senior general-purpose subagent powered by Claude Opus 4.7 Max. The most capable model available — use for the hardest problems.
mode: subagent
model: anthropic/claude-opus-4-7
variant: max
steps: 40
color: "#6366F1"
permission:
  edit: allow
  bash: allow
  webfetch: allow
  websearch: allow
---
```

### `senior-architect.md` (Opus)

```
---
description: Senior-level system architect. Deep architectural reasoning, complex tradeoff analysis, and high-stakes design decisions. Use ONLY for the hardest problems.
mode: subagent
model: anthropic/claude-opus-4-7
variant: max
steps: 20
color: "#B026FF"
permission:
  edit: deny
  bash: deny
  webfetch: allow
  websearch: allow
---
```

### `senior-planner.md` (Opus)

```
---
description: Senior planner for complex multi-phase execution strategy, dependency mapping, risk assessment, and milestone planning.
mode: subagent
model: anthropic/claude-opus-4-7
variant: max
steps: 18
color: "#8B5CF6"
permission:
  edit: deny
  bash: deny
---
```

### `senior-reviewer.md` (Opus)

```
---
description: Senior code reviewer. Deep bug detection, architectural misuse, and subtle logic flaws. Use for critical code before deployment.
mode: subagent
model: anthropic/claude-opus-4-7
variant: max
steps: 30
color: "#FF4444"
permission:
  edit: deny
  bash: deny
---
```

### `senior-debugger.md` (Opus)

```
---
description: Senior debugger for the hardest bugs — race conditions, memory leaks, distributed system failures, heisenbugs.
mode: subagent
model: anthropic/claude-opus-4-7
variant: max
steps: 35
color: "#DC2626"
permission:
  edit: allow
  bash: allow
---
```

### `senior-security.md` (Opus)

```
---
description: Senior security auditor for comprehensive vulnerability assessment — injection attacks, auth flaws, secret exposure, supply chain risks, and zero-day patterns.
mode: subagent
model: anthropic/claude-opus-4-7
variant: max
steps: 30
color: "#991B1B"
permission:
  edit: deny
  bash: allow
  webfetch: allow
  websearch: allow
---
```

### `senior-editor.md` (Opus)

```
---
description: Senior editor for content strategy, structural revision, and high-stakes writing. Final polish before publication.
mode: subagent
model: anthropic/claude-opus-4-7
variant: max
steps: 15
color: "#EAB308"
permission:
  edit: deny
  bash: deny
---
```

### `senior-researcher.md` (Opus)

```
---
description: Senior researcher for deep multi-source investigation, complex topic synthesis, and strategic recommendations.
mode: subagent
model: anthropic/claude-opus-4-7
variant: max
steps: 40
color: "#10B981"
permission:
  edit: allow
  bash: allow
  webfetch: allow
  websearch: allow
---
```

### `senior-quote-auditor.md` (Opus)

```
---
description: Senior quotation auditor for line-by-line source verification, paraphrasing detection, and attribution accuracy. Use for critical content — legal, academic, journalistic, or public-facing writing.
mode: subagent
model: anthropic/claude-opus-4-7
variant: max
steps: 20
color: "#F97316"
permission:
  edit: deny
  bash: deny
---
```

## Full Spec Reference Table

Complete configuration for all 9 roles across all 3 tiers:

| Role | Tier | File Name | Model | Steps | Edit | Bash | Web |
|------|------|-----------|-------|-------|------|------|-----|
| **Worker** | Junior | `junior-worker.md` | `deepseek/deepseek-v4-pro` | 40 | ✅ | ✅ | ✅ |
| | Mid | `worker.md` | `anthropic/claude-sonnet-4-6` | 40 | ✅ | ✅ | ✅ |
| | Senior | `senior-worker.md` | `anthropic/claude-opus-4-7` | 40 | ✅ | ✅ | ✅ |
| **Architect** | Junior | `junior-architect.md` | `deepseek/deepseek-v4-pro` | 25 | ❌ | ❌ | ✅ |
| | Mid | `architect.md` | `anthropic/claude-sonnet-4-6` | 25 | ❌ | ❌ | ✅ |
| | Senior | `senior-architect.md` | `anthropic/claude-opus-4-7` | 20 | ❌ | ❌ | ✅ |
| **Planner** | Junior | `junior-planner.md` | `deepseek/deepseek-v4-pro` | 25 | ❌ | ❌ | ❌ |
| | Mid | `planner.md` | `anthropic/claude-sonnet-4-6` | 25 | ❌ | ❌ | ❌ |
| | Senior | `senior-planner.md` | `anthropic/claude-opus-4-7` | 18 | ❌ | ❌ | ❌ |
| **Reviewer** | Junior | `junior-reviewer.md` | `deepseek/deepseek-v4-pro` | 30 | ❌ | ✅ | ❌ |
| | Mid | `reviewer.md` | `anthropic/claude-sonnet-4-6` | 30 | ❌ | ✅ | ❌ |
| | Senior | `senior-reviewer.md` | `anthropic/claude-opus-4-7` | 30 | ❌ | ❌ | ❌ |
| **Debugger** | Junior | `junior-debugger.md` | `deepseek/deepseek-v4-pro` | 35 | ❌ | ✅ | ❌ |
| | Mid | `debugger.md` | `anthropic/claude-sonnet-4-6` | 35 | ✅ | ✅ | ❌ |
| | Senior | `senior-debugger.md` | `anthropic/claude-opus-4-7` | 35 | ✅ | ✅ | ❌ |
| **Security** | Junior | `junior-security.md` | `deepseek/deepseek-v4-pro` | 25 | ❌ | ✅ | ✅ |
| | Mid | `security.md` | `anthropic/claude-sonnet-4-6` | 25 | ❌ | ✅ | ✅ |
| | Senior | `senior-security.md` | `anthropic/claude-opus-4-7` | 30 | ❌ | ✅ | ✅ |
| **Editor** | Junior | `junior-editor.md` | `deepseek/deepseek-v4-pro` | 25 | ❌ | ❌ | ❌ |
| | Mid | `editor.md` | `anthropic/claude-sonnet-4-6` | 25 | ❌ | ❌ | ❌ |
| | Senior | `senior-editor.md` | `anthropic/claude-opus-4-7` | 15 | ❌ | ❌ | ❌ |
| **Researcher** | Junior | `junior-researcher.md` | `deepseek/deepseek-v4-pro` | 35 | ✅ | ✅ | ✅ |
| | Mid | `researcher.md` | `anthropic/claude-sonnet-4-6` | 35 | ✅ | ✅ | ✅ |
| | Senior | `senior-researcher.md` | `anthropic/claude-opus-4-7` | 40 | ✅ | ✅ | ✅ |
| **Quote Auditor** | Junior | `junior-quote-auditor.md` | `deepseek/deepseek-v4-pro` | 25 | ❌ | ❌ | ❌ |
| | Mid | `quote-auditor.md` | `anthropic/claude-sonnet-4-6` | 25 | ❌ | ❌ | ❌ |
| | Senior | `senior-quote-auditor.md` | `anthropic/claude-opus-4-7` | 20 | ❌ | ❌ | ❌ |

## Model IDs Quick Reference

| Provider | Model ID in frontmatter | npm Package |
|----------|------------------------|-------------|
| DeepSeek | `deepseek/deepseek-v4-pro` | `@ai-sdk/deepseek` |
| Anthropic (Sonnet) | `anthropic/claude-sonnet-4-6` | `@ai-sdk/anthropic` |
| Anthropic (Opus) | `anthropic/claude-opus-4-7` | `@ai-sdk/anthropic` |
| xAI (Grok) | `xai/grok-4.3` | `@ai-sdk/xai` |

## How the Naming Convention Works

The Supervisor uses these names to pick the right agent:

- `junior-*` → DeepSeek (cheap, default, automatic spawning)
- `*` (no prefix) → Claude Sonnet (explicitly invoked for harder tasks)
- `senior-*` → Claude Opus (highest stakes, user explicitly asks for it)

When you say "send this to the architect," the Supervisor picks `architect` (Sonnet). When you say "use the junior architect," it picks `junior-architect` (DeepSeek). For automatic/unprompted spawning, the Supervisor defaults to `junior-*` to keep costs predictable.

## Cost Comparison

| Tier | Model | Approx. Relative Cost | Best For |
|------|-------|----------------------|----------|
| Junior | DeepSeek V4 Pro Max | $ | 80% of all tasks |
| Mid | Claude Sonnet 4.6 Max | $$ | Complex reasoning, deeper reviews |
| Senior | Claude Opus 4.7 Max | $$$$ | Production-critical, highest stakes |

## Starting Simple

Don't feel pressure to set up all 3 tiers at once. The single-tier DeepSeek setup (what ships in this repo) works great on its own. Add tiers gradually:

1. **Start with DeepSeek only** — one key, one model, works for everything
2. **Add a mid-tier worker** — just `worker.md` with Sonnet, for when you want deeper reasoning on specific tasks
3. **Add senior workers** — `senior-worker.md` and `senior-architect.md` with Opus, for the hardest problems
4. **Fill out the full 3-tier grid** — if you find yourself wanting different models for different roles
