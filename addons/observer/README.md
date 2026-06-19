# Observer — Visual Understanding for Text-Only Supervisors

Text-only AI supervisors (DeepSeek V4 Pro) can't see images. Observer gives them eyes — a multimodal Claude Sonnet 4.6 subagent that reads screenshots, UI states, error logs, and design mockups, then returns structured text analysis the supervisor can act on.

## Why Observer?

- **Supervisors are text-only** — DeepSeek V4 Pro (the default supervisor model) can't process images. When a user pastes a screenshot or a tool captures UI state, the supervisor gets a file path it can't read.
- **Observer bridges the gap** — a plugin intercepts pasted images, saves them to `/tmp`, and notifies the supervisor. The supervisor spawns @observer as a subagent. Observer reads the image and returns structured text analysis. The supervisor never sees the image — it sees the analysis.
- **Seven analysis modes** — Observer auto-detects what you need: error log extraction, UI comparison, chart data extraction, issue location + fix suggestions, page restoration (pixel-perfect HTML/CSS descriptions), text/dialogue extraction, or quick state summary for verification loops.

## How It Works

```
User pastes screenshot
        |
        v
observer-bridge.js intercepts the image → saves to /tmp → replaces with text path
        |
        v
Supervisor sees "[Image saved to: /tmp/opencode/pasted_abc123.png]" → spawns @observer
        |
        v
@observer (Claude Sonnet 4.6) reads the image, analyzes it, returns structured text
        |
        v
Supervisor reads the analysis and acts on it
```

The plugin (`observer-bridge.js`) also injects visual-understanding instructions into the supervisor's system prompt, telling it when and how to use @observer.

## Quick Setup

### 1. Add an Anthropic API Key

Observer uses Claude Sonnet 4.6 (multimodal). Add an Anthropic provider to your `opencode.json` if you don't have one:

```json
"anthropic": {
  "npm": "@ai-sdk/anthropic",
  "name": "Anthropic",
  "apiKey": "${ANTHROPIC_API_KEY}"
}
```

Or set `ANTHROPIC_API_KEY` in your environment.

### 2. Copy the Files

```bash
# The observer agent definition
cp addons/observer/observer.md ~/.config/opencode/agents/observer.md

# The paste-interception plugin
cp addons/observer/observer-bridge.js ~/.config/opencode/plugin/observer-bridge.js
```

### 3. (Optional) Merge Visual Context Awareness into AGENTS.md

If you use the Supervisor's AGENTS.md, merge the Visual Context Awareness block from `addons/observer/AGENTS-patch.md` into your `~/.config/opencode/AGENTS.md`. This teaches all subagents to ask the supervisor for visual help instead of silently working around visual ambiguity.

### 4. Restart OpenCode

The @observer subagent and paste-interception plugin activate on restart.

## What It Enables

- **Paste screenshots directly** — copy an error log, UI bug, or design mockup to your clipboard and paste it into chat. Observer extracts the text, locates issues, and suggests fixes.
- **Verify UI changes** — the supervisor captures browser/app state (via playwright or macos-use), spawns @observer to compare before/after, and confirms fixes.
- **Extract error logs** — paste a screenshot of a stack trace or terminal error. Observer extracts every line word-for-word, identifies key files and line numbers.
- **Compare mockups to implementation** — paste a design mockup alongside a screenshot of your implementation. Observer compares element-by-element and flags discrepancies.
- **Quick visual checks** — "what's on screen right now?" — Observer gives a 2-3 sentence triage before deeper analysis.

## Requirements

- [OpenCode](https://opencode.ai) installed
- An [Anthropic API key](https://console.anthropic.com/) (Claude Sonnet 4.6)
- The `@ai-sdk/anthropic` npm package: `npm install @ai-sdk/anthropic` (in `~/.config/opencode/`)

## Cost

Observer uses Claude Sonnet 4.6 (~$3/M input tokens, ~$15/M output tokens). Observer reads 1-2 images per request and returns structured text — typical image analysis is a few hundred tokens. At typical observer volume (pasting screenshots, verifying UI), costs are negligible.

## Advanced Extensions

Observer works standalone — paste an image, get analysis. For deeper automation, combine it with these tools (project-specific, not included):

- **playwright** — programmatic browser screenshots. Supervisor captures a page, Observer verifies the UI.
- **macos-use** — macOS desktop automation. Supervisor captures native app state, Observer identifies issues.
- **screenpipe** — 24/7 screen/audio history. Supervisor searches past screenshots, Observer interprets historical UI states.

These tools are configured separately in the Supervisor's main setup. Observer slots into any workflow that produces image paths.
