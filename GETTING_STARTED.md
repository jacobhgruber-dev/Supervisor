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

### ⚡ Fastest path — the one-line installer (recommended)

Run one command and you're done. The installer copies the Supervisor, all 47 subagents, the 22 bundled skills, the Observer plugin, and AGENTS.md into place — and it safely **merges** the config instead of overwriting it (your existing `opencode.json` is backed up first, and your settings always win):

| Platform | Install | Update later |
|----------|---------|--------------|
| **macOS / Linux** | `./install.sh` | `./update.sh` |
| **Windows (PowerShell)** | `.\setup.ps1` | `.\update.ps1` |

> 🩺 **Dependency Doctor.** Not sure what else your machine needs? Run `./install.sh --doctor` — it scans your system against the repo's dependency manifest and prints a tailored install command for every missing tool. It never fails and writes nothing. Re-run it any time.

> ✅ **Checkpoint:** You should see lines like `copied agent/supervisor.md, 47 agents/*.md, skills/...` and `Verification passed.`

### Manual method (reference)

Prefer to do it by hand? The manual copy below does exactly what the installer does, one file at a time:

> ⚠️ **Already configured providers in Desktop or have custom settings in your opencode.json?** Skip the template copy — just copy the agent files, plugin, and AGENTS.md. The template WILL overwrite your existing config, including any real API keys you've stored in MCP server fields.

```bash
# 1. Make sure the config folders exist
mkdir -p ~/.config/opencode/agent ~/.config/opencode/agents

# 2. The main config file
cp opencode.template.json ~/.config/opencode/opencode.json

# 3. Supervisor → agent/ ; subagents → agents/
cp agent/supervisor.md ~/.config/opencode/agent/supervisor.md
cp agents/*.md         ~/.config/opencode/agents/

# 4. The Observer plugin (lets you paste screenshots into chat)
cp plugin/observer-bridge.js ~/.config/opencode/observer-bridge.js

# 5. Behavioral guidelines (coding conventions for the agents)
cp AGENTS.md ~/.config/opencode/AGENTS.md
```

> 🪟 **On Windows?** The one-liner is `.\setup.ps1` (and `.\update.ps1` for updates). Or use these PowerShell equivalents of the manual copy:
> ```powershell
> # ~/.config/opencode/ → %USERPROFILE%\.config\opencode\
> mkdir $env:USERPROFILE\.config\opencode\agent
> mkdir $env:USERPROFILE\.config\opencode\agents
>
> copy opencode.template.json $env:USERPROFILE\.config\opencode\opencode.json
> copy agent\supervisor.md $env:USERPROFILE\.config\opencode\agent\supervisor.md
> copy agents\*.md $env:USERPROFILE\.config\opencode\agents\
> copy plugin\observer-bridge.js $env:USERPROFILE\.config\opencode\observer-bridge.js
> copy AGENTS.md $env:USERPROFILE\.config\opencode\AGENTS.md
> ```
> (`mkdir` in PowerShell creates parent directories automatically — no `-p` flag needed. `copy` replaces `cp`.)

> 📌 **Where agents go.** OpenCode loads agent markdown from both `agent/` and `agents/` (`{agent,agents}/**/*.md`). This install puts the Supervisor in `agent/` and the subagents in `agents/`. What makes the Supervisor primary is `mode: primary` in its frontmatter — not the folder name. Don't drop non-agent docs into either folder (they'll show up as phantom agents).

> 📌 **Already have an OpenCode config?** Don't overwrite your existing `opencode.json`! The agents, plugin, and AGENTS.md are safe to add — they won't clash with anything. The template is optional if you already have a config; if you skip it, merge in at least `"default_agent": "supervisor"` and `"subagent_depth": 3` (required for mule chains).

---

## 🟢 Step 4 — Connect your key (no editing files)

**For CLI users:** You **don't** paste your key into any config file. Instead, let OpenCode store it securely using its built-in login. In your terminal, run:

```bash
opencode auth login
```

You'll get a menu of providers. Then:

1. Choose **DeepSeek** — it's always in the interactive provider list.
2. Paste the `sk-...` key from Step 2 and press Enter.

> 💡 In the OpenCode TUI, the equivalent is the `/connect` command.

That's it. OpenCode saves the key in its own secure store (`~/.local/share/opencode/auth.json`) — **not** in this repo's `opencode.template.json`, so there's no risk of committing it to GitHub. Cloud providers (DeepSeek, Anthropic, Google, xAI) are authenticated this way — do not add them as a `provider` block in `opencode.json`. The template's only `provider` entry is optional Ollama for local models.

> 💡 **Prefer environment variables?** That works too — set `DEEPSEEK_API_KEY` (and later `ANTHROPIC_API_KEY`) in your shell and OpenCode will pick them up. Use whichever you like; you don't need both.

> 🖥️ **Using OpenCode Desktop?** Skip the CLI commands above. In OpenCode Desktop, go to **Settings → Providers**, click **DeepSeek**, and paste your API key there. Same workflow for any other provider — Settings → Providers → click the provider → paste the key.

**Where to get keys for all supported providers:**

| Provider | Sign-up / key page | Models powered |
|----------|-------------------|----------------|
| **DeepSeek** | [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys) | Supervisor + all junior-tier agents + most mules (worker-mule, architect-mule, etc.) |
| **Anthropic (Claude)** | [console.anthropic.com](https://console.anthropic.com) | Mid + senior tiers + claude-mule |
| **Google (Gemini)** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Observer vision agent + gemini-worker + gemini-mule |
| **xAI (Grok)** | [console.x.ai](https://console.x.ai) | grok-worker + grok-mule + designer + designer-mule |

> 💰 Only the DeepSeek key is required to start. Anthropic unlocks the full mid + senior tiers. Google activates the Observer so you can paste screenshots into chat. xAI is optional — ignore it until you want it.

**Checkpoint:** Run `opencode auth list` — you should see `deepseek` listed. ✅

---

## 🟢 Step 5 — Launch it

```bash
opencode
```

When OpenCode opens, look for the agent selector (often via the `Tab` key or a menu) and choose **Supervisor**. You're now talking to your project manager.

> 🛠️ **"Model not found" error on launch?** OpenCode auto-installs its SDK packages itself — DeepSeek is wired via `@ai-sdk/openai-compatible` from models.dev, so no manual `npm install` needed. If the model list looks stale, refresh it:
> ```bash
> opencode models --refresh
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

## 🧱 Step 7 — Add Claude to unlock mid + senior tiers

This is part of the core setup, not a bolt-on. The **full 4-tier system ships in the repo** — all 47 subagent files in `agents/` (48 agents total with the Supervisor primary) are already on your machine. DeepSeek powers the junior tier (and handles ~80% of work on its own), and an **Anthropic (Claude)** key switches on the mid and senior tiers. You *can* run DeepSeek-only as a budget minimum, but the system is designed to run on both keys.

**How the three tiers work — it's just naming:**

| You ask for… | Agent used | Model | Powered by |
|--------------|-----------|-------|------------|
| (automatic / "the junior worker") | `junior-worker` | DeepSeek Flash | Your DeepSeek key |
| "send this to the worker / architect" | `worker`, `architect` | Claude Sonnet 5 | Anthropic key |
| "use the **senior** reviewer" | `senior-reviewer` | Claude Opus 5 | Anthropic key |

The Claude-powered agents sit ready but inactive until the key is present — nothing else to configure.

**To switch them on:**

1. Get a key at **[console.anthropic.com](https://console.anthropic.com)** (same idea as DeepSeek — sign up, add a little credit, create a key starting with `sk-ant-...`).
2. Connect it the same native way — no file editing:
   ```bash
   opencode auth login
   ```
   Choose **Anthropic** and paste your `sk-ant-...` key. (Or set `ANTHROPIC_API_KEY` in your environment.)
3. Restart OpenCode. Now you can say *"use the senior architect for this."* (Screenshot paste / Observer is separate — it needs a **Google (Gemini)** key, or an Anthropic key for the Claude fallback; see Step 8.)

> 💰 **Heads up on cost.** Claude (especially Opus/"senior") is **much** pricier than DeepSeek. Use junior agents by default; call in the seniors only when it really matters. The Supervisor already follows this policy automatically.

> 🪝 **Important config detail: `subagent_depth: 3`.** The template file you copied in Step 3 includes `"subagent_depth": 3`. This is what lets subagents spawn mules — supervisor → subagent → mule chains of depth 3. If you skip the template and write your own `opencode.json`, make sure this field is set to `3` (not the default of `1`, which blocks nested agent spawns).

---

## 🌐 Optional Step 8 — Other expansions

These are extras you can ignore until you want them:

- **Grok (xAI)** — `grok-worker` (Grok 4.5), `grok-mule`, `designer`, and `designer-mule` all ship in `agents/` (Step 3 copied them). Add an xAI key through Desktop Settings → Providers (or `opencode auth login`) to activate them. See [PROVIDERS.md](PROVIDERS.md).
- **Addons** (`addons/` folder) — behavioral "modes," Grok notes, and a full reference catalog. See [`addons/README.md`](addons/README.md).
- **Bundled skills (22)** — 19 motion/design skills (animate, framer-motion, gsap-core, motion-design, design-system, ui-styling, and more) plus 3 utility skills (`agent-reach`, `anna`, `use-railway`) ship in `skills/` and install with everything else. Agents load them automatically when a task matches. See [`skills/README.md`](skills/README.md).
- **CLI quality tools** — the reviewer/debugger agents can use tools like `ruff`, `mypy`, and `trivy` when present. Optional but nice. See [`DEPENDENCIES.md`](DEPENDENCIES.md).

### 👁️ Observer — paste screenshots into chat (built in · dual-provider vision)

Your Supervisor runs on a text-only DeepSeek model, so it can't see images. **Observer** fixes that: it's a vision agent that ships with the repo (you already copied it in Step 3). Paste a screenshot of an error, a UI bug, or a design mockup directly into the chat, and Observer reads it — extracting the text, locating the problem, and handing the Supervisor a description it can act on.

Observer has **dual multimodal vision with zero extra setup**:

- **Primary:** Google **Gemini 3.7 Flash** — activates automatically once your **Google (Gemini)** key is in place (`opencode auth login`, choose Google).
- **Automatic fallback:** if only **Anthropic (Claude)** is configured (no Google key), the Observer plugin switches to **Claude Sonnet 5** — the same structured analysis, either way.

No model names or provider blocks to wire up. Pair it with `screenpipe` or `macos-automator` (below) and the Supervisor can capture *and* understand on-screen state.

### Optional MCP servers (nice-to-haves)

The config ships with two tools **already enabled** and ready — no setup, no keys:

- **`playwright`** — lets agents drive a real browser (clicks, forms, login flows).
- **`a11y-color-contrast`** — WCAG color-contrast checks for design and accessibility work.

It also includes **thirteen optional** MCP servers that are **disabled by default**. Most need a key, an app, or an extra install, so you turn them on only if you want them:

| MCP | What it adds | To enable |
|-----|--------------|-----------|
| **`chrome-devtools`** | Inspect pages, console, and network for debugging web apps | Just flip `"enabled": true` — no key needed, already pre-allowed in the permission block |
| **`elevenlabs`** | Text-to-speech / voice generation | Get a key at [elevenlabs.io](https://elevenlabs.io), paste it into `YOUR_ELEVENLABS_KEY`; needs [`uv`](https://docs.astral.sh/uv/) installed |
| **`railway`** | Deploy & manage apps on Railway | Install the [Railway CLI](https://docs.railway.com/guides/cli) and run `railway login` |
| **`screenpipe`** | Searches your 24/7 screen + audio history ("what was on screen at 2pm?") | Install & run the [screenpipe](https://screenpi.pe) app (records locally, stays on your machine). Works on macOS, Windows, and Linux. |
| **`macos-automator`** | Lets agents control native **macOS** apps via AppleScript/JXA — open apps, click buttons, read Mail/Safari, toggle settings | macOS only. Needs Node 24+ and Automation/Accessibility permission (System Settings → Privacy & Security). |
| **`yt-dlp`** | Download audio/video from YouTube and other sites for transcription/analysis | Needs [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) installed (`brew install yt-dlp` or `pip install yt-dlp`). |
| **`vercel`** | Deploy & manage apps on Vercel | Get a [Vercel token](https://vercel.com/account/tokens), paste it into `YOUR_VERCEL_TOKEN`. Already pre-allowed in the permission block. |
| **`gemini-api-docs`** | Live Gemini API documentation lookup for coding agents | Needs [`uv`](https://docs.astral.sh/uv/) installed. Works keyless. |
| **`context7`** | Live, version-accurate library/API docs so coding agents aren't guessing from old memory | Just flip it on — works keyless. (Optional free key at [context7.com](https://context7.com) for higher rate limits.) |
| **`github`** | Manage GitHub issues, PRs, and repos directly | Needs [Docker](https://www.docker.com) installed and a [GitHub token](https://github.com/settings/tokens) in `YOUR_GITHUB_TOKEN`. |
| **`macos-use`** | Native macOS GUI control — mouse, keyboard, accessibility automation | macOS only. Needs the `mcp-server-macos-use` binary at `/usr/local/bin`. Already pre-allowed in the permission block. |
| `firecrawl` | Optional web scrape/search (JS-heavy pages) | Get a key at firecrawl.dev; set `FIRECRAWL_API_KEY` |
| **`twenty-first`** | UI component search & generation (21st.dev) for design work | Flip `"enabled": true` and change its permission line from `"deny"` to `"allow"`. |

> 🪟 **On Windows?** `macos-automator` is macOS-only. For equivalent native desktop control on Windows, use **[CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP)** — follow that repo's setup, then add it to your `"mcp"` block the same way (disabled until you opt in). `screenpipe` already works on Windows.

> 🧠 **Pairs well with Observer.** `screenpipe` and `macos-automator` capture what's on screen; the built-in **Observer** agent (dual-provider vision — Gemini 3.7 Flash primary, Claude Sonnet 5 fallback — see the Observer section above) then *reads* those screenshots and explains them to your text-only Supervisor.

**How to turn one on** (the "permissions" part): in `opencode.json`, find the server under `"mcp"` and change `"enabled": false` to `"enabled": true`. For a few servers (`chrome-devtools`, `macos-use`, `vercel`), the template already has a matching `"allow"` entry in the `"permission"` block — just flip `enabled`. For the others (elevenlabs, railway, screenpipe, macos-automator, yt-dlp, gemini-api-docs, context7, github), you'll also need to add a corresponding `"<name>_*": "allow"` line to the `"permission"` block. `twenty-first` ships with a `"deny"` permission entry — change it to `"allow"` too. For example, to enable railway:

```json
"mcp": { "railway": { "enabled": true, ... } },
"permission": { "railway_*": "allow" }
```

> 💡 **Why disabled by default?** It's the safe starting point — nothing runs or spends money until you opt in. The Supervisor works perfectly without any of these.

---

## 🆘 Troubleshooting — the usual suspects

| Symptom | Most likely cause | Fix |
|---------|------------------|-----|
| **Supervisor doesn't appear** | `supervisor.md` missing, or missing `mode: primary` | Confirm `ls ~/.config/opencode/agent/supervisor.md` and that its frontmatter says `mode: primary`. Re-run the Step 3 copy commands if the file is missing. |
| **A phantom non-agent shows up (e.g. "tier-system-reference")** | A non-agent `.md` landed in an agent folder | Only real agent files belong in `~/.config/opencode/agent/` or `agents/`. Remove any docs that got copied there by mistake. |
| **"Agent not found"** when it tries to delegate | Subagents missing | Run `ls ~/.config/opencode/agents/*.md` — you should see 47 files. If empty, re-run the copy command in Step 3 (or `./install.sh`). |
| **Subagent can't spawn a mule / "Task tool not available"** | `subagent_depth` too low | The template sets `"subagent_depth": 3`. If you skipped the template or wrote your own config, make sure this field is set to `3` — the default of `1` blocks nested agent spawns (supervisor → subagent → mule). |
| **"Insufficient balance"** | $0 credit on your key | Add a few dollars at [platform.deepseek.com](https://platform.deepseek.com). |
| **"Model not found" / API errors** | Stale model list | Run `opencode models --refresh`. OpenCode auto-installs its SDK packages itself (DeepSeek is wired via `@ai-sdk/openai-compatible`) — no manual `npm install` needed. |
| **"Invalid API key" / "not authenticated"** | Key not connected, or a typo | Re-run `opencode auth login` and re-enter the key (no extra spaces). Confirm with `opencode auth list` that the provider shows up. |
| **MCP error on startup** (e.g. elevenlabs/railway/screenpipe) | An optional MCP got enabled without its key/install | Harmless to the Supervisor. Either set that server back to `"enabled": false` in `opencode.json`, or finish its setup (see Step 8). |
| **DeepSeek/Claude stopped working after adding config** | `options.apiKey` or `options.baseURL` overrides in a cloud `provider` block | Auth is loaded independently — a `provider` block never removes your stored key. Check any block for DeepSeek, Anthropic, Google, or xAI in your `opencode.json` and remove `options.apiKey`/`options.baseURL` overrides (or the whole cloud block — you don't need it). The template's Ollama-only block is fine to keep. |
| **Too many agents in the agent selector** | Non-agent `.md` files or stray files being picked up | Only agent files should be in `agents/`. Remove any docs, notes, or reference files from that folder. |
| **Max variant toggle disappeared** | The model or its variants are hidden by `blacklist`/`whitelist` | Partial `provider.models` entries merge with the built-in definition, so check for `blacklist`/`whitelist` entries hiding the model and remove them. Keep the template's Ollama block if you use local models — `models.dev` handles cloud variants. |
| **Subagents appear in @ autocomplete** | Agent file missing `hidden: true` in frontmatter | Add `hidden: true` to subagent markdown files. All shipped subagents already have this set — if you created custom ones, add it manually. |

---

## 🗺️ Where to go next

- **[README.md](README.md)** — the full architecture and design philosophy.
- **[tier-system-reference.md](tier-system-reference.md)** — exact specs for all 47 subagents in `agents/` (48 agents total with the Supervisor).
- **[DEPENDENCIES.md](DEPENDENCIES.md)** — every optional tool, organized by tier.
- **[skills/README.md](skills/README.md)** — the 22 bundled skills (19 motion/design + 3 utility).
- **[addons/README.md](addons/README.md)** — optional modes and Grok notes (Observer is built-in — see Step 8).

<div align="center">

<br>

**You did it.** 🎈 You went from zero to a working AI agent team.

*Stuck on something this guide didn't cover? Open an issue on the repo.*

</div>
