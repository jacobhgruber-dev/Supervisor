# opencode.template.json — Setup Instructions

This file is the template for your opencode configuration. It ships with an Ollama provider for local models — no cloud provider keys are needed in the config. Add DeepSeek, Anthropic, Google, and xAI through OpenCode Desktop's UI or `opencode auth login` instead. Copy `opencode.template.json` to your opencode config directory:

**macOS/Linux:**
```
cp opencode.template.json ~/.config/opencode/opencode.json
```

**Windows:**
```
copy opencode.template.json %USERPROFILE%\.config\opencode\opencode.json
```

## Connecting Your API Keys (Desktop — Recommended)

If you're on OpenCode Desktop, you do **not** need a `provider` block in `opencode.json`. Add keys through the UI:

1. Open Settings → Providers
2. Click the provider name
3. Paste your API key

Once a provider is configured this way, OpenCode handles everything internally — model listing, tool support, variants (like DeepSeek's Max toggle) — through `auth.json` and models.dev auto-discovery.

**Where to get keys:**

| Provider | Key URL | Notes |
|----------|---------|-------|
| DeepSeek | https://platform.deepseek.com/api_keys | $2 new-user credit; extremely cheap |
| Anthropic | https://console.anthropic.com | $5 credit recommended; lights up mid/senior tiers |
| Google (Gemini) | https://aistudio.google.com/apikey | Free tier available; lights up Observer + Gemini workers |
| xAI (Grok) | https://console.x.ai | Powers optional grok-worker addon + designer / designer-mule |

DeepSeek alone runs the supervisor + junior tier. Adding Anthropic enables the mid/senior tiers. Google enables Observer. xAI is an optional add-on.

## Connecting Your API Keys (CLI)

If you're using the CLI (`opencode auth login`), the flow is the same:

```bash
opencode auth login   # choose DeepSeek, paste your key
opencode auth login   # run again, choose Anthropic, paste your key
```

Keys are stored in `~/.local/share/opencode/auth.json`, not in this config file. No `provider` block needed.

> Prefer env vars? `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`, and `XAI_API_KEY` are read automatically.

## Warning: The `provider` Block

**You don't need a `provider` block for DeepSeek, Anthropic, Google, or xAI — connect them natively.** OpenCode has built-in provider implementations for all four (via models.dev), and a config `provider` block is **deep-merged** into that built-in definition — it never removes the credentials stored in `auth.json`. The real risks of adding a cloud-provider block:

1. **`options.apiKey` shadows your stored key** — a block that sets `options.apiKey` takes precedence over the key you saved through Desktop/auth login, and requests can fail authentication.
2. **`options.baseURL` overrides the endpoint** — pointing at the wrong URL breaks calls entirely.
3. **`blacklist`/`whitelist` hide models** — anything listed there disappears from the model selector, variants included.

For reference, `npm` and `models` do **not** replace the built-in wiring: provider-level `npm` is only a per-model fallback, and `models` entries merge per-field with fallbacks to the models.dev definition — a partial entry preserves built-in fields.

**A `provider` block is required for custom providers** — local models (Ollama, LM Studio), proxies, or custom endpoints that OpenCode doesn't know about natively — and it's the legitimate way to intentionally customize a built-in (e.g. a `baseURL` override). The template already includes Ollama. For the four cloud providers, use Desktop auth or env vars instead.

## What's in This Config File

The shipped `opencode.template.json` contains only an Ollama provider for local models. It defines:

| Field | Value | What it does |
|-------|-------|--------------|
| `model` | `deepseek/deepseek-v4-pro` | Primary model for the supervisor and subagents |
| `default_agent` | `supervisor` | Makes Supervisor the default agent on startup |
| `subagent_depth` | `3` | How many levels deep subagents can spawn subagents. 1 = only supervisor can spawn. 3 = supervisor → subagent → mule chains work. |
| `mcp` | *(see below)* | MCP server definitions (tools available to agents) |
| `permission` | *(see below)* | Tool permission rules for each MCP |

## MCP Servers

The `mcp` block gives agents extra capabilities. One is enabled by default; the rest are disabled.

### Enabled by default

Browser/automation tool, run via `npx` on first use:

- **`playwright`** — drive a real browser (clicks, forms, login, screenshots)

### Disabled by default

Each needs a key or extra install. To enable one, set `"enabled": true` in the `mcp` block. For servers not already in the `permission` block, add a corresponding `"<name>_*": "allow"` entry:

| MCP | Adds | Setup |
|-----|------|-------|
| `chrome-devtools` | Inspect pages, console, network, performance traces | Just flip `"enabled": true` — already pre-allowed in the `permission` block |
| `elevenlabs` | Text-to-speech / voice | Key from https://elevenlabs.io; needs `uv` (`uvx`) |
| `railway` | Deploy & manage apps | Railway CLI + `railway login` |
| `screenpipe` | Search 24/7 screen + audio history | Run the screenpipe app (https://screenpi.pe); cross-platform |
| `macos-automator` | Control native macOS apps (AppleScript/JXA) | macOS only; Node 24+, Automation + Accessibility permission |
| `yt-dlp` | Download audio/video for transcription | `brew install yt-dlp` or `pip install yt-dlp` |
| `vercel` | Deploy & manage apps on Vercel | Vercel token — already pre-allowed in the `permission` block |
| `gemini-api-docs` | Live Gemini API docs lookup | Needs `uv`; works keyless |
| `context7` | Live, version-accurate library/API docs | Works keyless; optional key from https://context7.com |
| `github` | Manage GitHub issues, PRs, repos | Docker + GitHub token in `GITHUB_PERSONAL_ACCESS_TOKEN` |
| `macos-use` | Native macOS GUI control | macOS only; binary at `/usr/local/bin` — already pre-allowed in `permission` block |
| `twenty-first` | 21st.dev component search/retrieval for UI work | Flip `"enabled": true`; **design MCP gating** — denied globally and for supervisor; allowed only on the `designer` agent |
| `a11y-color-contrast` | WCAG color-contrast checks | Flip `"enabled": true`; allowed globally (and on `designer`) |

> **Windows note:** `macos-automator` is macOS-only. For native Windows control, use [CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP) and add it to `"mcp"` the same opt-in way. `screenpipe` works on Windows.

> **Design MCP gating:** `twenty-first_*` and `open-design_*` are denied at top-level `permission` and on `agent.supervisor`. The `agent.designer` block allows `twenty-first_*`, `open-design_*`, and `a11y-color-contrast_*`. The template does not ship an `open-design` MCP server definition (it is path-local); add your own server entry if you use open-design, and keep the permission keys.

## Permission Block

The `permission` block controls which MCP tools agents are allowed to call. The template pre-approves three servers (`chrome-devtools`, `macos-use`, `vercel`) with `"allow"` entries, plus `a11y-color-contrast_*`. Design tools (`twenty-first_*`, `open-design_*`) are explicitly `"deny"` at the top level and for the supervisor — only the `designer` agent is allowed them. All other disabled MCPs have no entry in the `permission` block — to enable one, you need **both** changes:

1. Set `"enabled": true` inside that MCP's entry in the `mcp` block
2. Add a corresponding `"<name>_*": "allow"` entry to the `permission` block (or rely on agent-scoped allow for gated design tools)

Skipping either step leaves the MCP unavailable. Reverse the steps to disable a built-in MCP (set `enabled: false` and remove its permission entry).

## Adding Agent Files

Once your `opencode.json` is in place, copy the agent files to your opencode config. OpenCode loads agent markdown from both `agent/` and `agents/` (`{agent,agents}/**/*.md`). This install puts the Supervisor in `agent/` and subagents in `agents/`. `mode: primary` inside `supervisor.md` is what makes it the primary agent.

**macOS/Linux:**
```
mkdir -p ~/.config/opencode/agent ~/.config/opencode/agents
cp agent/supervisor.md ~/.config/opencode/agent/supervisor.md
cp agents/*.md         ~/.config/opencode/agents/
cp plugin/*.js         ~/.config/opencode/
cp AGENTS.md           ~/.config/opencode/AGENTS.md
```

**Windows (PowerShell):**
```
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\agent"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\agents"
Copy-Item agent\supervisor.md -Destination "$env:USERPROFILE\.config\opencode\agent\supervisor.md"
Copy-Item agents\*.md    -Destination "$env:USERPROFILE\.config\opencode\agents\"
Copy-Item plugin\*.js    -Destination "$env:USERPROFILE\.config\opencode\"
Copy-Item AGENTS.md      -Destination "$env:USERPROFILE\.config\opencode\AGENTS.md"
```

## Restart and Verify

Restart opencode. Check that everything is wired up correctly:

1. **Supervisor is the default agent** — when opencode starts, the agent selector should show "supervisor" as the active primary agent (not "general" or any other agent).
2. **Clean agent selector** — you should see your configured agents in the dropdown. No missing providers, no broken model listings.
3. **Provider check (Desktop)** — open Settings → Providers. Providers you configured through the UI should show as connected. If you added a **cloud** `provider` block (DeepSeek/Anthropic/Google/xAI) with `options.apiKey` or `options.baseURL` overrides, remove those overrides (or the whole block — you don't need it) and restart. The template's Ollama-only `provider` entry is fine to keep for local models.
4. **Model variants (Desktop)** — if you added DeepSeek through Settings, the "Max" toggle should appear in the model selector. If it's missing, you may have `blacklist`/`whitelist` entries in a cloud `provider` block hiding it — remove them. Partial `provider.models` entries merge with the built-in definition, so they don't strip variants on their own.
5. **`subagent_depth`** — confirm `"subagent_depth": 3` is present so supervisor → subagent → mule chains work.

If something is wrong, double-check that your `opencode.json` has **no cloud `provider` blocks** (DeepSeek/Anthropic/Google/xAI) and that you added those keys through Settings or `opencode auth login`, not by editing the config file directly.
