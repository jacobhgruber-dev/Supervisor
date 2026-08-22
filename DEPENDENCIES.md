# Dependencies — Setting Up Your System

A complete list of everything needed to run the Supervisor agent workflow. Start with Tier 1 (you can be up and running in 5 minutes) and add tiers as you go.

> 🩺 **Dependency Doctor.** Not sure what's installed? Run `./install.sh --doctor` (macOS/Linux) — it scans your machine against the repo's dependency manifest (`deps.json`), tells you which tools are present, and prints a tailored install command for every missing one. It never fails and writes nothing.

---

## Tier 1: Essential (3 items)

The bare minimum. Install these and you have a working supervisor.

| What | Why | How |
|------|-----|-----|
| **OpenCode** | The app itself | `npm install -g opencode` |
| **DeepSeek API key** | Powers the supervisor and all 9 subagents | [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys) |
| **Node.js** | Provider packages, MCP servers via npx | `brew install node` |

---

## Tier 2: Plugins (optional, 4 items)

The base config ships with the Observer plugin already configured: `"plugin": ["observer-bridge.js"]`. Copy `plugin/observer-bridge.js` to your config root (already done in the main setup). Additional optional plugins are available:

```json
"plugin": [
  "opencode-wakelock",
  "opencode-pty",
  "opencode-websearch-cited",
  "opencode-notificator"
]
```

| Plugin | What it does |
|--------|-------------|
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

> 🔐 Security agents (`security`, `junior-security`, `senior-security`, `security-mule`) also run these as optional scanners — see their `Tool Awareness` sections.

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

The config ships with **two MCP servers enabled by default** — no keys needed, OpenCode runs them via `npx` on first use:

| MCP | What it adds |
|-----|--------------|
| `playwright` | Drive a real browser — clicks, forms, login flows |
| `a11y-color-contrast` | WCAG color-contrast checks for design and accessibility work |

It also includes **thirteen optional MCP servers, disabled by default.** Each needs a key or an extra install, so you opt in only when you want it. To turn one on: set its `"enabled": true` in the `"mcp"` block **and** make sure the `"permission"` block allows it (`"<name>_*": "allow"` — `twenty-first` ships as `"deny"` and must be changed).

| MCP | What it adds | Setup |
|-----|--------------|-------|
| `chrome-devtools` | Inspect pages, console, and network for web debugging | Just flip `"enabled": true` — no key needed, already pre-allowed in the permission block |
| `elevenlabs` | Text-to-speech / voice generation | Key from [elevenlabs.io](https://elevenlabs.io) → `YOUR_ELEVENLABS_KEY`; needs [`uv`](https://docs.astral.sh/uv/) installed |
| `railway` | Deploy & manage apps on Railway | Install the [Railway CLI](https://docs.railway.com/guides/cli), then `railway login` |
| `screenpipe` | Search 24/7 screen + audio history | Install & run the [screenpipe](https://screenpi.pe) app (records locally). Cross-platform. |
| `macos-automator` | Control native **macOS** apps via AppleScript/JXA | macOS only. Node 24+, plus Automation + Accessibility permission. |
| `yt-dlp` | Download audio/video from YouTube and other sites for transcription/analysis | `brew install yt-dlp` or `pip install yt-dlp` |
| `vercel` | Deploy & manage apps on Vercel | Key from [vercel.com/account/tokens](https://vercel.com/account/tokens) → `YOUR_VERCEL_TOKEN` |
| `gemini-api-docs` | Live Gemini API documentation lookup | Needs [`uv`](https://docs.astral.sh/uv/) installed. Works keyless. |
| `context7` | Live, version-accurate library/API docs | Works keyless; optional free key from [context7.com](https://context7.com) for higher limits. |
| `github` | Manage GitHub issues, PRs, repos | [Docker](https://www.docker.com) + a [GitHub token](https://github.com/settings/tokens) → `YOUR_GITHUB_TOKEN`. |
| `macos-use` | Native macOS GUI control — mouse, keyboard, accessibility automation | macOS only. Needs the `mcp-server-macos-use` binary at `/usr/local/bin`. |
| `firecrawl` | Web scrape/search for JS-heavy pages (optional worker tool) | Free tier key at [firecrawl.dev](https://www.firecrawl.dev). Set `FIRECRAWL_API_KEY`. |
| `twenty-first` | UI component search & generation (21st.dev) | Flip `"enabled": true` and change its permission from `"deny"` to `"allow"`. |

> ℹ️ `open-design` appears in the config only as a **permission key** (gating the designer agent) — there is no `open-design` MCP server entry in the template. If you want that service, add a server entry to the `"mcp"` block yourself and set its permission to `"allow"`.

**Windows desktop control:** `macos-automator` and `macos-use` are macOS-only. On Windows, use [CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP) (follow its repo setup) and add it to `"mcp"` the same opt-in way. The Windows installer (`setup.ps1`) drops the macOS-only entries automatically. `screenpipe` runs on Windows already.

Example — enabling Context7:

```json
"mcp": {
  "context7": {
    "type": "local",
    "command": ["npx", "-y", "@upstash/context7-mcp"],
    "enabled": true
  }
},
"permission": {
  "context7_*": "allow"
}
```

---

## What's Not Listed Here

- **API keys** (DeepSeek, Anthropic, Google, xAI) — documented in [PROVIDERS.md](PROVIDERS.md).
- **Model files** (whisper models) — auto-downloaded on first use.
