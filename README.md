# Supervisor — Agent Orchestration for OpenCode

A shareable setup for the Supervisor agent workflow in [OpenCode](https://opencode.ai). The Supervisor is a primary agent that plans, delegates to specialized subagents, reviews outputs, fixes issues, and commits — all while keeping its own context window clean. You talk to the Supervisor. It manages the team.

## What You Get

- **Supervisor agent** — a primary agent that orchestrates work through delegation. It reads the project, plans the work, spawns subagents, reviews their output, fixes issues, and commits.
- **9 specialized subagents** — worker, architect, planner, reviewer, debugger, security, researcher, editor, quote-auditor. Each powered by DeepSeek V4 Pro Max.
- **Behavioral guidelines** (AGENTS.md) — coding conventions that reduce LLM mistakes: simplicity, surgical changes, goal-driven execution, mode switching.
- **Grok worker** — optional alternative model worker for when you want Grok 4.3's strengths.
- **Upgrade path** — instructions for adding Claude Sonnet/Opus tiers when you need them.

## Quick Start

### 1. Get a DeepSeek API Key

Visit https://platform.deepseek.com/api_keys and create an API key. This is the only key you need to get started — all agents run on DeepSeek.

### 2. Configure OpenCode

Copy the configuration files to your opencode directory:

```bash
# Copy config (update the API key first)
cp opencode.json ~/.config/opencode/opencode.json

# Copy agent files
cp supervisor.md ~/.config/opencode/agent/supervisor.md
cp agents/*.md ~/.config/opencode/agents/
cp AGENTS.md ~/.config/opencode/AGENTS.md
```

### 3. Edit opencode.json

Replace `YOUR_DEEPSEEK_API_KEY` with your actual key. If you don't have an opencode config yet, this file becomes your full config. If you already have one, merge the provider and agent sections into your existing config.

### 4. Restart OpenCode

The Supervisor will appear as a primary agent option. Select it, and you're ready to delegate.

### 5. Start Delegating

```
"Review this project and tell me what needs work"
"Build a REST API for the user model"
"Fix the login bug"
"Research best practices for X"
"Audit the auth code for security issues"
```

The Supervisor handles the rest — planning, spawning subagents, reviewing, fixing, and committing.

## Architecture

```
You (the User)
      |
      v
Supervisor Agent (primary, DeepSeek V4 Pro Max)
      |
      +---> worker          (implementation, 40 steps, full access)
      +---> architect       (design, 25 steps, read-only)
      +---> planner         (sequencing, 25 steps, read-only)
      +---> reviewer        (code review, 30 steps, read-only)
      +---> debugger        (runtime errors, 35 steps, read-only + bash)
      +---> security        (vulnerability scan, 25 steps, read-only + bash)
      +---> researcher      (information, 35 steps, full access)
      +---> editor          (proofreading, 25 steps, read-only)
      +---> quote-auditor   (quote verification, 25 steps, read-only)
      +---> grok-worker     (alternative model, 40 steps, full access)
```

## How It Works

The Supervisor follows a strict workflow for every request:

1. **Orient** — reads governing docs to understand the project
2. **Plan** — identifies work items and decides what to delegate
3. **Triage** — if the path isn't clear, spawns a researcher/debugger/architect first
4. **Delegate** — spawns subagents with specific, actionable prompts
5. **Review** — runs verification, reads diffs for quality, spawns reviewer for complex changes
6. **Fix** — re-spawns subagents for failures (never self-fixes)
7. **Commit** — commits in logical units, pushes, updates docs

Key principle: **Always delegate.** The Supervisor self-executes only mechanical operations (commits, pushes, updating docs). All substantive work goes to subagents.

## File Structure

```
Supervisor/
├── README.md                      # This file
├── supervisor.md                  # Supervisor agent prompt (-> ~/.config/opencode/agent/)
├── opencode.json                  # Template config with placeholder API keys
├── opencode.json.md               # Config setup instructions
├── AGENTS.md                      # Behavioral guidelines (-> ~/.config/opencode/)
├── reference.md                   # Full subagent catalog and quick reference
├── agents/
│   ├── worker.md                  # General-purpose implementation agent
│   ├── architect.md               # System design and tradeoff analysis
│   ├── planner.md                 # Task breakdown and sequencing
│   ├── reviewer.md                # Code review and bug detection
│   ├── debugger.md                # Runtime error triage
│   ├── security.md                # Vulnerability scanning
│   ├── researcher.md              # Information gathering and synthesis
│   ├── editor.md                  # Grammar, spelling, readability
│   ├── quote-auditor.md           # Quotation verification
│   ├── grok-worker.md             # Alternative Grok-powered worker
│   └── UPGRADING.md               # How to add Claude Sonnet/Opus tiers
└── skills/
    └── README.md                  # Skills system documentation
```

## Requirements

- [OpenCode](https://opencode.ai) installed
- A [DeepSeek API key](https://platform.deepseek.com/api_keys) (free tier available)
- Optional: [Anthropic API key](https://console.anthropic.com) for Claude Sonnet/Opus upgrades
- Optional: [xAI API key](https://console.x.ai) for Grok worker

## Design Philosophy

**Delegate everything.** The Supervisor's job is orchestration, not implementation. Subagents do the work. The Supervisor's value is synthesis — seeing the combined output of multiple subagents and making decisions.

**One model, many roles.** All subagents use the same model (DeepSeek V4 Pro Max) but different prompts and permission sets. The specialization comes from the instructions, not the model — a security auditor and an editor have very different prompts, same brain.

**Read-only by default.** Specialized subagents (architect, reviewer, debugger, security, editor, planner, quote-auditor) can read and analyze but cannot edit files or run commands. Only the worker has full access. This prevents accidental changes from analysis agents.

**Upgrade when needed.** DeepSeek handles 95% of work. When you hit a wall or the stakes are high, add Claude Sonnet/Opus tiers (see `agents/UPGRADING.md`). The architecture supports this without changing anything else.

## Credits

Originally developed as a personal opencode configuration. Extracted and shared so others can use the same supervisor-agent workflow.

## License

MIT — use it, modify it, share it.
