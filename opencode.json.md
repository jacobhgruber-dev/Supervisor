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

## Required: DeepSeek API Key

1. Get your API key at: https://platform.deepseek.com/api_keys
2. Replace `YOUR_DEEPSEEK_API_KEY` in the provider section with your actual key
3. The supervisor agent and all subagents run on DeepSeek V4 Pro Max — you only need this one key to get started

## Optional Providers

Want to add other models? Add their provider blocks to the `provider` section:

### Anthropic (Claude)
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
    }
  }
}
```

Get key: https://console.anthropic.com

### xAI (Grok)
```json
"xai": {
  "npm": "@ai-sdk/xai",
  "name": "xAI (Grok)",
  "options": {
    "apiKey": "YOUR_XAI_API_KEY"
  },
  "models": {
    "grok-4.3": {
      "name": "Grok 4.3",
      "tools": true
    }
  }
}
```

Get key: https://console.x.ai

### Ollama (Local)
```json
"ollama": {
  "npm": "@ai-sdk/openai-compatible",
  "name": "Ollama (local)",
  "options": {
    "baseURL": "http://localhost:11434/v1"
  },
  "models": {
    "qwen3.6:27b": {
      "tools": true,
      "name": "Qwen 3.6 27B"
    }
  }
}
```

Install: https://ollama.com

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

Once your opencode.json is configured, copy the agent files to your opencode config:

```
cp supervisor.md ~/.config/opencode/agent/supervisor.md
cp agents/*.md ~/.config/opencode/agents/
cp AGENTS.md ~/.config/opencode/AGENTS.md
```

Restart opencode — the supervisor will appear as your primary agent option.
