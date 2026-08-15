# Skills

This repo ships 18 bundled skills as self-contained file trees — no absolute-path symlinks. Each skill is a specialized instruction set that extends agent capabilities; opencode loads them on demand when a task matches the skill's description.

## What are Skills?

Skills are specialized instruction sets that extend agent capabilities. In opencode, skills live in `~/.config/opencode/skills/` and are loaded on demand when a task matches their description.

## Bundled Skills

| Skill | Purpose |
|---|---|
| `agent-reach` | Multi-platform web research/social search — 小红书, X/Twitter, Bilibili, Reddit, LinkedIn, GitHub, YouTube, podcasts, RSS, and more (community CLI tool). |
| `animate` | Build an animation from scratch, deciding in craft order: should it animate, what purpose, which tool, properties, curve, duration, interrupts, exits. |
| `animation-vocabulary` | Reverse-lookup glossary: turn a vague description of a motion effect into its exact term (e.g., "the bouncy thing when a popover opens" → Pop in). |
| `apple-design` | Apple's approach to interface design and fluid, physical motion translated for the web — gesture-driven UI, springs, sheets, materials, typography. |
| `ask-sonner` | Sonner React toast library guide — setup, toast variants, promises, styling, theming, positioning, and troubleshooting. |
| `emil-design-eng` | Emil Kowalski's philosophy on UI polish, component design, animation decisions, and the invisible details that make software feel great. |
| `find-animation-opportunities` | Read-only search of a codebase for places that don't animate but should — proposes exact motion values, rejects what shouldn't move. |
| `framer-motion-gestures` | Official Framer Motion skill for gesture animations — drag, pan, tap, hover, focus, touch. |
| `framer-motion-layout` | Official Framer Motion skill for layout animations — shared transitions, `layoutId`, exit animations, `AnimatePresence`. |
| `framer-motion-react` | Official Framer Motion skill for React integration — `AnimatePresence`, motion components, `useAnimation`, SSR. |
| `framer-motion-scroll` | Official Framer Motion skill for scroll-linked animations — `useScroll`, `useTransform`, scroll-triggered effects, parallax. |
| `framer-motion-variants` | Official Framer Motion skill for animation variants — state machines, orchestration, stagger, repeat, sequencing. |
| `improve-animations` | Codebase-wide motion audit by a senior motion advisor — prioritized roadmap and self-contained implementation plans. |
| `review-animations` | Reviews animation/motion code against a high craft bar (Emil Kowalski's design engineering philosophy). Defaults to flagging. |
| `pick-ui-library` | Pick the right library for a frontend task from a curated, opinionated list — inputs, charts, command menus, virtualization, drag-and-drop, toasts, state. |
| `prototype` | Build multiple genuinely different UI variants behind a live visual picker so you can flip through them and promote the one that feels right. |
| `use-railway` | Operate Railway infrastructure — projects, services, databases, buckets, deploys, environments, domains, feature flags, agent tooling. |
| `anna` | Search and download books and academic articles from Anna's Archive (invoked via `/anna`). |

## How to Add a Skill

Skills follow a standard structure:

```
~/.config/opencode/skills/
└── my-skill/
    ├── SKILL.md          # Main instructions (required)
    └── references/       # Supporting docs (optional)
        └── api_ref.md
```

The `SKILL.md` file contains:
- A description that determines when the skill is auto-loaded
- Step-by-step workflow instructions
- References to supporting tools and scripts

See the [OpenCode documentation](https://opencode.ai/docs) for details on creating custom skills.
