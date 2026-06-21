# Dependencies — Setting Up Your System

A complete list of everything needed to run the Supervisor agent workflow. Start with Tier 1 (you can be up and running in 5 minutes) and add tiers as you go.

---

## Tier 1: Essential (3 items)

The bare minimum. Install these and you have a working supervisor.

| What | Why | How |
|------|-----|-----|
| **OpenCode** | The app itself | `npm install -g opencode` |
| **DeepSeek API key** | Powers the supervisor and all 9 subagents | [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys) |
| **Node.js** | Provider packages, MCP servers via npx | `brew install node` |

---

## Tier 2: Plugins (5 items)

These go in the `"plugin"` array in your `opencode.json`. OpenCode auto-installs them — no manual install needed. The shipped config includes `opencode-xai-auth`; the rest are optional quality-of-life additions.

```json
"plugin": [
  "opencode-xai-auth",
  "opencode-wakelock",
  "opencode-pty",
  "opencode-websearch-cited",
  "opencode-notificator"
]
```

| Plugin | What it does |
|--------|-------------|
| `opencode-xai-auth` | xAI (Grok) authentication — shipped in the config |
| `opencode-wakelock` | Keeps screen awake during long agent runs |
| `opencode-pty` | Terminal integration |
| `opencode-websearch-cited` | Web search with source citations |
| `opencode-notificator` | Desktop notifications when tasks complete |

---

## Tier 3: Recommended CLI Tools (4 items)

Not essential, but these make the workflow significantly better. All via Homebrew.

| CLI | Used by | `brew install` |
|-----|---------|----------------|
| `ffmpeg` | Audio conversion for whisper transcription | `brew install ffmpeg` |
| `whisper-cpp` | Fast audio transcription (`whisper-cli`) | `brew install whisper-cpp` |
| `ripgrep` (`rg`) | Fast code search — subagents use it constantly | `brew install ripgrep` |
| `gh` | GitHub CLI — commits, PRs, repo management | `brew install gh` |

---

## Tier 3b: Code Quality & Security CLI Tools (14 items)

These are baked into the subagent instructions (reviewer, debugger, worker). They run automatically when agents detect relevant file changes. All via Homebrew or pip.

| CLI | Used by | Install |
|-----|---------|---------|
| `ruff` | reviewer, debugger, worker | `pip3 install --break-system-packages ruff` |
| `mypy` | reviewer, debugger, worker | `pip3 install --break-system-packages mypy` |
| `shellcheck` | reviewer, debugger, worker | `brew install shellcheck` |
| `trivy` | reviewer, debugger, worker | `brew install trivy` |
| `radon` | reviewer, worker | `pip3 install --break-system-packages radon` |
| `lizard` | reviewer | `pip3 install --break-system-packages lizard` |
| `py-spy` | debugger, worker | `pip3 install --break-system-packages py-spy` |
| `scalene` | debugger, worker | `pip3 install --break-system-packages scalene` |
| `coverage` | reviewer, debugger, worker | `pip3 install --break-system-packages coverage` |
| `hypothesis` | reviewer, debugger, worker | `pip3 install --break-system-packages hypothesis` |
| `cosmic-ray` | reviewer (suggest only) | `pip3 install --break-system-packages cosmic-ray` |
| `pymupdf` | worker | `pip3 install --break-system-packages pymupdf` |
| `python-docx` | worker | `pip3 install --break-system-packages python-docx` |
| `beautifulsoup4` | worker | `pip3 install --break-system-packages beautifulsoup4` |

---

## Tier 4: Python Packages (4 items)

Useful for automation scripts, web scraping, and high-quality transcription.

| Package | Used by | Install |
|---------|---------|---------|
| `requests` | HTTP requests in scripts | `pip3 install requests` |
| `beautifulsoup4` | HTML parsing | `pip3 install beautifulsoup4` |
| `PySocks` | SOCKS proxy support (Tor) | `pip3 install PySocks` |
| `faster-whisper` | High-quality transcription | See setup below |

### faster-whisper setup

For high-quality transcription (better accuracy than `whisper-cpp`), install in a dedicated venv:

```bash
python3 -m venv ~/whisper-env
source ~/whisper-env/bin/activate
pip install faster-whisper
```

The `large-v3` model downloads automatically on first use (~3 GB).

---

## Tier 5: MCP Servers

The config ships with **two browser/automation MCP servers enabled by default** — no keys needed, OpenCode runs them via `npx` on first use:

| MCP | What it adds |
|-----|--------------|
| `playwright` | Drive a real browser — clicks, forms, login flows |
| `chrome-devtools` | Inspect pages, console, and network for web debugging |

It also includes **three optional MCP servers, disabled by default.** Each needs a key or an extra install, so you opt in only when you want it. To turn one on: set its `"enabled": true` in the `"mcp"` block **and** change its line in the `"permission"` block from `"deny"` to `"allow"`.

| MCP | What it adds | Setup |
|-----|--------------|-------|
| `firecrawl` | Web scraping + search for JS-heavy pages | Free key from [firecrawl.dev](https://firecrawl.dev) → `YOUR_FIRECRAWL_KEY` |
| `elevenlabs` | Text-to-speech / voice generation | Key from [elevenlabs.io](https://elevenlabs.io) → `YOUR_ELEVENLABS_KEY`; needs [`uv`](https://docs.astral.sh/uv/) installed |
| `railway` | Deploy & manage apps on Railway | Install the [Railway CLI](https://docs.railway.com/guides/cli), then `railway login` |
| `screenpipe` | Search 24/7 screen + audio history | Install & run the [screenpipe](https://screenpi.pe) app (records locally). Cross-platform. |
| `macos-automator` | Control native **macOS** apps via AppleScript/JXA | macOS only. Node 24+, plus Automation + Accessibility permission. |
| `context7` | Live, version-accurate library/API docs | Works keyless; optional free key from [context7.com](https://context7.com) for higher limits. |
| `github` | Manage GitHub issues, PRs, repos | [Docker](https://www.docker.com) + a [GitHub token](https://github.com/settings/tokens) → `YOUR_GITHUB_TOKEN`. |

**Windows desktop control:** `macos-automator` is macOS-only. On Windows, use [CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP) (follow its repo setup) and add it to `"mcp"` the same opt-in way. `screenpipe` runs on Windows already.

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

---

## What's Not Listed Here

- **Anthropic API key** — documented in `opencode.json.md` (providers) and `tier-system-reference.md` (3-tier configuration).
- **Model files** (whisper models) — auto-downloaded on first use.
