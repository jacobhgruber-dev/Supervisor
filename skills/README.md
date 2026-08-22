# Skills

This repo ships the **Blessed Portable Set of 22 skills** as self-contained file trees — 19 motion/design skills + 3 utility skills (`agent-reach`, `anna`, `use-railway`). Each skill is a specialized instruction set that extends agent capabilities; opencode loads them on demand when a task matches the skill's description.

## What are Skills?

Skills are specialized instruction sets that extend agent capabilities. In opencode, skills live in `~/.config/opencode/skills/` and are loaded on demand when a task matches their description.

## Bundled Skills

### Motion & Design (19)

| Skill | Purpose |
|---|---|
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
| `gsap-core` | Official GSAP core API skill — `gsap.to()`/`from()`/`fromTo()`, easing, duration, stagger, defaults, `gsap.matchMedia()`. |
| `motion-design` | Motion design principles for emotionally-driven, technically sound animation — timing, easing, choreography, Disney principles adapted for UI. |
| `design-system` | Three-layer token architecture (primitive→semantic→component), CSS variables, spacing/typography scales, component specs. |
| `ui-styling` | shadcn/ui + Tailwind patterns — accessible components, theming, dark mode, consistent styling. |

### Utility (3)

| Skill | Purpose |
|---|---|
| `agent-reach` | Multi-platform web research/social search — 小红书, X/Twitter, Bilibili, Reddit, LinkedIn, GitHub, YouTube, podcasts, RSS, and more (community CLI tool). |
| `anna` | Search and download books and academic articles from Anna's Archive (invoked via `/anna`). |
| `use-railway` | Operate Railway infrastructure — projects, services, databases, buckets, deploys, environments, domains, feature flags, agent tooling. |

## Exclusion Policy (Strict)

- Private/local OSINT skills are NEVER bundled: `people-osint`, `people-search`, `image-osint` — they are personal investigation tooling with local credentials/workflows; they stay in the user's `~/.opencode/skills/` only.
- Complex skills with broken absolute-path dependencies are excluded: `banner-design`, `brand`, `design`, `slides`, `ui-ux-pro-max` — they carry hardcoded local paths and are not portable.
- Portability rule: a skill is bundled only if its tree is self-contained (no absolute paths, no symlinks) and it loads correctly on any machine.

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
