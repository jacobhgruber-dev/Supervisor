# Addons — Optional Extras

The Supervisor repo ships with everything you need out of the box: one API key, one model, nine specialized subagent roles (41 agent files across 4 tiers). Addons layer on additional capabilities for a more complete setup.

## Available Addons

| Addon | What It Adds | Setup Time |
|-------|-------------|------------|
| [OpenCode Modes](open-code-modes/) | 9 behavioral modes for the main agent — trigger words that change how it thinks (architect, debug, review, etc.) | 1 minute — copy one file |
| [Grok Worker](grok-worker/) | An alternative-model subagent running on xAI's Grok 4.3, for when you want Grok's strengths on a task | 2 minutes — add an xAI key + copy one file |

> **Observer is no longer an addon — it's built into the base setup.** The multimodal screenshot-reading subagent (`agents/observer.md`) and its paste-interception plugin (`plugin/observer-bridge.js`) ship with the core repo and activate once an Anthropic key is configured. See [GETTING_STARTED.md](../GETTING_STARTED.md).

## See Also

- **[reference.md](../reference.md)** — the comprehensive catalog of all agents, subagents, modes, commands, and model costs.

## How Addons Work

Each addon is self-contained. Pick the ones you want, follow the README inside, and copy the files into your opencode config directory. Nothing conflicts with the base setup or with each other.

## Recommended Path

1. **Start with base** — supervisor + 9 subagents, DeepSeek only. Use it for a week.
2. **Add OpenCode Modes** — gives you trigger-word control over the agent's behavior. One file, immediate benefit.
3. **Read the Reference** — the catalog at the repo root explains every agent, subagent, mode, and command. Copy it to your Desktop for quick access: `cp reference.md ~/Desktop/opencode-reference.md`.
