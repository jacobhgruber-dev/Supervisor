export const title = "Observer Bridge";

import { randomUUID } from "node:crypto"
import { mkdirSync, readdirSync, statSync, unlinkSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"

const tempDir = join(tmpdir(), "opencode")
mkdirSync(tempDir, { recursive: true })

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

const supportsImage = new Map()
const injectedSessions = new Set()

export default async function () {
  return {
    "experimental.chat.system.transform": async (input, output) => {
      const capable = input.model?.capabilities?.input?.image ?? false
      if (input.sessionID) {
        supportsImage.set(input.sessionID, capable)
      }
      if (!capable && input.sessionID && !injectedSessions.has(input.sessionID)) {
        injectedSessions.add(input.sessionID)
        output.system.push(
          "## Visual Understanding (Images, Screenshots, Desktop State)\n" +
          "You are a text-only model. You cannot see images directly. Use the @observer subagent for all visual tasks.\n\n" +
          "### When to use @observer\n" +
          "- A message contains `[Image saved to: <path>]` — the user pasted an image. Call @observer immediately.\n" +
          "- A macos-automator tool response contains a screenshot path — call @observer to understand the UI state.\n" +
          "- A screenpipe search result references screenshots — call @observer to interpret them.\n" +
          "- You need to compare two screenshots (e.g., before/after a UI change) — pass both paths to @observer.\n\n" +
          "### How to call @observer\n" +
          "Spawn @observer as a subagent with a message like:\n" +
          "  \"Read the image at /tmp/macos-automator/screenshot_12345.png and tell me what the UI looks like.\"\n\n" +
          "### Verification loop (for UI changes)\n" +
          "1. Use playwright (web) or macos-automator (native) to capture the app state\n" +
          "2. Spawn @observer with the screenshot path to analyze visual state\n" +
          "3. Compare with expected behavior\n" +
          "4. Fix discrepancies, repeat from step 1",
        )
      }
    },

    "chat.message": async (input, output) => {
      const capable = supportsImage.get(input.sessionID)
      if (capable) return

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

        try {
          writeFileSync(filepath, Buffer.from(base64, "base64"))
          output.parts[i] = {
            type: "text",
            text: `[Image saved to: ${filepath}]`,
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

      if (imageFound) {
        const userText = output.parts
          .filter(p => p.type === "text" && !p.synthetic)
          .map(p => p.text)
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

        output.parts.push({
          type: "agent",
          name: "observer",
          synthetic: true,
          id: "prt_" + randomUUID(),
          sessionID: input.sessionID,
          messageID: input.messageID,
        })
      }
    },
  }
}
