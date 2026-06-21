# opencode.json — Setup Instructions

This file is the template for your opencode configuration. Copy `opencode.json` to your opencode config directory:

**macOS/Linux:**
```
cp opencode.json ~/.config/opencode/opencode.json
```

**Windows:**
```
copy opencode.json %APPDATA%\opencode\opencode.json
```

## Connecting Your Keys (no keys in this file)

The shipped config already defines the **DeepSeek** and **Anthropic** providers (model names only — no API keys). You connect keys natively with OpenCode's login, which stores them in `~/.local/share/opencode/auth.json`, not in this repo:

```bash
opencode auth login   # choose DeepSeek, paste your key
opencode auth login   # run again, choose Anthropic, paste your key
```

- DeepSeek key: https://platform.deepseek.com/api_keys (if DeepSeek isn't in the menu, choose **Other** → id `deepseek`)
- Anthropic key: https://console.anthropic.com
- Prefer env vars? `DEEPSEEK_API_KEY` and `ANTHROPIC_API_KEY` are read automatically.

DeepSeek alone runs the supervisor + junior tier. Adding Anthropic lights up the mid/senior tiers and Observer.

## Optional Providers

### xAI (Grok) — for the optional grok-worker addon

Add this provider block if you use the [grok-worker addon](addons/grok-worker/), then connect the key with `opencode auth login` (choose xAI) or the `XAI_API_KEY` env var — same native flow, no key in the file:

```json
"xai": {
  "npm": "@ai-sdk/xai",
  "name": "xAI (Grok)",
  "models": {
    "grok-4.3": {
      "name": "Grok 4.3",
      "tools": true
    }
  }
}
```

Get key: https://console.x.ai

## MCP Servers

The `mcp` block gives agents extra capabilities. The config ships with two enabled (no keys needed) and three optional ones disabled by default.

**Enabled by default** — browser/automation tools, run via `npx` on first use:

- `playwright` — drive a real browser (clicks, forms, login)
- `chrome-devtools` — inspect pages, console, and network

**Optional (disabled by default)** — each needs a key or extra install. To use one, set `"enabled": true` **and** flip its line in the top-level `"permission"` block from `"deny"` to `"allow"`:

| MCP | Adds | Setup |
|-----|------|-------|
| `firecrawl` | Web scraping + search | Key from https://firecrawl.dev |
| `elevenlabs` | Text-to-speech / voice | Key from https://elevenlabs.io; needs `uv` |
| `railway` | Deploy & manage apps | Railway CLI + `railway login` |
| `screenpipe` | Search 24/7 screen + audio history | Run the screenpipe app (https://screenpi.pe); cross-platform |
| `macos-automator` | Control native macOS apps (AppleScript/JXA) | macOS only; Node 24+, Automation + Accessibility permission |
| `context7` | Live, version-accurate library/API docs | Works keyless; optional key from https://context7.com |
| `github` | Manage GitHub issues, PRs, repos | Docker + GitHub token in `YOUR_GITHUB_TOKEN` |

> **Windows:** `macos-automator` is macOS-only. For native Windows control, use [CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP) and add it to `"mcp"` the same opt-in way. `screenpipe` works on Windows too.

Example — enabling Firecrawl:

```json
"mcp": {
  "firecrawl": {
    "type": "local",
    "command": ["npx", "-y", "firecrawl-mcp"],
    "enabled": true,
    "environment": { "FIRECRAWL_API_KEY": "YOUR_FIRECRAWL_KEY" }
  }
},
"permission": {
  "firecrawl_*": "allow"
}
```

## Adding Agent Files

Once your opencode.json is configured, copy the agent files to your opencode config. **All markdown agents — the primary supervisor and every subagent — go in the same `agents/` (plural) folder.** OpenCode does not read a singular `agent/` folder; `mode: primary` inside `supervisor.md` is what makes it the primary agent.

```
mkdir -p ~/.config/opencode/agents ~/.config/opencode/plugin
cp supervisor.md ~/.config/opencode/agents/supervisor.md
cp agents/*.md   ~/.config/opencode/agents/
cp plugin/*.js   ~/.config/opencode/plugin/
cp AGENTS.md     ~/.config/opencode/AGENTS.md
```

Restart opencode — the supervisor will appear as your primary agent option.
