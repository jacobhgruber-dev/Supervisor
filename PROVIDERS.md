# 🔑 Provider Setup Guide

The Supervisor system needs API keys to power its agents. This guide walks through setting up each provider. All four can be configured in under 10 minutes total.

---

## Tier 1: DeepSeek (Required)

**What it powers:** The Supervisor agent, the entire junior tier (9 subagents), and 9 DeepSeek mule-tier agents.

**Cost:** Extremely cheap. A $2–$5 credit top-up lasts weeks of regular use.

**Sign up:** [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)

**Steps:**

1. Sign up with email + password at the link above.
2. Top up $2–$5 under **Billing** (required — a $0 balance gives "insufficient balance" errors).
3. Create an API key under **API Keys**.
4. Copy the key — it starts with `sk-...` and you won't be able to view it again after closing the dialog.

**Connect the key:**

- **OpenCode Desktop:** Settings → Providers → DeepSeek → Paste the key.
- **CLI:** Run `opencode auth login`, choose **DeepSeek**, paste the key.

> The key is stored securely by OpenCode in `~/.local/share/opencode/auth.json`. You never put it in a config file.

---

## Tier 2: Anthropic / Claude (Highly Recommended)

**What it powers:**
- **Mid tier** — 9 agents on Claude Sonnet 4.6 (`worker`, `architect`, `reviewer`, etc.)
- **Senior tier** — 9 agents on Claude Opus 4.8 (`senior-worker`, `senior-architect`, etc.)
- **Observer** — screenshot reading / multimodal vision agent (Sonnet 4.6)

**Cost:** More expensive than DeepSeek. Use deliberately — the Supervisor defaults to junior (DeepSeek) agents and only escalates to mid/senior when you explicitly ask.

**Sign up:** [console.anthropic.com](https://console.anthropic.com)

**Steps:**

1. Sign up at the link above.
2. Add $5 credit under **Billing**.
3. Create an API key under **API Keys**.
4. Copy the key — it starts with `sk-ant-...`.

**Connect the key:**

- **OpenCode Desktop:** Settings → Providers → Anthropic → Paste the key.
- **CLI:** Run `opencode auth login`, choose **Anthropic**, paste the key.

> Once connected, the mid and senior agents (all 18 files, already installed) activate automatically. You can say "use the senior reviewer" and the agent picks it up without any further configuration.

---

## Tier 3: Google / Gemini (Recommended)

**What it powers:**
- `gemini-worker` — full-access Gemini agent (Gemini 2.5 Pro)
- `gemini-mule` — leaf agent for long-context, multimodal, or web-heavy tasks (Gemini 2.5 Flash)

**Cost:** Moderate. Cheaper than Anthropic, pricier than DeepSeek.

**Sign up:** [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

**Steps:**

1. Sign in with your Google account.
2. Click **Create API Key**.
3. Copy the key.

**Connect the key:**

- **OpenCode Desktop:** Settings → Providers → Google → Paste the key.
- **CLI:** Run `opencode auth login`, choose **Google**, paste the key.

> The `gemini-worker` and `gemini-mule` agent files ship with the repo and activate once the key is present.

---

## Tier 4: xAI / Grok (Optional)

**What it powers:**
- `grok-worker` — alternative-model worker on Grok 4.3 (requires installing the addon from `addons/grok-worker/`)
- `grok-mule` — leaf agent for creative reasoning and complex coding (3x the cost of `worker-mule` — use sparingly)

**Cost:** Moderate. The Grok worker addon is optional and independent of the core system.

**Sign up:** [console.x.ai](https://console.x.ai)

**Steps:**

1. Sign up at the link above.
2. Add credit under **Billing**.
3. Create an API key under **API Keys**.
4. Copy the key.

**Connect the key:**

- **OpenCode Desktop:** Settings → Providers → xAI → Paste the key.
- **CLI:** Run `opencode auth login`, choose **xAI**, paste the key.

> To use `grok-worker`, you must also install the addon — copy `addons/grok-worker/grok-worker.md` into `~/.config/opencode/agents/`. See `addons/grok-worker/README.md` for full instructions.

---

## How It All Fits Together

| Provider | What It Unlocks | Cost Tier | Setup Time |
|----------|----------------|-----------|------------|
| **DeepSeek** | Supervisor + 9 junior subagents (the whole system) | $ (cheapest) | ~2 min |
| **Anthropic** | 9 mid + 9 senior subagents + Observer vision | $$$ (priciest) | ~3 min |
| **Google** | gemini-worker + gemini-mule | $$ (moderate) | ~2 min |
| **xAI** | grok-worker + grok-mule (optional addon) | $$ (moderate) | ~3 min |

**Architecture in one sentence:** The Supervisor runs on DeepSeek. It spawns junior agents on DeepSeek by default. Mid and senior agents (Anthropic), Gemini agents (Google), and Grok agents (xAI) sit ready and activate as soon as their key is connected. No config changes needed — the agent files are already installed.

---

## IMPORTANT: Do NOT Add a Provider Block to opencode.json

When you connect a key through OpenCode Desktop or `opencode auth login`, the key is stored in a secure internal file (`~/.local/share/opencode/auth.json`). OpenCode handles the provider wiring internally.

Adding a `"provider"` block to `opencode.json` can **override** the internal implementation and break authentication. The template config (`opencode.json` in this repo) intentionally does not include a provider block for this reason.

If you see a `"provider"` block in any config template, delete it — let OpenCode manage providers natively.

---

## One-Key Minimum

**You only need DeepSeek to start.** The entire system — Supervisor + all 9 junior agents — runs on DeepSeek alone. That one key (and $2 of credit) gets you a fully functional AI agent team.

Add Anthropic, Google, or xAI keys later at your own pace. The agent files are already in place; they simply activate when the key appears. No rewiring, no config edits.

---

## Model IDs (Reference)

When configuring providers manually or writing agent frontmatter:

| Provider | Model ID | Agent Files |
|----------|----------|-------------|
| DeepSeek | `deepseek/deepseek-v4-pro` | `supervisor.md`, all `junior-*.md` |
| Anthropic (Sonnet) | `anthropic/claude-sonnet-4-6` | `worker.md`, `architect.md`, etc. |
| Anthropic (Opus) | `anthropic/claude-opus-4-8` | all `senior-*.md` |
| Google (Pro) | `google/gemini-3.1-pro-preview` | `gemini-worker.md` |
| Google (Flash) | `google/gemini-2.5-flash` | `gemini-mule.md`, `observer.md` |
| xAI (Grok) | `xai/grok-4.3` | `grok-worker.md` (addon), `grok-mule.md` |
