# Grok Worker — Now Bundled in Core

Grok Worker is no longer an addon. It is included out of the box in the core agent set as [`agents/grok-worker.md`](../../agents/grok-worker.md), running on **Grok 4.6** (`xai/grok-4.6`). There is nothing to copy — the Supervisor can spawn it as soon as your xAI key is configured.

## Activation (1 step)

### Add your xAI key

In OpenCode Desktop: **Settings → Providers → xAI** → paste your API key.

Or CLI: `opencode auth login` → choose xAI → paste key.

Get a key at [console.x.ai](https://console.x.ai). No provider block needed in opencode.json — xAI is a built-in provider that OpenCode handles natively through models.dev.

Once the key is set, say *"send this to the grok-worker"* and the Supervisor will spawn Grok 4.6.

## Cost

You pay xAI directly for Grok usage. Use it deliberately — DeepSeek (junior) and Claude (mid/senior) cover almost everything.
