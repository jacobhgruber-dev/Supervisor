export const title = "Observer Bridge";

import { randomUUID } from "node:crypto"
import { mkdirSync, readFileSync, readdirSync, statSync, unlinkSync, writeFileSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"

// Pasted images are persisted here before being handed to the observer
// subagent. The literal /tmp path is intentional: it is stable across
// platforms and is the /tmp/opencode convention the observer
// instructions reference.
const tempDir = join("/", "tmp", "opencode")
mkdirSync(tempDir, { recursive: true })

// Clean up stale pasted images older than one hour.
const MAX_AGE_MS = 3600_000
try {
  for (const name of readdirSync(tempDir)) {
    const filepath = join(tempDir, name)
    try {
      if (Date.now() - statSync(filepath).mtimeMs > MAX_AGE_MS) {
        unlinkSync(filepath)
      }
    } catch {}
  }
} catch {}

// Text-only providers that need the observer bridge. Defaults to "deepseek";
// override with OBSERVER_BRIDGE_PROVIDERS="providerA,providerB".
const bridgeProviders = (process.env.OBSERVER_BRIDGE_PROVIDERS || "deepseek")
  .split(",")
  .map((name) => name.trim().toLowerCase())
  .filter(Boolean)

// opencode stores provider credentials in ~/.local/share/opencode/auth.json,
// keyed by provider id (e.g. {"google": {"type": "api", "key": "..."}}).
function loadAuth() {
  try {
    return JSON.parse(
      readFileSync(join(homedir(), ".local", "share", "opencode", "auth.json"), "utf8")
    )
  } catch {
    return {}
  }
}

function hasGoogle(config, auth) {
  return Boolean(config?.provider?.google) ||
    Boolean(process.env.GOOGLE_API_KEY) ||
    Boolean(auth?.google)
}

function hasAnthropic(config, auth) {
  return Boolean(config?.provider?.anthropic) ||
    Boolean(process.env.ANTHROPIC_API_KEY) ||
    Boolean(auth?.anthropic)
}

// Resolve the active observer agent: Google (Gemini) wins over Anthropic
// (Claude Sonnet 5). Returns null when no vision provider is connected.
function resolveObserver(config, auth) {
  if (hasGoogle(config, auth)) return "observer"
  if (hasAnthropic(config, auth)) return "observer-claude"
  return null
}

const supportsImage = new Map()
const injectedSessions = new Set()

export default async function () {
  // The resolved opencode config arrives asynchronously via the config hook.
  let config = {}
  const auth = loadAuth()
  const observerName = () => resolveObserver(config, auth)

  function visionPrompt() {
    const name = observerName()
    if (!name) {
      return (
        "## Visual Understanding (Images, Screenshots, Desktop State)\n" +
        "You are a text-only model and no vision model is connected. You cannot see images " +
        "directly, and neither @observer nor @observer-claude is available. Do not spawn them.\n\n" +
        "### What to do instead\n" +
        "- Rely on text-based tool output: accessibility trees (macos-use traversal, playwright accessibility snapshot), logs, and extracted text.\n" +
        "- If a message contains `[Image saved to: <path>]`, the image was saved but cannot be analyzed — tell the user to configure a Google (Gemini) or Anthropic (Claude) key.\n" +
        "- For UI verification, compare accessibility snapshots or text output instead of screenshots."
      )
    }
    const agent = `@${name}`
    return (
      "## Visual Understanding (Images, Screenshots, Desktop State)\n" +
      `You are a text-only model. You cannot see images directly. Use the ${agent} subagent for all visual tasks.\n\n` +
      `### When to use ${agent}\n` +
      "- A message contains `[Image saved to: <path>]` — the user pasted an image. Call it immediately.\n" +
      "- A macos-use tool response contains a screenshot path — call it to understand the UI state.\n" +
      "- You need to compare two screenshots (e.g., before/after a UI change) — pass both paths to it.\n\n" +
      `### How to call ${agent}\n` +
      `Spawn ${agent} as a subagent with a message like:\n` +
      "  \"Read the image at /tmp/opencode/screenshot_12345.png and tell me what the UI looks like.\"\n\n" +
      "### Verification loop (for UI changes)\n" +
      "1. Use playwright (web) or macos-use (native) to capture the app state\n" +
      `2. Spawn ${agent} with the screenshot path to analyze visual state\n` +
      "3. Compare with expected behavior\n" +
      "4. Fix discrepancies, repeat from step 1"
    )
  }

  return {
    async config(cfg) {
      config = cfg ?? {}
    },

    "experimental.chat.system.transform": async (input, output) => {
      const capable = input.model?.capabilities?.input?.image === true
      if (input.sessionID) {
        supportsImage.set(input.sessionID, capable)
      }
      if (capable) return

      const provider = input.model?.providerID || input.model?.provider?.id || input.model?.provider
      const isBridgeProvider =
        typeof provider === "string" && bridgeProviders.includes(provider.trim().toLowerCase())
      if (!isBridgeProvider) return

      if (input.sessionID && !injectedSessions.has(input.sessionID)) {
        injectedSessions.add(input.sessionID)
        output.system.push(visionPrompt())
      }
    },

    "chat.message": async (input, output) => {
      const capable =
        input.model?.capabilities?.input?.image === true ||
        supportsImage.get(input.sessionID)
      if (capable) return

      const provider = input.model?.providerID || input.model?.provider?.id || input.model?.provider
      const isBridgeProvider =
        typeof provider === "string" && bridgeProviders.includes(provider.trim().toLowerCase())
      if (provider !== undefined && !isBridgeProvider) return

      let imageFound = false

      for (let i = output.parts.length - 1; i >= 0; i--) {
        const part = output.parts[i]
        if (part.type !== "file") continue
        if (!part.mime?.startsWith("image/")) continue
        if (!part.url?.startsWith("data:")) continue

        const base64 = part.url.split(",")[1]
        if (!base64) continue

        const ext = part.mime.split("/")[1]?.replace("jpeg", "jpg") || "png"
        const filename = `pasted_${randomUUID()}.${ext}`
        const filepath = join(tempDir, filename)
        const note = observerName() ? "" : " (Note: No vision key configured for @observer)"

        try {
          writeFileSync(filepath, Buffer.from(base64, "base64"))
          output.parts[i] = {
            type: "text",
            text: `[Image saved to: ${filepath}]${note}`,
            synthetic: true,
            id: "prt_" + randomUUID(),
            sessionID: input.sessionID,
            messageID: input.messageID,
          }
          imageFound = true
        } catch (err) {
          output.parts[i] = {
            type: "text",
            text: `[Image saved error: ${err.message}]`,
            synthetic: true,
            id: "prt_" + randomUUID(),
            sessionID: input.sessionID,
            messageID: input.messageID,
          }
        }
      }

      if (!imageFound) return

      const userText = output.parts
        .filter((p) => p.type === "text" && !p.synthetic)
        .map((p) => p.text)
        .join("\n")
        .slice(0, 300)

      if (userText) {
        output.parts.push({
          type: "text",
          text: `[User query message: ${userText}]`,
          synthetic: true,
          id: "prt_" + randomUUID(),
          sessionID: input.sessionID,
          messageID: input.messageID,
        })
      }

      const name = observerName()
      if (name) {
        output.parts.push({
          type: "agent",
          name,
          synthetic: true,
          id: "prt_" + randomUUID(),
          sessionID: input.sessionID,
          messageID: input.messageID,
        })
      }
    },
  }
}
