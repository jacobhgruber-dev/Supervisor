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
- **44 agents across 4 tiers (junior, mid, senior, mule)** — 9 roles (worker, architect, planner, reviewer, debugger, security, researcher, editor, quote-auditor) at junior (DeepSeek V4 Pro), mid (Claude Sonnet 5), senior (Claude Opus 4.8), and mule (various models) tiers, plus alternative model workers. All with built-in awareness of 14+ CLI code quality and security tools.
- **Behavioral guidelines** (AGENTS.md) — coding conventions that reduce LLM mistakes: simplicity, surgical changes, goal-driven execution, mode switching.
- **Automated code quality pipeline** — reviewer runs ruff + mypy + trivy on every review; debugger matches tools to symptoms (py-spy, scalene); worker self-verifies before reporting done; supervisor verifies lint/types/coverage before committing.
- **Grok worker** — an alternative-model worker on xAI's Grok 4.3. Ships in `agents/grok-worker.md` with a mirror copy and setup README in `addons/grok-worker/`. Activate by adding an xAI key; the core system doesn't depend on it.
- **Full 4-tier system built in** — all 44 agents (including mule tier and alternative model workers) ship with the repo. The `junior-*` / `*` / `senior-*` naming convention is already configured with exact specs (model, steps, permissions). Mid and senior tiers activate as soon as you add an Anthropic API key.
- **Observer (built in)** — a multimodal Gemini 3.5 Flash subagent plus a paste-interception plugin. Paste a screenshot into chat and Observer returns structured analysis (text extraction, UI comparison, error logs). The supervisor sees the text; the observer sees the image. Activates automatically once a Google (Gemini) key is configured.
- **Optional addons** — OpenCode Modes (9 behavioral trigger words) and a comprehensive full reference catalog. See [addons/](addons/).

## Quick Start

### 1. Get a DeepSeek API Key

Visit https://platform.deepseek.com/api_keys and create an API key. This is the only key you need to get started — all junior-tier agents and most mules run on DeepSeek.

> **Provider note:** This repo uses 4 providers (DeepSeek, Anthropic, Google, xAI). DeepSeek is the only one required to start — it powers the Supervisor + junior tier. Add Anthropic to unlock mid/senior tiers, Google to activate Observer + Gemini workers, and xAI for Grok workers. See [PROVIDERS.md](PROVIDERS.md) for direct links to get keys.

For a full list of recommended CLI tools, Python packages, and optional services, see [DEPENDENCIES.md](DEPENDENCIES.md).

### 2. Configure OpenCode

**If you configured providers through OpenCode Desktop (Settings → Providers):** you don't need to touch `opencode.json` at all — your provider config is already set. Just copy the agent files, plugin, and AGENTS.md:

```bash
# Copy ALL agents — supervisor + subagents — into the same folder (plural "agents")
mkdir -p ~/.config/opencode/agents
cp agent/supervisor.md ~/.config/opencode/agents/supervisor.md
cp agents/*.md   ~/.config/opencode/agents/

# Copy the Observer plugin (lets you paste screenshots into chat)
cp plugin/observer-bridge.js ~/.config/opencode/observer-bridge.js

# Copy behavioral guidelines (merge if you already have AGENTS.md)
cp AGENTS.md ~/.config/opencode/AGENTS.md
```

**If this is your first opencode setup** (and you haven't configured providers yet)**:** copy the full config too — it gives you MCP servers, `default_agent`, and `"subagent_depth": 3` (required for mule chains):

```bash
# Copy config (no API keys live in here — see step 3)
cp opencode.template.json ~/.config/opencode/opencode.json

# Copy ALL agents — supervisor + subagents — into the same folder (plural "agents")
mkdir -p ~/.config/opencode/agents
cp agent/supervisor.md ~/.config/opencode/agents/supervisor.md
cp agents/*.md   ~/.config/opencode/agents/

# Copy the Observer plugin (lets you paste screenshots into chat)
cp plugin/observer-bridge.js ~/.config/opencode/observer-bridge.js

# Copy behavioral guidelines (merge if you already have AGENTS.md)
cp AGENTS.md ~/.config/opencode/AGENTS.md
```

> **Note:** OpenCode loads every markdown agent — the primary Supervisor *and* the subagents — from `~/.config/opencode/agents/` (plural). The `mode:` field inside each file (`primary` vs `subagent`) is what distinguishes them, not the folder. There is no singular `agent/` folder.

### 3. Connect your keys

No keys go in `opencode.json`. Authenticate natively instead.

**Desktop (OpenCode app):** Go to Settings → Providers → DeepSeek and paste your API key. Repeat for Anthropic if you want mid/senior tiers, Google if you want Observer + Gemini workers, or xAI if you want Grok workers.

**CLI:** Use `opencode auth login`:

```bash
opencode auth login   # choose DeepSeek, paste your key
opencode auth login   # run again, choose Anthropic, paste your key
```

Provider discovery is handled natively by OpenCode through models.dev — no provider block needed in your config; auth comes from your login.

> **Note:** If DeepSeek isn't in the CLI menu, pick **Other** and enter `deepseek` as the id.

Keys are stored in OpenCode's secure file (`~/.local/share/opencode/auth.json`). Alternatively, set the `DEEPSEEK_API_KEY` and `ANTHROPIC_API_KEY` environment variables.

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
Make sure you've added your DeepSeek API key through OpenCode Desktop (Settings → Providers) or `opencode auth login`. If you modified `opencode.json` to add a custom `provider` block, remove it — built-in providers (DeepSeek, Anthropic, Google, xAI) are handled natively and don't belong in the config.

**"Agent not found" when the Supervisor tries to spawn a subagent:**
Make sure the agent `.md` files are in `~/.config/opencode/agents/` — not in a subdirectory. Run:
```bash
ls ~/.config/opencode/agents/*.md
```
You should see `worker.md`, `architect.md`, `planner.md`, etc.

**Already have an opencode.json?**
If you already configured providers through OpenCode Desktop (Settings → Providers), you don't need to touch `opencode.template.json` at all — just copy the agent files, plugin, and AGENTS.md. The agent files won't conflict with anything.

**Supervisor not appearing as a primary agent?**
Confirm `supervisor.md` is at `~/.config/opencode/agents/supervisor.md` (plural `agents/`) and that its frontmatter says `mode: primary`. OpenCode has no singular `agent/` folder — everything goes in `agents/`.

## Architecture

```
You (the User)
      |
      v
Supervisor Agent (primary, DeepSeek V4 Pro)
      |
       +---> worker          (implementation, 40 steps, full access)
       +---> architect       (design, 25 steps, edit + web + playwright)
       +---> planner         (sequencing, 25 steps, read-only)
       +---> reviewer        (code review, 30 steps, read-only)
       +---> debugger        (runtime errors, 35 steps, edit + web + playwright)
       +---> security        (vulnerability scan, 30 steps, read-only + bash + web + playwright)
       +---> researcher      (information, 40 steps, full access)
        +---> editor          (proofreading, 25 steps, read + edit)
        +---> quote-auditor   (quote verification, 25 steps, read-only)
        +---> observer        (visual analysis, multimodal, read-only)
```

(Each role also has `junior-*`, `*` (mid), `senior-*`, and `*-mule` tier variants. `gemini-worker` and `grok-worker` ship in `agents/` — activate with Google / xAI keys. Local Ollama placeholders: `local-coder`, `local-reasoner`.)

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
├── agent/supervisor.md   # Primary Supervisor agent (source only — copy FROM here; OpenCode reads from ~/.config/opencode/agents/ not here)
├── opencode.template.json         # Template config with MCP servers, Ollama provider, subagent_depth: 3
├── opencode.json.md               # Config setup instructions
├── reference.md                   # Comprehensive agent/mode/command catalog (keep on Desktop!)
├── subagents.md                   # Quick reference for the 9 base subagents
├── tier-system-reference.md       # Complete 4-tier agent specs and naming conventions
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
│   ├── junior-* / * / senior-* / *-mule  # Same 9 roles at all 4 tiers (DeepSeek, Claude, Opus, mule)
│   ├── observer.md                # Multimodal Observer subagent (Gemini 3.5 Flash)
│   ├── gemini-worker.md           # High-powered worker (Gemini 3.1 Pro)
│   ├── grok-worker.md             # High-powered worker (Grok 4.3)
│   ├── local-coder.md             # Ollama placeholder (configure before use)
│   └── local-reasoner.md          # Ollama placeholder (configure before use)
├── plugin/
│   └── observer-bridge.js         # Paste-a-screenshot interception — deploys to config root: ~/.config/opencode/observer-bridge.js (not a plugin/ subdirectory)
├── addons/
│   ├── README.md                  # Addon overview
│   ├── grok-worker/               # Optional xAI Grok worker (+ setup README)
│   └── open-code-modes/           # 9 behavioral modes (trigger words)
│       ├── README.md
│       ├── AGENTS.md              # Mode switching rules — ⚠️ WARNING: merge with existing root AGENTS.md; do NOT overwrite (-> ~/.config/opencode/)
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

**One model, many roles (junior tier default).** All junior-tier subagents use the same model (DeepSeek V4 Pro) but different prompts and permission sets. The specialization comes from the instructions, not the model — a security auditor and an editor have very different prompts, same brain. Mid and senior tiers use different models (Claude Sonnet 5, Claude Opus 4.8) for tasks needing deeper reasoning.

**Edit permissions by role.** Worker, researcher, debugger, architect, and editor have `edit: allow` — they can create or modify code files. Planner, reviewer, security, and quote auditor are read-only (`edit: deny`). For bash: worker, researcher, debugger, reviewer, and security have `bash: allow`; architect, planner, editor, and quote auditor have `bash: deny`. For web access (webfetch, websearch, playwright): worker, researcher, debugger, architect, and security have full web access; reviewer, editor, planner, and quote auditor do not. Tiers differ only in model, never in permissions.

**Tiers scale with your needs.** All 4 tiers (junior, mid, senior, mule) ship in the repo. DeepSeek handles 95% of work on its own. Mid and senior agents (Claude Sonnet/Opus) are already configured and activate when you add an Anthropic API key (see `tier-system-reference.md`). No architectural changes needed.

## Credits

Originally developed as a personal opencode configuration. Extracted and shared so others can use the same supervisor-agent workflow.

## License

MIT — use it, modify it, share it.
