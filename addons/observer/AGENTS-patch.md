<!--
  AGENTS-PATCH: Visual Context Awareness
  Merge this block into your ~/.config/opencode/AGENTS.md file.
  Place it after the existing "API keys" section (or wherever makes sense in your config).
  This teaches subagents to ask the supervisor for visual help instead of
  silently working around images they can't see.
-->

## Visual Context Awareness

The supervisor has access to visual tools that subagents do not:

| Tool | What it does |
|---|---|
| **playwright** | Browser screenshots, DOM snapshots, console logs |
| **@observer** (Claude Sonnet 4.6) | Reads screenshots and returns structured text analysis |
| **macos-use** | macOS desktop control — captures UI state of native apps |
| **screenpipe** | Searches 24/7 screen/audio history for past activity |

### When to ask the supervisor for visual context

As a subagent, flag when visual verification would help your work:
- "I need to know what this UI looks like right now" → ask supervisor to capture via playwright/macos-use
- "What was on screen when this error occurred at 14:32?" → ask supervisor to search screenpipe
- "Does this mockup match the implementation?" → ask supervisor to run @observer comparison
- "I'm investigating a visual bug but can't see screenshots" → ask supervisor to analyze and describe

The supervisor will fetch the visual context and include it in your prompt or follow-up message. Do not silently work around visual ambiguity — ask.
