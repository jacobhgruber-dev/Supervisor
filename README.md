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

> 🚀 **New to all this?** If you've never set up OpenCode or used an API key before, start with **[GETTING_STARTED.md](GETTING_STARTED.md)** — a step-by-step, idiot-proof walkthrough that takes you from zero to a working agent team in ~15 minutes. There's also a visual version at [`index.html`](index.html) (open it in a browser, or host it via GitHub Pages). The README below assumes you already know your way around OpenCode.

## What You Get

- **Supervisor agent** — a primary agent that orchestrates work through delegation. It reads the project, plans the work, spawns subagents, reviews their output, fixes issues, and commits — including automated quality verification (ruff, mypy, shellcheck, radon, coverage).
- **27 specialized subagents across 3 tiers** — 9 roles (worker, architect, planner, reviewer, debugger, security, researcher, editor, quote-auditor) at junior (DeepSeek V4 Pro Max), mid (Claude Sonnet 4.6 Max), and senior (Claude Opus 4.8 Max) tiers. All with built-in awareness of 14+ CLI code quality and security tools.
- **Behavioral guidelines** (AGENTS.md) — coding conventions that reduce LLM mistakes: simplicity, surgical changes, goal-driven execution, mode switching.
- **Automated code quality pipeline** — reviewer runs ruff + mypy + trivy on every review; debugger matches tools to symptoms (py-spy, scalene); worker self-verifies before reporting done; supervisor verifies lint/types/coverage before committing.
- **Grok worker** — optional alternative model worker for when you want Grok 4.3's strengths.
- **Full 3-tier system built in** — all 27 agents ship with the repo. The `junior-*` / `*` / `senior-*` naming convention is already configured with exact specs (model, steps, permissions). Mid and senior tiers activate as soon as you add an Anthropic API key.
- **Observer (built in)** — a multimodal Claude Sonnet 4.6 subagent plus a paste-interception plugin. Paste a screenshot into chat and Observer returns structured analysis (text extraction, UI comparison, error logs). The supervisor sees the text; the observer sees the image. Activates automatically once an Anthropic key is configured.
- **Optional addons** — OpenCode Modes (9 behavioral trigger words) and a comprehensive full reference catalog. See [addons/](addons/).

## Quick Start

### 1. Get a DeepSeek API Key

Visit https://platform.deepseek.com/api_keys and create an API key. This is the only key you need to get started — all agents run on DeepSeek.

For a full list of recommended CLI tools, Python packages, and optional services, see [DEPENDENCIES.md](DEPENDENCIES.md).

### 2. Configure OpenCode

**If you already have an opencode config:** do NOT overwrite your `opencode.json`. Instead, merge just the `provider` block (DeepSeek) into your existing config. The agent `.md` files can be copied directly — they won't conflict with anything.

**If this is your first opencode setup:** copy the full config:

```bash
# Copy config (replace the API key placeholder first)
cp opencode.json ~/.config/opencode/opencode.json

# Copy ALL agents — supervisor + subagents — into the same folder (plural "agents")
mkdir -p ~/.config/opencode/agents
cp supervisor.md ~/.config/opencode/agents/supervisor.md
cp agents/*.md   ~/.config/opencode/agents/

# Copy the Observer plugin (lets you paste screenshots into chat)
mkdir -p ~/.config/opencode/plugin
cp plugin/*.js ~/.config/opencode/plugin/

# Copy behavioral guidelines (merge if you already have AGENTS.md)
cp AGENTS.md ~/.config/opencode/AGENTS.md
```

> **Note:** OpenCode loads every markdown agent — the primary Supervisor *and* the subagents — from `~/.config/opencode/agents/` (plural). The `mode:` field inside each file (`primary` vs `subagent`) is what distinguishes them, not the folder. There is no singular `agent/` folder.

### 3. Edit opencode.json

Replace `YOUR_DEEPSEEK_API_KEY` with your actual key. If you don't have an opencode config yet, this file becomes your full config. If you already have one, merge the provider section into your existing config.

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
Don't overwrite it. Just merge the `"provider"` block from this repo's `opencode.json` into yours. The agent `.md` files don't conflict with anything.

**Supervisor not appearing as a primary agent?**
Confirm `supervisor.md` is at `~/.config/opencode/agents/supervisor.md` (plural `agents/`) and that its frontmatter says `mode: primary`. OpenCode has no singular `agent/` folder — everything goes in `agents/`.

## Architecture

```
You (the User)
      |
      v
Supervisor Agent (primary, DeepSeek V4 Pro Max)
      |
       +---> worker          (implementation, 40 steps, full access)
       +---> architect       (design, 25 steps, edit + web + playwright)
       +---> planner         (sequencing, 25 steps, read-only)
       +---> reviewer        (code review, 30 steps, read-only)
       +---> debugger        (runtime errors, 35 steps, edit + web + playwright)
       +---> security        (vulnerability scan, 25 steps, read-only + bash + web + playwright)
       +---> researcher      (information, 35 steps, full access)
       +---> editor          (proofreading, 25 steps, read + edit)
        +---> quote-auditor   (quote verification, 25 steps, read-only + bash)
       +---> grok-worker     (alternative model, 40 steps, full access)
       +---> observer        (visual analysis, multimodal, read-only)
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
├── supervisor.md                  # Primary Supervisor agent (-> ~/.config/opencode/agents/)
├── opencode.json                  # Template config with placeholder API keys
├── opencode.json.md               # Config setup instructions
├── reference.md                   # Comprehensive agent/mode/command catalog (keep on Desktop!)
├── subagents.md                   # Quick reference for the 9 base subagents
├── tier-system-reference.md       # Complete 3-tier agent specs and naming conventions
├── AGENTS.md                      # Behavioral guidelines (-> ~/.config/opencode/)
├── agents/                        # All subagents (-> ~/.config/opencode/agents/, plural)
│   ├── worker.md                  # General-purpose implementation agent
│   ├── architect.md               # System design and tradeoff analysis
│   ├── planner.md                 # Task breakdown and sequencing
│   ├── reviewer.md                # Code review and bug detection
│   ├── debugger.md                # Runtime error triage
│   ├── security.md                # Vulnerability scanning
│   ├── researcher.md              # Information gathering and synthesis
│   ├── editor.md                  # Grammar, spelling, readability
│   ├── quote-auditor.md           # Quotation verification
│   ├── junior-* / senior-*        # Same 9 roles at DeepSeek (junior) and Opus (senior) tiers
│   ├── grok-worker.md             # Alternative Grok-powered worker
│   └── observer.md                # Multimodal Observer subagent (Claude Sonnet 4.6)
├── plugin/
│   └── observer-bridge.js         # Paste-a-screenshot interception (-> ~/.config/opencode/plugin/)
├── addons/
│   ├── README.md                  # Addon overview
│   └── open-code-modes/           # 9 behavioral modes (trigger words)
│       ├── README.md
│       ├── AGENTS.md              # Mode switching rules (-> ~/.config/opencode/)
│       └── modes/                 # Individual mode files
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

**Edit permissions by role.** Worker, researcher, debugger, architect, and editor have `edit: allow` — they can create or modify code files. Planner, reviewer, security, and quote auditor are read-only (`edit: deny`). For bash: worker, researcher, debugger, reviewer, security, and quote auditor have `bash: allow`; architect, planner, and editor have `bash: deny`. For web access (webfetch, websearch, playwright): worker, researcher, debugger, architect, and security have full web access; reviewer, editor, planner, and quote auditor do not. Tiers differ only in model, never in permissions.

**Tiers scale with your needs.** All 3 tiers ship in the repo. DeepSeek handles 95% of work on its own. Mid and senior agents (Claude Sonnet/Opus) are already configured and activate when you add an Anthropic API key (see `tier-system-reference.md`). No architectural changes needed.

## Credits

Originally developed as a personal opencode configuration. Extracted and shared so others can use the same supervisor-agent workflow.

## License

MIT — use it, modify it, share it.
