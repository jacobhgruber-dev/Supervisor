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
| Anthropic | https://console.anthropic.com | $5 credit recommended; lights up mid/senior tiers + Observer |
| Google (Gemini) | https://aistudio.google.com/apikey | Free tier available |
| xAI (Grok) | https://console.x.ai | Powers optional grok-worker addon |

DeepSeek alone runs the supervisor + junior tier. Adding Anthropic enables the mid/senior tiers and Observer. Google and xAI are optional add-ons.

## Connecting Your API Keys (CLI)

If you're using the CLI (`opencode auth login`), the flow is the same:

```bash
opencode auth login   # choose DeepSeek, paste your key
opencode auth login   # run again, choose Anthropic, paste your key
```

Keys are stored in `~/.local/share/opencode/auth.json`, not in this config file. No `provider` block needed.

> Prefer env vars? `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`, and `XAI_API_KEY` are read automatically.

## Warning: The `provider` Block

**Do not add a `provider` block for DeepSeek, Anthropic, Google, or xAI.** OpenCode has built-in provider implementations for all four. Adding a `provider` block has two dangerous side effects:

1. **`npm` + `models` fields override the internal implementation.** A `provider` block that specifies `npm` and `models` fully replaces OpenCode's built-in provider wiring. Previously-working providers can stop working entirely.

2. **`provider.models` replaces, not merges.** Any model you list in `provider.models` replaces the models.dev definition for that model ID. This strips built-in variants — for example, the DeepSeek "Max" toggle disappears if you define `deepseek/deepseek-v4-pro` in a custom `provider.models` block.

**The `provider` block is only for custom providers** — local models (Ollama, LM Studio), proxies, or custom endpoints that OpenCode doesn't know about natively. The template already includes Ollama. Do not add cloud providers (DeepSeek, Anthropic, Google, xAI) here — use Desktop auth or env vars instead.

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

Browser/automation tools, run via `npx` on first use:

- **`playwright`** — drive a real browser (clicks, forms, login, screenshots)
- **`chrome-devtools`** — inspect pages, console messages, network requests, performance traces

### Disabled by default

Each needs a key or extra install. To enable one, set `"enabled": true` in the `mcp` block **and** flip its line in the `permission` block from `"deny"` to `"allow"`:

| MCP | Adds | Setup |
|-----|------|-------|
| `elevenlabs` | Text-to-speech / voice | Key from https://elevenlabs.io; needs `uv` (`uvx`) |
| `railway` | Deploy & manage apps | Railway CLI + `railway login` |
| `screenpipe` | Search 24/7 screen + audio history | Run the screenpipe app (https://screenpi.pe); cross-platform |
| `macos-automator` | Control native macOS apps (AppleScript/JXA) | macOS only; Node 24+, Automation + Accessibility permission |
| `context7` | Live, version-accurate library/API docs | Works keyless; optional key from https://context7.com |
| `github` | Manage GitHub issues, PRs, repos | Docker + GitHub token in `GITHUB_PERSONAL_ACCESS_TOKEN` |

> **Windows note:** `macos-automator` is macOS-only. For native Windows control, use [CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP) and add it to `"mcp"` the same opt-in way. `screenpipe` works on Windows.



## Permission Block

The `permission` block controls which MCP tools agents are allowed to call. Each disabled MCP has a corresponding `"deny"` entry. To enable a disabled MCP, you need **both** changes:

1. Set `"enabled": true` inside that MCP's entry in the `mcp` block
2. Change its permission from `"deny"` to `"allow"` in the `permission` block

Skipping either step leaves the MCP unavailable. Reverse the steps to disable a built-in MCP (set `enabled: false` + `deny`).

## Adding Agent Files

Once your `opencode.json` is in place, copy the agent files to your opencode config. **All markdown agents — the primary supervisor and every subagent — go in the same `agents/` (plural) folder.** OpenCode does not read a singular `agent/` folder; `mode: primary` inside `supervisor.md` is what makes it the primary agent.

**macOS/Linux:**
```
mkdir -p ~/.config/opencode/agents
cp agent/supervisor.md ~/.config/opencode/agents/supervisor.md
cp agents/*.md   ~/.config/opencode/agents/
cp plugin/*.js   ~/.config/opencode/
cp AGENTS.md     ~/.config/opencode/AGENTS.md
```

**Windows (PowerShell):**
```
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\agents"
Copy-Item agent\supervisor.md -Destination "$env:USERPROFILE\.config\opencode\agents\supervisor.md"
Copy-Item agents\*.md    -Destination "$env:USERPROFILE\.config\opencode\agents\"
Copy-Item plugin\*.js    -Destination "$env:USERPROFILE\.config\opencode\"
Copy-Item AGENTS.md      -Destination "$env:USERPROFILE\.config\opencode\AGENTS.md"
```

## Restart and Verify

Restart opencode. Check that everything is wired up correctly:

1. **Supervisor is the default agent** — when opencode starts, the agent selector should show "supervisor" as the active primary agent (not "general" or any other agent).
2. **Clean agent selector** — you should see your configured agents in the dropdown. No missing providers, no broken model listings.
3. **Provider check (Desktop)** — open Settings → Providers. Providers you configured through the UI should show as connected. If you added a `provider` block by mistake and providers are broken, remove it and restart.
4. **Model variants (Desktop)** — if you added DeepSeek through Settings, the "Max" toggle should appear in the model selector. If it's missing, you may have a `provider.models` block overriding the built-in definition — remove it.

If something is wrong, double-check that your `opencode.json` has **no `provider` block** and that you added keys through Settings or `opencode auth login`, not by editing the config file directly.
