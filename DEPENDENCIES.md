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

These go in the `"plugin"` array in your `opencode.json`. OpenCode auto-installs them — no manual install needed.

```json
"plugin": [
  "opencode-wakelock",
  "opencode-pty",
  "opencode-websearch-cited",
  "opencode-notificator",
  "opencode-gemini-auth"
]
```

| Plugin | What it does |
|--------|-------------|
| `opencode-wakelock` | Keeps screen awake during long agent runs |
| `opencode-pty` | Terminal integration |
| `opencode-websearch-cited` | Web search with source citations |
| `opencode-notificator` | Desktop notifications when tasks complete |
| `opencode-gemini-auth` | Gemini Code Assist authentication |

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
python3 -m venv ~/Projects/Whisper/fw-env
source ~/Projects/Whisper/fw-env/bin/activate
pip install faster-whisper
```

The `large-v3` model downloads automatically on first use (~3 GB).

---

## Tier 5: Optional — Firecrawl MCP (1 item)

Web scraping, search, and structured data extraction. OpenCode runs it via npx — no manual install.

```json
"mcp": {
  "firecrawl": {
    "type": "local",
    "command": ["npx", "-y", "firecrawl-mcp"],
    "enabled": true,
    "env": {
      "FIRECRAWL_API_KEY": "YOUR_FIRECRAWL_KEY"
    }
  }
}
```

Requires a free API key from [firecrawl.dev](https://firecrawl.dev).

---

## What's Not Listed Here

- **Claude, Grok, ElevenLabs API keys** — documented in `opencode.json.md` (optional providers) and `agents/UPGRADING.md` (3-tier upgrade).
- **Model files** (whisper models, ollama models) — auto-downloaded on first use or pulled via `ollama pull`.
- **Anna's Archive / AudiobookBay CLIs** — personal workflow tools, not part of the supervisor system.
