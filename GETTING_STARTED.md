<!-- markdownlint-disable MD033 MD041 -->
<div align="center">

# 🚀 Getting Started — Zero to Hero

### Never set up an AI coding agent before? Start here.

**This guide assumes you know nothing.** No prior experience with OpenCode, API keys, or terminals required. Follow it top to bottom and you'll have a working AI "team" in about 15 minutes.

<br>

![Difficulty](https://img.shields.io/badge/difficulty-beginner-brightgreen?style=for-the-badge)
![Time](https://img.shields.io/badge/time-~15_min-blue?style=for-the-badge)
![Cost to start](https://img.shields.io/badge/cost_to_start-~$1_of_credit-orange?style=for-the-badge)

</div>

---

## 🧭 What you're about to set up (in plain English)

You're installing a free app called **OpenCode** that runs in your terminal. On its own, OpenCode is just a chat box for talking to an AI. This repo turns it into something much more powerful: a **Supervisor**.

Think of it like hiring a project manager instead of a single freelancer:

> **You** talk to **one** agent — the **Supervisor**.
> The Supervisor breaks your request into pieces, hands each piece to a specialist (a "worker," a "reviewer," a "security auditor," and 6 more roles), checks their work, fixes mistakes, and reports back to you.

You never manage the team. You just say *"build me a login page"* or *"find the bug in this file,"* and the Supervisor handles the rest.

```
        YOU
         │   "Build a REST API for the user model"
         ▼
   ┌───────────────┐
   │  SUPERVISOR   │  plans → delegates → reviews → fixes → commits
   └───────────────┘
         │
   ┌─────┼─────┬─────────┬──────────┐
   ▼     ▼     ▼         ▼          ▼
 worker architect reviewer security  …+5 more roles
```

**The one thing that powers all of this is an *API key* — so let's explain that next.**

---

## 🔑 What is an API key? (read this if you've never used one)

An **API key** is a long password that lets your computer talk to an AI model (like DeepSeek or Claude) over the internet. The AI doesn't run on your laptop — it runs on the model company's servers. Your key tells them *"this request is from me, charge it to my account."*

A few things that surprise beginners:

- **It costs money, but barely.** You pay per use (per word in and out). The default model in this setup, **DeepSeek**, is extremely cheap — a typical task costs a fraction of a cent. Most people put **$2–$5** of credit on their account and it lasts for weeks.
- **Treat it like a password.** Anyone with your key can spend your money. Never post it publicly or commit it to GitHub. (You'll connect your key with OpenCode's built-in `auth login`, which tucks it into its own secure file on your machine — it never goes into this repo's config, so there's nothing to accidentally commit.)
- **You can delete it anytime.** If a key ever leaks, you log into the provider's website and revoke it. No harm done.

That's the whole concept. Now let's get one.

---

## ✅ Before you begin — the 3 things you need

| # | Thing | Why | Get it |
|---|-------|-----|--------|
| 1 | **A terminal** | Where you type commands | Already on your Mac (**Terminal** app) or Linux. On Windows, install [Git Bash](https://git-scm.com/downloads). |
| 2 | **Node.js** | OpenCode runs on it | Mac: `brew install node` · or download from [nodejs.org](https://nodejs.org) |
| 3 | **A DeepSeek API key** | Powers the whole team | We'll get this in **Step 2** 👇 |

> 💡 **What's a terminal?** It's the app where you type text commands instead of clicking buttons. On a Mac, press `Cmd + Space`, type "Terminal," and hit Enter. Everything in a grey box below gets typed (or pasted) there, followed by Enter.

> 💡 **How do I know if I have Node?** Type `node --version` in your terminal. If you see a number like `v22.x.x`, you're set. If it says "command not found," install it using the link above.

---

## 🟢 Step 1 — Install OpenCode

In your terminal, paste this and press Enter:

```bash
npm install -g opencode
```

**Did it work?** Run:

```bash
opencode --version
```

If you see a version number, you're good. ✅
If you see `command not found`, Node didn't install correctly — go back and install Node.js first.

---

## 🟢 Step 2 — Get your DeepSeek API key (the only key you need to start)

This is the key that powers your Supervisor and all 9 junior specialists. **It's the only one required.**

1. Go to **[platform.deepseek.com](https://platform.deepseek.com/api_keys)** and create an account (email + password).
2. Add a little credit: look for **"Top up"** or **"Billing"** and add **$2–$5**. (This lasts a long time — DeepSeek is cheap.)
3. Click **"API keys"** in the sidebar → **"Create new API key."**
4. **Copy the key immediately** and paste it somewhere safe (a notes app for now). It looks like `sk-1a2b3c...` and **you can't view it again** after you close the box.

> ⚠️ **Don't skip the "add credit" part.** A brand-new key with $0 balance will give you "insufficient balance" errors that look like the setup is broken when it isn't.

**Checkpoint:** You should now have a string starting with `sk-` saved somewhere. ✅

---

## 🟢 Step 3 — Put the files where OpenCode looks for them

OpenCode reads its settings from a hidden folder in your home directory: `~/.config/opencode/`. We need to copy this repo's files there.

First, **download this repo** (if you haven't already):

```bash
git clone https://github.com/jacobhgruber-dev/Supervisor.git
cd Supervisor
```

Now copy the pieces into place. Paste these one block at a time:

> ⚠️ **Already configured providers in Desktop or have custom settings in your opencode.json?** Skip the template copy — just copy the agent files, plugin, and AGENTS.md. The template WILL overwrite your existing config, including any real API keys you've stored in MCP server fields.

```bash
# 1. Make sure the config folders exist
mkdir -p ~/.config/opencode/agents

# 2. The main config file
cp opencode.template.json ~/.config/opencode/opencode.json

# 3. ALL agents go in the SAME folder — "agents" (plural).
#    The Supervisor (a primary agent) and every subagent live together here.
cp agent/supervisor.md ~/.config/opencode/agents/supervisor.md
cp agents/*.md   ~/.config/opencode/agents/

# 4. The Observer plugin (lets you paste screenshots into chat)
cp plugin/observer-bridge.js ~/.config/opencode/observer-bridge.js

# 5. Behavioral guidelines (coding conventions for the agents)
cp AGENTS.md ~/.config/opencode/AGENTS.md
```

> 🪟 **On Windows?** Use these PowerShell equivalents instead:
> ```powershell
> # ~/.config/opencode/ → %USERPROFILE%\.config\opencode\
> mkdir $env:USERPROFILE\.config\opencode\agents
> 
> copy opencode.template.json $env:USERPROFILE\.config\opencode\opencode.json
> copy agent\supervisor.md $env:USERPROFILE\.config\opencode\agents\supervisor.md
> copy agents\*.md $env:USERPROFILE\.config\opencode\agents\
> copy plugin\observer-bridge.js $env:USERPROFILE\.config\opencode\observer-bridge.js
> copy AGENTS.md $env:USERPROFILE\.config\opencode\AGENTS.md
> ```
> (`mkdir` in PowerShell creates parent directories automatically — no `-p` flag needed. `copy` replaces `cp`.)

> 🪤 **The #1 beginner footgun — one folder, and it's plural.**
> *Every* agent — the Supervisor **and** the 40 subagents — goes in `~/.config/opencode/agents/` (**plural**). What makes the Supervisor "primary" is the `mode: primary` line inside `supervisor.md`, **not** a separate folder. OpenCode does **not** read a singular `agent/` folder, so if you put `supervisor.md` there, it silently won't load and the Supervisor won't show up. Keep everything in `agents/`.

> 📌 **Already have an OpenCode config?** Don't overwrite your existing `opencode.json`! The agents, plugin, and AGENTS.md are safe to add — they won't clash with anything. The `opencode.json` template is optional; it only adds MCP servers and permissions.

---

## 🟢 Step 4 — Connect your key (no editing files)

**For CLI users:** You **don't** paste your key into any config file. Instead, let OpenCode store it securely using its built-in login. In your terminal, run:

```bash
opencode auth login
```

You'll get a menu of providers. Then:

1. Choose **DeepSeek**. (If DeepSeek isn't in the list, choose **Other**, and type `deepseek` as the provider id.)
2. Paste the `sk-...` key from Step 2 and press Enter.

That's it. OpenCode saves the key in its own secure store (`~/.local/share/opencode/auth.json`) — **not** in this repo's `opencode.template.json`, so there's no risk of committing it to GitHub. The provider blocks in `opencode.json` just tell OpenCode which models exist; the key comes from your login.

> 💡 **Prefer environment variables?** That works too — set `DEEPSEEK_API_KEY` (and later `ANTHROPIC_API_KEY`) in your shell and OpenCode will pick them up. Use whichever you like; you don't need both.

> 🖥️ **Using OpenCode Desktop?** Skip the CLI commands above. In OpenCode Desktop, go to **Settings → Providers**, click **DeepSeek**, and paste your API key there. Same workflow for any other provider — Settings → Providers → click the provider → paste the key.

**Where to get keys for all supported providers:**

| Provider | Sign-up / key page | Models powered |
|----------|-------------------|----------------|
| **DeepSeek** | [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys) | All junior-tier agents (Supervisor, workers, architects, etc.) |
| **Anthropic (Claude)** | [console.anthropic.com](https://console.anthropic.com) | Mid + senior tiers, Observer vision agent |
| **xAI (Grok)** | [console.x.ai](https://console.x.ai) | Optional `grok-worker` addon |
| **Google (Gemini)** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Optional `gemini-worker` addon |

> 💰 Only the DeepSeek key is required to start. Anthropic unlocks the full 3-tier system. The others are optional addons — ignore them until you want them.

**Checkpoint:** Run `opencode auth list` — you should see `deepseek` listed. ✅

---

## 🟢 Step 5 — Launch it

```bash
opencode
```

When OpenCode opens, look for the agent selector (often via the `Tab` key or a menu) and choose **Supervisor**. You're now talking to your project manager.

> 🛠️ **"Model not found" error on launch?** OpenCode usually auto-installs the model package, but if it complains, run this once inside the config folder:
> ```bash
> cd ~/.config/opencode && npm install @ai-sdk/deepseek
> ```

---

## 🎉 Step 6 — Your first task (the "hero" moment)

Type any of these to the Supervisor and watch it delegate:

```
"Review this project and tell me what needs work"
"Build a small command-line to-do app in Python"
"Fix the login bug"
"Research the best way to structure a REST API and write up the options"
```

What you'll see: the Supervisor states a plan, spawns one or more specialists, reviews their output, and reports back — all on its own. **That's it. You're up and running.** 🏆

---

## 🧱 Step 7 — Add Claude to complete the system (mid + senior tiers + Observer)

This is part of the core setup, not a bolt-on. The **full 3-tier system ships in the repo** — all 40 agent files are already on your machine. DeepSeek powers the junior tier (and handles ~80% of work on its own), and an **Anthropic (Claude)** key switches on the other two tiers **plus Observer's screenshot vision**. You *can* run DeepSeek-only as a budget minimum, but the system is designed to run on both keys.

**How the three tiers work — it's just naming:**

| You ask for… | Agent used | Model | Powered by |
|--------------|-----------|-------|------------|
| (automatic / "the junior worker") | `junior-worker` | DeepSeek V4 Pro | Your DeepSeek key |
| "send this to the worker / architect" | `worker`, `architect` | Claude Sonnet 4.6 | Anthropic key |
| "use the **senior** reviewer" | `senior-reviewer` | Claude Opus 4.8 | Anthropic key |

The Claude-powered agents (and Observer) sit ready but inactive until the key is present — nothing else to configure.

**To switch them on:**

1. Get a key at **[console.anthropic.com](https://console.anthropic.com)** (same idea as DeepSeek — sign up, add a little credit, create a key starting with `sk-ant-...`).
2. Connect it the same native way — no file editing:
   ```bash
   opencode auth login
   ```
   Choose **Anthropic** and paste your `sk-ant-...` key. (Or set `ANTHROPIC_API_KEY` in your environment.)
3. Restart OpenCode. Now you can say *"use the senior architect for this,"* and you can **paste a screenshot** straight into chat — Observer reads it (see below).

> 💰 **Heads up on cost.** Claude (especially Opus/"senior") is **much** pricier than DeepSeek. Use junior agents by default; call in the seniors only when it really matters. The Supervisor already follows this policy automatically.

> 💸 **Built-in saver.** The config sets a `small_model` (DeepSeek) so cheap background chores — naming conversations, short summaries — never run on an expensive model.

### 👁️ Observer — paste screenshots into chat (built in)

Your Supervisor runs on a text-only model, so it can't see images. **Observer** fixes that: it's a Claude vision agent that ships with the repo (you already copied it in Step 3). Paste a screenshot of an error, a UI bug, or a design mockup directly into the chat, and Observer reads it — extracting the text, locating the problem, and handing the Supervisor a description it can act on.

It activates automatically once your Anthropic key is in place (it runs on Claude Sonnet 4.6). No model names to wire up — Observer activates automatically when an Anthropic key is present (added via Desktop Settings or CLI), no provider block needed. Pair it with `screenpipe` or `macos-automator` (Step 8) and the Supervisor can capture *and* understand on-screen state.

---

## 🌐 Optional Step 8 — Other expansions

These are extras you can ignore until you want them:

- **Grok (xAI)** — an optional `grok-worker` addon adds an alternative-model worker on Grok 4.3. Add an xAI key through Desktop Settings → Providers (or `opencode auth login`), then copy one file. No provider block needed — see PROVIDERS.md. See [`addons/grok-worker/`](addons/grok-worker/). No auth plugin needed.
- **Addons** (`addons/` folder) — behavioral "modes," the Grok worker, and a full reference catalog. See [`addons/README.md`](addons/README.md).
- **CLI quality tools** — the reviewer/debugger agents can use tools like `ruff`, `mypy`, and `trivy` when present. Optional but nice. See [`DEPENDENCIES.md`](DEPENDENCIES.md).

### Optional MCP servers (nice-to-haves)

The config ships with two browser/automation tools **already enabled** and ready — no setup, no keys:

- **`playwright`** — lets agents drive a real browser (clicks, forms, login flows).
- **`chrome-devtools`** — inspect pages, console, and network for debugging web apps.

It also includes seven **optional** MCP servers that are **disabled by default**. Most need a key, an app, or an extra install, so you turn them on only if you want them:

| MCP | What it adds | To enable |
|-----|--------------|-----------|
| **`firecrawl`** | Web scraping + search for JS-heavy pages | Get a free key at [firecrawl.dev](https://firecrawl.dev), paste it into `YOUR_FIRECRAWL_KEY` |
| **`elevenlabs`** | Text-to-speech / voice generation | Get a key at [elevenlabs.io](https://elevenlabs.io), paste it into `YOUR_ELEVENLABS_KEY`; needs [`uv`](https://docs.astral.sh/uv/) installed |
| **`railway`** | Deploy & manage apps on Railway | Install the [Railway CLI](https://docs.railway.com/guides/cli) and run `railway login` |
| **`screenpipe`** | Searches your 24/7 screen + audio history ("what was on screen at 2pm?") | Install & run the [screenpipe](https://screenpi.pe) app (records locally, stays on your machine). Works on macOS, Windows, and Linux. |
| **`macos-automator`** | Lets agents control native **macOS** apps via AppleScript/JXA — open apps, click buttons, read Mail/Safari, toggle settings | macOS only. Needs Node 24+ and Automation/Accessibility permission (System Settings → Privacy & Security). |
| **`context7`** | Live, version-accurate library/API docs so coding agents aren't guessing from old memory | Just flip it on — works keyless. (Optional free key at [context7.com](https://context7.com) for higher rate limits.) |
| **`github`** | Manage GitHub issues, PRs, and repos directly | Needs [Docker](https://www.docker.com) installed and a [GitHub token](https://github.com/settings/tokens) in `YOUR_GITHUB_TOKEN`. |

> 🪟 **On Windows?** `macos-automator` is macOS-only. For equivalent native desktop control on Windows, use **[CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP)** — follow that repo's setup, then add it to your `"mcp"` block the same way (disabled until you opt in). `screenpipe` already works on Windows.

> 🧠 **Pairs well with Observer.** `screenpipe` and `macos-automator` capture what's on screen; the built-in **Observer** agent (a Claude vision agent — see Step 7) then *reads* those screenshots and explains them to your text-only Supervisor.

**How to turn one on** (the "permissions" part): in `opencode.json`, find the server under `"mcp"` and change `"enabled": false` to `"enabled": true`, then in the `"permission"` block change that server's line from `"deny"` to `"allow"`. For example, to enable Firecrawl:

```json
"mcp": { "firecrawl": { "enabled": true, ... } },
"permission": { "firecrawl_*": "allow" }
```

> 💡 **Why disabled + denied by default?** It's the safe starting point — nothing runs or spends money until you opt in. The Supervisor works perfectly without any of these.

---

## 🆘 Troubleshooting — the usual suspects

| Symptom | Most likely cause | Fix |
|---------|------------------|-----|
| **Supervisor doesn't appear** | `supervisor.md` in the wrong folder, or missing `mode: primary` | Confirm it's in `~/.config/opencode/agents/` (**plural**) with `ls ~/.config/opencode/agents/supervisor.md`, and that its frontmatter says `mode: primary`. There is no singular `agent/` folder. |
| **A phantom non-agent shows up (e.g. "tier-system-reference")** | A non-agent `.md` landed in the agents folder | Only real agent files belong in `~/.config/opencode/agents/`. Remove any docs: `rm ~/.config/opencode/agents/tier-system-reference.md`. |
| **"Agent not found"** when it tries to delegate | Subagents missing | Run `ls ~/.config/opencode/agents/*.md` — you should see ~29 files. If empty, re-run the copy command in Step 3. |
| **"Insufficient balance"** | $0 credit on your key | Add a few dollars at [platform.deepseek.com](https://platform.deepseek.com). |
| **"Model not found" / API errors** | Provider package missing | `cd ~/.config/opencode && npm install @ai-sdk/deepseek` (OpenCode Desktop usually auto-installs provider packages; this is only needed if you get 'Model not found' errors) |
| **"Invalid API key" / "not authenticated"** | Key not connected, or a typo | Re-run `opencode auth login` and re-enter the key (no extra spaces). Confirm with `opencode auth list` that the provider shows up. |
| **MCP error on startup** (e.g. firecrawl/elevenlabs/railway) | An optional MCP got enabled without its key/install | Harmless to the Supervisor. Either set that server back to `"enabled": false` in `opencode.json`, or finish its setup (see Step 8). |
| **DeepSeek/Claude stopped working after adding config** | A `provider` block in `opencode.json` overrides auth | Remove the `provider` block from your `opencode.json` entirely. The template no longer ships one — if you have one, it's leftover and interfering. |
| **Too many agents in the agent selector** | Non-agent `.md` files or stray files being picked up | Only agent files should be in `agents/`. Remove any docs, notes, or reference files from that folder. The template no longer ships a `provider` block. |
| **Max variant toggle disappeared** | A `provider.models` block stripped built-in model variants | Remove the `provider` block from `opencode.json` — `models.dev` handles variants. |
| **Subagents appear in @ autocomplete** | Agent file missing `hidden: true` in frontmatter | Add `hidden: true` to subagent markdown files. All shipped subagents already have this set — if you created custom ones, add it manually. |

---

## 🗺️ Where to go next

- **[README.md](README.md)** — the full architecture and design philosophy.
- **[tier-system-reference.md](tier-system-reference.md)** — exact specs for all 40 agents.
- **[DEPENDENCIES.md](DEPENDENCIES.md)** — every optional tool, organized by tier.
- **[addons/README.md](addons/README.md)** — modes, local models, and the visual Observer.

<div align="center">

<br>

**You did it.** 🎈 You went from zero to a working AI agent team.

*Stuck on something this guide didn't cover? Open an issue on the repo.*

</div>
