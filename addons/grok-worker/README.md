# Grok Worker — Optional Alternative-Model Worker

A full-access generalist subagent that runs on **xAI's Grok 4.3** instead of DeepSeek/Claude. Use it when you specifically want Grok's model for a task. It's entirely optional and ships **outside** the core agent set so it never auto-loads unless you opt in.

## What it is

`grok-worker.md` is a `mode: subagent` agent with full permissions (edit, bash, web). The only thing that makes it "Grok" is its frontmatter line `model: xai/grok-4.3`.

## Setup (3 steps)

### 1. Add an xAI provider to your `opencode.json`

No auth plugin is needed — just a provider block with your key:

```json
"provider": {
  "xai": {
    "npm": "@ai-sdk/xai",
    "name": "xAI (Grok)",
    "options": { "apiKey": "YOUR_XAI_API_KEY" },
    "models": {
      "grok-4.3": { "name": "Grok 4.3", "tools": true }
    }
  }
}
```

Get a key at [console.x.ai](https://console.x.ai).

### 2. Copy the agent into your agents folder

```bash
cp addons/grok-worker/grok-worker.md ~/.config/opencode/agents/grok-worker.md
```

(Same folder as every other agent — see the main guide.)

### 3. Restart OpenCode

Now you can say *"send this to the grok-worker"* and the Supervisor will spawn Grok.

## Cost

You pay xAI directly for Grok usage. Use it deliberately — DeepSeek (junior) and Claude (mid/senior) cover almost everything.
