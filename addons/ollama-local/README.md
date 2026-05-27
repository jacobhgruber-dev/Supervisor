# Ollama Local — On-Device Models

Run AI models 100% on your device via [Ollama](https://ollama.com). No cloud API calls, no data leaving your machine, no per-token costs. Two local subagents: a coder and a reasoner.

## Why Local Models?

- **Privacy** — code, documents, and conversations never leave your device
- **Cost** — zero per-token charges after the initial model download
- **Offline** — works without internet once models are pulled
- **Speed** — no network latency for straightforward tasks

Local models aren't as capable as cloud-tier models (DeepSeek, Claude, Grok) for complex work, but they excel at straightforward coding, analysis, and planning where you want privacy or zero cost.

## Setup

### 1. Install Ollama

```bash
brew install ollama
```

Or download from [ollama.com](https://ollama.com).

### 2. Pull Recommended Models

These are the models this addon is configured for. Pull the ones you want:

```bash
# Primary recommendation — coding specialist (fast, good for everyday tasks)
ollama pull freehuntx/qwen3-coder:14b

# General-purpose models (27B parameters, higher quality but slower)
ollama pull qwen3.6:27b
ollama pull qwen3.6:27b-coding-nvfp4

# Quantized variants (smaller, faster, slightly lower quality)
ollama pull batiai/qwen3.6-27b:q4
ollama pull batiai/qwen3.6-27b:q3

# Reasoning model (good for analysis and planning)
ollama pull gemma4:e4b
```

### 3. Add Ollama to Your opencode.json

Add this provider block to your `opencode.json`:

```json
"ollama": {
  "npm": "@ai-sdk/openai-compatible",
  "name": "Ollama (local)",
  "options": {
    "baseURL": "http://localhost:11434/v1"
  },
  "models": {
    "freehuntx/qwen3-coder:14b": {
      "tools": true,
      "name": "Qwen3 Coder 14B"
    },
    "qwen3.6:27b": {
      "tools": true,
      "name": "Qwen 3.6 27B"
    },
    "qwen3.6:27b-coding-nvfp4": {
      "tools": true,
      "name": "Qwen 3.6 27B Coding (nvfp4)"
    },
    "gemma4:e4b": {
      "tools": true,
      "name": "Gemma 4 (e4b)"
    },
    "batiai/qwen3.6-27b:q4": {
      "tools": true,
      "name": "Qwen 3.6 27B Q4"
    },
    "batiai/qwen3.6-27b:q3": {
      "tools": true,
      "name": "Qwen 3.6 27B Q3"
    }
  }
}
```

### 4. Copy the Local Agent Files

```bash
cp agents/local-coder.md ~/.config/opencode/agents/
cp agents/local-reasoner.md ~/.config/opencode/agents/
```

### 5. Restart OpenCode

The agents `local-coder` and `local-reasoner` will be available for the supervisor to spawn.

## The Local Agents

| Agent | Model | Use For | Permissions |
|-------|-------|---------|-------------|
| `local-coder` | Qwen3 Coder 14B | Coding tasks — write, edit, debug, refactor | Full access (edit + bash + web) |
| `local-reasoner` | Gemma 4 (e4b) | Analysis, planning, evaluation — think and report | Read-only + web |

### When to Use Each

**Use `local-coder`** for straightforward implementation tasks where you want privacy or zero cost:
- Writing boilerplate, utilities, or simple components
- Fixing typos, formatting, or small bugs
- Tasks where the pattern is clear and you just need execution

**Use `local-reasoner`** for analysis tasks that should stay on-device:
- Planning and structuring before implementing
- Evaluating approaches or summarizing code
- Any analysis of sensitive or proprietary code

**Use cloud agents (DeepSeek/Claude)** when the task requires deeper reasoning — local models are good but not frontier.

## Model Recommendations

### Start Here: `freehuntx/qwen3-coder:14b`

The best balance of speed, quality, and resource usage. Purpose-built for code. Install first.

```
ollama pull freehuntx/qwen3-coder:14b
```

### General Purpose: `qwen3.6:27b`

Higher quality for analysis and planning. Needs more RAM but produces better results on complex reasoning.

```
ollama pull qwen3.6:27b
```

### Coding Specialist: `qwen3.6:27b-coding-nvfp4`

Same 27B base model, fine-tuned for coding, with nvfp4 quantization for better performance on compatible hardware.

```
ollama pull qwen3.6:27b-coding-nvfp4
```

### Quantized Variants (Smaller/Faster)

If the 27B models are too large for your hardware:

```bash
ollama pull batiai/qwen3.6-27b:q4    # 4-bit quantized (~16 GB RAM needed)
ollama pull batiai/qwen3.6-27b:q3    # 3-bit quantized (~12 GB RAM needed)
```

### Reasoning: `gemma4:e4b`

Google's Gemma 4 at the e4b size. Good for structured analysis, planning, and evaluation. Lighter than the 27B models.

```
ollama pull gemma4:e4b
```

### Model-to-Agent Mapping

To switch which model an agent uses, edit the `model:` field in the agent's `.md` file. For example, to upgrade `local-coder` from Qwen3 Coder 14B to Qwen 3.6 27B:

```yaml
# In local-coder.md, change:
model: ollama/freehuntx/qwen3-coder:14b
# To:
model: ollama/qwen3.6:27b-coding-nvfp4
```

Restart opencode for the change to take effect.

## Resource Requirements

| Model | Approx. RAM | Approx. Disk |
|-------|------------|-------------|
| Qwen3 Coder 14B | 10 GB | 9 GB |
| Gemma 4 (e4b) | 10 GB | 9 GB |
| Qwen 3.6 27B Q3 | 14 GB | 17 GB |
| Qwen 3.6 27B Q4 | 18 GB | 17 GB |
| Qwen 3.6 27B | 22 GB | 17 GB |

Apple Silicon Macs with 16 GB RAM can run the 14B models comfortably. For 27B models, 32 GB+ RAM recommended.
