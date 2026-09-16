# Addons — Optional Extras

The Supervisor repo ships with everything you need out of the box: one API key, one model, nine specialized subagent roles (47 subagent files across 4 tiers — 48 agents total with the Supervisor — including designer / designer-mule). Addons layer on additional capabilities for a more complete setup.

## Available Addons

| Addon | What It Adds | Setup Time |
|-------|-------------|------------|
| [OpenCode Modes](open-code-modes/) | 9 behavioral modes for the main agent — trigger words that change how it thinks (architect, debug, review, etc.) | Nothing to copy — built into the Supervisor |

> **Grok Worker is no longer an addon — it's built into the base setup.** The alternative-model worker subagent (`agents/grok-worker.md`) ships with the core repo, running on Grok 4.6 (`xai/grok-4.6`), and activates once an xAI API key is configured. See [grok-worker/](grok-worker/) for activation details.

> **Observer is no longer an addon — it's built into the base setup.** The multimodal screenshot-reading subagent (`agents/observer.md`) and its paste-interception plugin (`plugin/observer-bridge.js`) ship with the core repo and activate once a Google (Gemini) key is configured. See [GETTING_STARTED.md](../GETTING_STARTED.md).

## See Also

- **[reference.md](../reference.md)** — the comprehensive catalog of all agents, subagents, modes, commands, and model costs.

## How Addons Work

Each addon is self-contained. Pick the ones you want, follow the README inside, and copy the files into your opencode config directory. Nothing conflicts with the base setup or with each other.

## Recommended Path

1. **Start with base** — supervisor + 9 subagents, DeepSeek only. Use it for a week.
2. **Use OpenCode Modes** — gives you trigger-word control over the agent's behavior. Built into the Supervisor — nothing to install.
3. **Read the Reference** — the catalog at the repo root explains every agent, subagent, mode, and command. Copy it to your Desktop for quick access: `cp reference.md ~/Desktop/opencode-reference.md`.
