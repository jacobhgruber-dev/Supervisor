# Skills (No Pre-Bundled Skills Included)

This repo focuses on the agent orchestration system. Skills (custom workflows for specific domains) are separate.

## What are Skills?

Skills are specialized instruction sets that extend agent capabilities. In opencode, skills live in `~/.config/opencode/skills/` and are loaded on demand when a task matches their description.

## Examples of Skills You Might Add

- **Firecrawl** — web scraping, search, and structured data extraction
- **ElevenLabs** — music and audio generation
- **Stripe** — payment integration best practices
- **PDF/Document parsing** — convert local files to markdown
- **Custom workflows** — any domain-specific tool chain you build

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
