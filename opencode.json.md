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
    "claude-sonnet-4-6-20250514": {
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

## MCP Servers (optional)

Add MCP servers under the `mcp` key for extended capabilities:

```json
"mcp": {
  "firecrawl": {
    "type": "local",
    "command": ["npx", "-y", "firecrawl-mcp"],
    "enabled": true,
    "env": {
      "FIRECRAWL_API_KEY": "YOUR_FIRECRAWL_KEY"
    }
  }
}
```

Get key: https://firecrawl.dev

## Adding Agent Files

Once your opencode.json is configured, copy the agent files to your opencode config:

```
cp supervisor.md ~/.config/opencode/agent/supervisor.md
cp agents/*.md ~/.config/opencode/agents/
cp AGENTS.md ~/.config/opencode/AGENTS.md
```

Restart opencode — the supervisor will appear as your primary agent option.
