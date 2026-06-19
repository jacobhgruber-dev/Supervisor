# Addons — Optional Extras

The Supervisor repo ships with everything you need out of the box: one API key, one model, nine specialized subagents. Addons layer on additional capabilities for a more complete setup.

## Available Addons

| Addon | What It Adds | Setup Time |
|-------|-------------|------------|
| [OpenCode Modes](open-code-modes/) | 9 behavioral modes for the main agent — trigger words that change how it thinks (architect, debug, review, etc.) | 1 minute — copy one file |
| [Ollama Local](ollama-local/) | Run models 100% on your device via Ollama — two local subagents (coder + reasoner), no cloud API calls, data stays private | 10 minutes — install Ollama + pull models |
| [Observer](observer/) | Visual understanding for text-only supervisors — a multimodal Claude subagent that reads screenshots, UI states, and error logs. Paste images, get structured text analysis | 2 minutes — copy 2 files + add Anthropic API key |
| [Reference](../reference.md) | Comprehensive catalog of all agents, subagents, modes, commands, and model costs — the complete picture when you have everything | 0 minutes — read |

## How Addons Work

Each addon is self-contained. Pick the ones you want, follow the README inside, and copy the files into your opencode config directory. Nothing conflicts with the base setup or with each other.

## Recommended Path

1. **Start with base** — supervisor + 9 subagents, DeepSeek only. Use it for a week.
2. **Add OpenCode Modes** — gives you trigger-word control over the agent's behavior. One file, immediate benefit.
3. **Add Ollama Local** — when you want private, offline, or cost-free model access for certain tasks.
4. **Read the Reference** — the catalog at the repo root explains every agent, subagent, mode, and command. Copy it to your Desktop for quick access: `cp reference.md ~/Desktop/opencode-reference.md`.
