# Supervisor — Agent Orchestration for OpenCode

```
YOU: "Build a REST API for the user model"
  |
  v
SUPERVISOR (plans, delegates, reviews, commits)
  |
  +--> worker     (builds it)
  +--> architect  (designs first if needed)
  +--> reviewer   (checks the diff)
  +--> security   (scans for issues)
  +--> debugger   (fixes failures)
  +--> ...and 4 more specialized roles
```

A shareable setup for the Supervisor agent workflow in [OpenCode](https://opencode.ai). The Supervisor is a primary agent that plans, delegates to specialized subagents, reviews outputs, fixes issues, and commits — all while keeping its own context window clean. You talk to the Supervisor. It manages the team.

## What You Get

- **Supervisor agent** — a primary agent that orchestrates work through delegation. It reads the project, plans the work, spawns subagents, reviews their output, fixes issues, and commits.
- **9 specialized subagents** — worker, architect, planner, reviewer, debugger, security, researcher, editor, quote-auditor. Each powered by DeepSeek V4 Pro Max.
- **Behavioral guidelines** (AGENTS.md) — coding conventions that reduce LLM mistakes: simplicity, surgical changes, goal-driven execution, mode switching.
- **Grok worker** — optional alternative model worker for when you want Grok 4.3's strengths.
- **Upgrade path** — instructions for adding Claude Sonnet/Opus tiers, including a recommended 3-tier naming convention (`junior-*` / `*` / `senior-*`) with the exact specs (model, steps, permissions) used in production.
- **Optional addons** — OpenCode Modes (9 behavioral trigger words), Ollama Local (on-device agents), and a comprehensive full reference catalog. See [addons/](addons/).

## Quick Start

### 1. Get a DeepSeek API Key

Visit https://platform.deepseek.com/api_keys and create an API key. This is the only key you need to get started — all agents run on DeepSeek.

For a full list of recommended CLI tools, Python packages, and optional services, see [DEPENDENCIES.md](DEPENDENCIES.md).

### 2. Configure OpenCode

**If you already have an opencode config:** do NOT overwrite your `opencode.json`. Instead, merge just the `provider` block (DeepSeek) and the `agent` block (supervisor) into your existing config. The agent `.md` files can be copied directly — they won't conflict with anything.

**If this is your first opencode setup:** copy the full config:

```bash
# Copy config (replace the API key placeholder first)
cp opencode.json ~/.config/opencode/opencode.json

# Copy supervisor agent
cp supervisor.md ~/.config/opencode/agent/supervisor.md

# Copy subagent files (rename any that conflict with your own)
cp agents/*.md ~/.config/opencode/agents/

# Copy behavioral guidelines (merge if you already have AGENTS.md)
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

### Troubleshooting

**"Model not found" or API errors on restart:**
```
npm install @ai-sdk/deepseek
```
Run this in `~/.config/opencode/`. OpenCode should auto-install provider packages, but if it doesn't, this one-liner fixes it.

**"Agent not found" when the Supervisor tries to spawn a subagent:**
Make sure the agent `.md` files are in `~/.config/opencode/agents/` — not in a subdirectory. Run:
```bash
ls ~/.config/opencode/agents/*.md
```
You should see `worker.md`, `architect.md`, `planner.md`, etc.

**Already have an opencode.json?**
Don't overwrite it. Just merge the `"provider"` and `"agent"` blocks from this repo's `opencode.json` into yours. The agent `.md` files don't conflict with anything.

**Supervisor not appearing as a primary agent?**
Confirm `supervisor.md` is at `~/.config/opencode/agent/supervisor.md` (note: `agent/` singular, not `agents/` plural).

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
├── DEPENDENCIES.md                # Full dependency list (CLI tools, packages, services)
├── supervisor.md                  # Supervisor agent prompt (-> ~/.config/opencode/agent/)
├── opencode.json                  # Template config with placeholder API keys
├── opencode.json.md               # Config setup instructions
├── reference.md                   # Comprehensive agent/mode/command catalog (keep on Desktop!)
├── subagents.md                   # Quick reference for the 9 base subagents
├── AGENTS.md                      # Behavioral guidelines (-> ~/.config/opencode/)
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
├── addons/
│   ├── README.md                  # Addon overview
│   ├── open-code-modes/           # 9 behavioral modes (trigger words)
│   │   ├── README.md
│   │   ├── AGENTS.md              # Mode switching rules (-> ~/.config/opencode/)
│   │   └── modes/                 # Individual mode files
│   └── ollama-local/              # On-device models via Ollama
│       ├── README.md              # Setup guide + model recommendations
│       └── agents/                # Local subagent files
└── skills/
    └── README.md                  # Skills system documentation
```

## Requirements

- [OpenCode](https://opencode.ai) installed
- A [DeepSeek API key](https://platform.deepseek.com/api_keys) (free tier available)
- Node.js (for provider packages and MCP servers)
- See [DEPENDENCIES.md](DEPENDENCIES.md) for recommended CLI tools and optional services

## Design Philosophy

**Delegate everything.** The Supervisor's job is orchestration, not implementation. Subagents do the work. The Supervisor's value is synthesis — seeing the combined output of multiple subagents and making decisions.

**One model, many roles.** All subagents use the same model (DeepSeek V4 Pro Max) but different prompts and permission sets. The specialization comes from the instructions, not the model — a security auditor and an editor have very different prompts, same brain.

**Read-only by default.** Specialized subagents (architect, reviewer, debugger, security, editor, planner, quote-auditor) can read and analyze but cannot edit files or run commands. Only the worker has full access. This prevents accidental changes from analysis agents.

**Upgrade when needed.** DeepSeek handles 95% of work. When you hit a wall or the stakes are high, add Claude Sonnet/Opus tiers (see `agents/UPGRADING.md`). The architecture supports this without changing anything else.

## Credits

Originally developed as a personal opencode configuration. Extracted and shared so others can use the same supervisor-agent workflow.

## License

MIT — use it, modify it, share it.
