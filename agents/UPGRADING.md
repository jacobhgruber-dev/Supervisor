# Upgrading: The Full 3-Tier System

The default setup ships with one tier — DeepSeek V4 Pro Max for everything. That's a great starting point and handles most work at low cost.

If you have an Anthropic API key, you can graduate to a **3-tier system** where the model dictates the tier, and DeepSeek becomes your workhorse "junior" tier:

| Tier | Model | Role | Naming Convention |
|------|-------|------|-------------------|
| **Junior** | DeepSeek V4 Pro Max | Default workhorse, most tasks | `junior-worker`, `junior-architect`, etc. |
| **Mid** | Claude Sonnet 4.6 Max | Complex reasoning, deeper reviews | `worker`, `architect`, etc. (no prefix) |
| **Senior** | Claude Opus 4.8 Max | Highest stakes, production-critical | `senior-worker`, `senior-architect`, etc. |

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
    "claude-opus-4-8": {
      "name": "Claude Opus 4.8 Max",
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
steps: 30
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
steps: 40
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
  bash: allow
---
```

## Step 4: Add Senior-Tier Agents (Claude Opus)

Create these with the `senior-` prefix. Same prompt content as the base agents — just different frontmatter.

### `senior-worker.md` (Opus)

```
---
description: Senior general-purpose subagent powered by Claude Opus 4.8 Max. The most capable model available — use for the hardest problems.
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
---
```

### `senior-architect.md` (Opus)

```
---
description: Senior-level system architect. Deep architectural reasoning, complex tradeoff analysis, and high-stakes design decisions. Use ONLY for the hardest problems.
mode: subagent
model: anthropic/claude-opus-4-8
variant: max
steps: 25
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
model: anthropic/claude-opus-4-8
variant: max
steps: 25
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
model: anthropic/claude-opus-4-8
variant: max
steps: 30
color: "#FF4444"
permission:
  edit: deny
  bash: allow
---
```

### `senior-debugger.md` (Opus)

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
---
```

### `senior-security.md` (Opus)

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
---
```

### `senior-editor.md` (Opus)

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

### `senior-researcher.md` (Opus)

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
---
```

### `senior-quote-auditor.md` (Opus)

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

| Role | Tier | File Name | Model | Steps | Edit | Bash | Web |
|------|------|-----------|-------|-------|------|------|-----|
| **Worker** | Junior | `junior-worker.md` | `deepseek/deepseek-v4-pro` | 40 | ✅ | ✅ | ✅ |
| | Mid | `worker.md` | `anthropic/claude-sonnet-4-6` | 40 | ✅ | ✅ | ✅ |
| | Senior | `senior-worker.md` | `anthropic/claude-opus-4-8` | 40 | ✅ | ✅ | ✅ |
| **Architect** | Junior | `junior-architect.md` | `deepseek/deepseek-v4-pro` | 25 | ❌ | ❌ | ✅ |
| | Mid | `architect.md` | `anthropic/claude-sonnet-4-6` | 25 | ❌ | ❌ | ✅ |
| | Senior | `senior-architect.md` | `anthropic/claude-opus-4-8` | 25 | ❌ | ❌ | ✅ |
| **Planner** | Junior | `junior-planner.md` | `deepseek/deepseek-v4-pro` | 25 | ❌ | ❌ | ❌ |
| | Mid | `planner.md` | `anthropic/claude-sonnet-4-6` | 25 | ❌ | ❌ | ❌ |
| | Senior | `senior-planner.md` | `anthropic/claude-opus-4-8` | 25 | ❌ | ❌ | ❌ |
| **Reviewer** | Junior | `junior-reviewer.md` | `deepseek/deepseek-v4-pro` | 30 | ❌ | ✅ | ❌ |
| | Mid | `reviewer.md` | `anthropic/claude-sonnet-4-6` | 30 | ❌ | ✅ | ❌ |
| | Senior | `senior-reviewer.md` | `anthropic/claude-opus-4-8` | 30 | ❌ | ✅ | ❌ |
| **Debugger** | Junior | `junior-debugger.md` | `deepseek/deepseek-v4-pro` | 35 | ✅ | ✅ | ❌ |
| | Mid | `debugger.md` | `anthropic/claude-sonnet-4-6` | 35 | ✅ | ✅ | ❌ |
| | Senior | `senior-debugger.md` | `anthropic/claude-opus-4-8` | 35 | ✅ | ✅ | ❌ |
| **Security** | Junior | `junior-security.md` | `deepseek/deepseek-v4-pro` | 30 | ❌ | ✅ | ✅ |
| | Mid | `security.md` | `anthropic/claude-sonnet-4-6` | 30 | ❌ | ✅ | ✅ |
| | Senior | `senior-security.md` | `anthropic/claude-opus-4-8` | 30 | ❌ | ✅ | ✅ |
| **Editor** | Junior | `junior-editor.md` | `deepseek/deepseek-v4-pro` | 25 | ✅ | ❌ | ❌ |
| | Mid | `editor.md` | `anthropic/claude-sonnet-4-6` | 25 | ✅ | ❌ | ❌ |
| | Senior | `senior-editor.md` | `anthropic/claude-opus-4-8` | 25 | ✅ | ❌ | ❌ |
| **Researcher** | Junior | `junior-researcher.md` | `deepseek/deepseek-v4-pro` | 40 | ✅ | ✅ | ✅ |
| | Mid | `researcher.md` | `anthropic/claude-sonnet-4-6` | 40 | ✅ | ✅ | ✅ |
| | Senior | `senior-researcher.md` | `anthropic/claude-opus-4-8` | 40 | ✅ | ✅ | ✅ |
| **Quote Auditor** | Junior | `junior-quote-auditor.md` | `deepseek/deepseek-v4-pro` | 25 | ❌ | ✅ | ❌ |
| | Mid | `quote-auditor.md` | `anthropic/claude-sonnet-4-6` | 25 | ❌ | ✅ | ❌ |
| | Senior | `senior-quote-auditor.md` | `anthropic/claude-opus-4-8` | 25 | ❌ | ✅ | ❌ |

## Model IDs Quick Reference

| Provider | Model ID in frontmatter | npm Package |
|----------|------------------------|-------------|
| DeepSeek | `deepseek/deepseek-v4-pro` | `@ai-sdk/deepseek` |
| Anthropic (Sonnet) | `anthropic/claude-sonnet-4-6` | `@ai-sdk/anthropic` |
| Anthropic (Opus) | `anthropic/claude-opus-4-8` | `@ai-sdk/anthropic` |
| xAI (Grok) | `xai/grok-4.3` | `@ai-sdk/xai` |

## Step 5: Update the Supervisor Prompt (Critical)

Renaming agents to `junior-*` is only half the job. The supervisor prompt itself must be updated — otherwise it'll try to spawn agents with the old bare names and find nothing. Here are the exact changes, drawn from the original production setup.

### supervisor.md changes

**Change 1 — Mission statement (line 8):**

Change:
```
You are the Senior Supervisor speaking to the Manager. Your job is to keep your
context window tight and orchestrate work through subagents.
```
To:
```
You are the Senior Supervisor speaking to the Manager. Your job is to keep your
context window tight and orchestrate work through junior-tier subagents.
```

**Change 2 — Pre-Implementation Triage table (lines 92-102):**

Prefix every agent name with `junior-`:

| Single-tier (current) | 3-tier (change to) |
|---|---|
| `Spawn \`worker\`` | `Spawn \`junior-worker\`` |
| `Spawn \`debugger\`` | `Spawn \`junior-debugger\`` |
| `Spawn \`researcher\`` | `Spawn \`junior-researcher\`` |
| `Spawn \`architect\`` | `Spawn \`junior-architect\`` |
| `Spawn \`planner\`` | `Spawn \`junior-planner\`` |
| `Spawn \`security\`` | `Spawn \`junior-security\`` |

Also update the closing line:
```
When in doubt, triage first — a misdirected `worker` wastes a whole session.
```
To:
```
When in doubt, triage first — a misdirected `junior-worker` wastes a whole session.
```

**Change 3 — Subagent Toolbox table (lines 140-148):**

Add `junior-` prefix to every agent name in the table. Example:

| Single-tier | 3-tier |
|---|---|
| `\`worker\`` | `\`junior-worker\`` |
| `\`researcher\`` | `\`junior-researcher\`` |
| `\`debugger\`` | `\`junior-debugger\`` |
| (etc. — all 9 roles) | |

**Change 4 — Default tier policy (line 151):**

Change:
```
Default to these subagents. Match the subagent to the *activity*...
```
To:
```
Default to the junior tier. Match the subagent to the *activity*, not just the
project area — implementation, investigation, research, design, review, security,
planning, editing, and quote-auditing are different jobs. The Manager will
escalate to mid/senior tier explicitly if needed.
```

Also replace the "Optional 3-tier upgrade" blurb (lines 153-154) with just:
```
For escalations, use the bare names (`worker`, `architect`, etc.) for Sonnet and
`senior-*` for Opus. See `agents/UPGRADING.md` for the full spec.
```

### AGENTS.md changes

The Spawning Rules section currently says "default to the base tier." Update the last section to match the 3-tier system:

Replace:
```
## Spawning Rules (Always Active)

Subagents are specialized agents you can spawn for focused work. See the
`supervisor.md` for the orchestration workflow and `reference.md` for the full
subagent catalog.

**Default tier policy:**
- Default to the base tier (DeepSeek V4 Pro Max) for all automatic/unprompted
  subagent spawning.
- Before using a higher-tier subagent autonomously, explain to the user WHY
  it's warranted.
- When the user explicitly names a subagent, use exactly what they asked for.
- For simple file-discovery tasks, the `explore` built-in subagent is always
  acceptable.

**Rationale:** The base tier (DeepSeek V4 Pro Max) is a frontier model fully
capable of professional work. Upper tiers (Claude Sonnet/Opus) are reserved for
conscious escalation, not background convenience.
```

With:
```
## Subagent Spawning Rules (Always Active)

The Task tool can spawn specialized subagents (27 available across 9 roles at
3 tiers — see `reference.md` for the full catalog).

**Default tier policy:**

- **Default to the junior tier** (DeepSeek V4 Pro Max) for all
  automatic/unprompted subagent spawning.
- Before using a mid or senior tier subagent autonomously, explain to the user
  WHY the higher tier is warranted (e.g., "this bug involves distributed state —
  I want Opus on it because DeepSeek might miss a race condition").
- When the user explicitly names a subagent (e.g., "send this to
  senior-architect"), use exactly what they asked for — no override.
- For simple research/file-discovery tasks, the `explore` built-in subagent is
  always acceptable — it's already lightweight.

**Rationale:** The junior tier (DeepSeek V4 Pro Max) is a frontier model fully
capable of professional work. The mid and senior tiers (Sonnet/Opus Max) are
reserved for conscious escalation, not background convenience. You should not
silently spend Anthropic credits on tasks that DeepSeek can handle.
```

## Updating subagents.md

Optionally update the subagent quick reference to reflect the 3-tier naming. The quickest fix: update the header line in `subagents.md` to:

```
27 subagent files across 9 roles at 3 tiers • upgrade path: see agents/UPGRADING.md
```

## Verifying the 3-Tier Setup

After making all changes, your agent directory should look like:

```
~/.config/opencode/agents/
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
├── grok-worker.md            # Alternative model
└── UPGRADING.md              # This file
```

Restart opencode. The Supervisor should now spawn `junior-*` agents by default, with `*` (Sonnet) and `senior-*` (Opus) available for explicit escalation.

---

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
| Senior | Claude Opus 4.8 Max | $$$$ | Production-critical, highest stakes |

## Starting Simple

Don't feel pressure to set up all 3 tiers at once. The single-tier DeepSeek setup (what ships in this repo) works great on its own. Add tiers gradually:

1. **Start with DeepSeek only** — one key, one model, works for everything
2. **Add a mid-tier worker** — just `worker.md` with Sonnet, for when you want deeper reasoning on specific tasks
3. **Add senior workers** — `senior-worker.md` and `senior-architect.md` with Opus, for the hardest problems
4. **Fill out the full 3-tier grid** — if you find yourself wanting different models for different roles
