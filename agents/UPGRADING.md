# Upgrading: Adding Claude Sonnet & Opus Tiers

The default agents in this repo use DeepSeek V4 Pro Max — a frontier model that handles professional-level work at low cost. For higher-stakes work, you can add Claude Sonnet (mid-tier) or Claude Opus (senior-tier) versions of each agent.

## Quick Setup: Claude Sonnet (recommended upgrade)

Add this provider to your opencode.json:

```json
"provider": {
  "anthropic": {
    "npm": "@ai-sdk/anthropic",
    "name": "Anthropic (Claude)",
    "options": {
      "apiKey": "YOUR_ANTHROPIC_API_KEY"
    },
    "models": {
      "claude-sonnet-4-6-20250514": {
        "name": "Claude Sonnet 4.6 Max",
        "tools": true
      },
      "claude-opus-4-7-20250514": {
        "name": "Claude Opus 4.7 Max",
        "tools": true
      }
    }
  }
}
```

Get your API key at: https://console.anthropic.com

## Adding Sonnet Subagents

For each agent you want to upgrade, create a new file with the `sonnet-` prefix:

### `agents/sonnet-architect.md`
```
---
description: Claude Sonnet architect for deeper design questions and complex tradeoff analysis.
mode: subagent
model: anthropic/claude-sonnet-4-6-20250514
steps: 12
color: "#7B61FF"
permission:
  edit: deny
  bash: deny
  webfetch: allow
  websearch: allow
---

You are a software architect powered by Claude Sonnet. You handle design questions, code structure reviews, tradeoff analysis, and architectural decision-making.

[Same prompt text as the architect agent — copy from agents/architect.md]
```

### `agents/sonnet-worker.md`
```
---
description: General-purpose worker powered by Claude Sonnet. Use for tasks where you want Sonnet's reasoning depth.
mode: subagent
model: anthropic/claude-sonnet-4-6-20250514
steps: 30
color: "#818CF8"
permission:
  edit: allow
  bash: allow
  webfetch: allow
  websearch: allow
---

[Same prompt text as worker.md]
```

## Adding Opus Subagents (highest tier)

For the most critical work, create Opus-tier agents with the `senior-` prefix:

### `agents/senior-architect.md`
```
---
description: Claude Opus architect for the hardest design problems — complex systems, critical tradeoffs.
mode: subagent
model: anthropic/claude-opus-4-7-20250514
steps: 15
color: "#B026FF"
permission:
  edit: deny
  bash: deny
  webfetch: allow
  websearch: allow
---

[Same prompt text as architect.md]
```

## Tier Comparison

| Tier | Model | Best For | Relative Cost |
|------|-------|----------|---------------|
| Base | DeepSeek V4 Pro Max | Default — most tasks | $ |
| Mid | Claude Sonnet 4.6 Max | Complex reasoning, PR reviews | $$ |
| Senior | Claude Opus 4.7 Max | Highest stakes, production-critical | $$$$ |

## Pattern

Follow this pattern for any agent role:
1. Copy the base agent's .md file
2. Rename with the tier prefix (`sonnet-` or `senior-`)
3. Update the model field in frontmatter
4. Adjust step count (Sonnet ~12-14, Opus ~15-20)
5. Update the description to reflect the tier
6. Optionally update the color for visual distinction in the opencode UI
