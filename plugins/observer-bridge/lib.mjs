// Core logic for the observer-bridge V2 plugin. Kept separate from index.js
// because index.js imports "@opencode/plugin", a module the OpenCode host
// injects for loaded plugins (no package.json/node_modules is shown anywhere
// in the V2 docs for local plugins) and which does not resolve under a plain
// `node` process. Testing this file directly (with a mock ctx) avoids that
// problem entirely; see scripts/test_observer_bridge.mjs.
import { randomUUID } from "node:crypto"
import { mkdirSync, readdirSync, statSync, unlinkSync, writeFileSync } from "node:fs"
import { join } from "node:path"

// Pasted images are persisted here before being handed to the observer
// subagent. The literal /tmp path is intentional: it is stable across
// platforms and is the /tmp/opencode convention the observer instructions
// reference. OBSERVER_BRIDGE_TMPDIR exists only so tests can redirect this
// to an isolated scratch directory; it is unset in real deployments.
function resolveTempDir() {
  return process.env.OBSERVER_BRIDGE_TMPDIR || join("/", "tmp", "opencode")
}

// Clean up stale pasted images older than one hour. Only our own files
// (pasted_*) are ever touched: /tmp/opencode is a shared convention also
// used by macos-use/playwright screenshot capture and other tooling, and
// this plugin must not delete files it didn't create.
const MAX_AGE_MS = 3600_000
const PASTED_PREFIX = "pasted_"

function cleanupStale(tempDir) {
  // mode: 0o700 only takes effect when mkdirSync actually creates the
  // directory; if tempDir already exists, Node's recursive mkdir is a no-op
  // and leaves its existing mode untouched (no chmod is issued here or
  // anywhere else in this file).
  mkdirSync(tempDir, { recursive: true, mode: 0o700 })
  try {
    for (const name of readdirSync(tempDir)) {
      if (!name.startsWith(PASTED_PREFIX)) continue
      const filepath = join(tempDir, name)
      try {
        if (Date.now() - statSync(filepath).mtimeMs > MAX_AGE_MS) {
          unlinkSync(filepath)
        }
      } catch {}
    }
  } catch {}
}

// Text-only providers that need the observer bridge. Defaults to "deepseek";
// override with OBSERVER_BRIDGE_PROVIDERS="providerA,providerB".
function resolveBridgeProviders() {
  return (process.env.OBSERVER_BRIDGE_PROVIDERS || "deepseek")
    .split(",")
    .map((name) => name.trim().toLowerCase())
    .filter(Boolean)
}

function isBridgeProvider(providerID, bridgeProviders) {
  return typeof providerID === "string" && bridgeProviders.includes(providerID.trim().toLowerCase())
}

// V1 read ~/.local/share/opencode/auth.json directly. V2 exposes connection
// state through ctx.integration.connection.active(integrationID), which (per
// Connection.Info = CredentialInfo | EnvInfo in the V2 API) already accounts
// for env-var-sourced credentials. The direct process.env checks below are
// kept anyway as zero-cost, belt-and-suspenders redundancy matching V1's
// original three-signal check (config block, env var, stored credential) —
// the V1 config-block signal (`config?.provider?.google`) has no direct V2
// equivalent (no monolithic readable config object) and is dropped as
// superseded by the integration API, which is the host's own authoritative
// "is this provider connected" check.
async function hasGoogle(ctx) {
  if (process.env.GOOGLE_API_KEY) return true
  try {
    return Boolean(await ctx.integration.connection.active("google"))
  } catch (err) {
    console.error("[observer-bridge] integration.connection.active(google) failed:", err?.message || err)
    return false
  }
}

async function hasAnthropic(ctx) {
  if (process.env.ANTHROPIC_API_KEY) return true
  try {
    return Boolean(await ctx.integration.connection.active("anthropic"))
  } catch (err) {
    console.error("[observer-bridge] integration.connection.active(anthropic) failed:", err?.message || err)
    return false
  }
}

// Resolve the active observer agent: Google (Gemini) wins over Anthropic
// (Claude Sonnet 5). Returns null when no vision provider is connected.
async function resolveObserver(ctx) {
  if (await hasGoogle(ctx)) return "observer"
  if (await hasAnthropic(ctx)) return "observer-claude"
  return null
}

function visionPrompt(name) {
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
    '  "Read the image at /tmp/opencode/screenshot_12345.png and tell me what the UI looks like."\n\n' +
    "### Verification loop (for UI changes)\n" +
    "1. Use playwright (web) or macos-use (native) to capture the app state\n" +
    `2. Spawn ${agent} with the screenshot path to analyze visual state\n` +
    "3. Compare with expected behavior\n" +
    "4. Fix discrepancies, repeat from step 1"
  )
}

// V1 read input.model?.capabilities?.input?.image (a boolean) directly off
// the hook input. V2's session hooks only carry {providerID, id, variant?}
// for the model — no capabilities — so this cross-references ctx.model.list()
// (Model.Info[], where capabilities.input is a string[] such as ["text",
// "image"]). Provider id is compared case-insensitively, consistent with
// isBridgeProvider, since the hook-supplied providerID and the catalog's
// providerID are not guaranteed to share casing. Matches `id` or `modelID`
// since the exact bare-vs-composite id convention isn't pinned down by the
// V2 docs (Model.Info has both fields; Model.Ref only has `id`) — kept both
// deliberately since this remains unconfirmed, not dead code.
// Returns true, false, or undefined (unknown — e.g. model not in the catalog).
async function isImageCapable(ctx, providerID, modelID) {
  if (!providerID || !modelID) return undefined
  let models
  try {
    models = await ctx.model.list()
  } catch (err) {
    console.error("[observer-bridge] model.list failed:", err?.message || err)
    return undefined
  }
  if (!Array.isArray(models)) return undefined
  const normalizedProviderID = String(providerID).trim().toLowerCase()
  const match = models.find(
    (m) =>
      typeof m?.providerID === "string" &&
      m.providerID.trim().toLowerCase() === normalizedProviderID &&
      (m?.id === modelID || m?.modelID === modelID),
  )
  if (!match) return undefined
  return Array.isArray(match.capabilities?.input) && match.capabilities.input.includes("image")
}

// Allowlist mapping mime type -> safe file extension. The extension is never
// derived by splitting/parsing the mime string: an attacker-controlled mime
// such as "image/../../etc/passwd" or "image/x\..\..\evil" must not be able
// to influence the filename beyond falling back to the default "png".
const IMAGE_EXTENSIONS = {
  "image/png": "png",
  "image/jpeg": "jpg",
  "image/gif": "gif",
  "image/webp": "webp",
  "image/bmp": "bmp",
  "image/tiff": "tiff",
  "image/svg+xml": "svg",
  "image/heic": "heic",
  "image/heif": "heif",
  "image/avif": "avif",
}

function extensionForMime(mime) {
  return IMAGE_EXTENSIONS[String(mime).toLowerCase()] ?? "png"
}

// Parse a base64 data: URI from a V2 prompt file attachment's `uri` field
// (PromptInput.FileAttachment has no separate `mime` field — mime must come
// from the URI itself). Returns null for file://, http(s), or non-base64
// data URIs (those already flow through the normal attachment pipeline) and
// for non-image mime types.
function parseImageDataUri(uri) {
  if (typeof uri !== "string" || !uri.startsWith("data:")) return null
  const comma = uri.indexOf(",")
  if (comma === -1) return null
  const header = uri.slice("data:".length, comma)
  if (!header.endsWith(";base64")) return null
  const mime = header.slice(0, -";base64".length)
  if (!mime.startsWith("image/")) return null
  const data = uri.slice(comma + 1)
  if (!data) return null
  return { mime, data }
}

export async function setup(ctx) {
  const tempDir = resolveTempDir()
  cleanupStale(tempDir)

  const bridgeProviders = resolveBridgeProviders()

  // V1 "experimental.chat.system.transform" -> V2 "context" hook.
  //
  // No once-per-session gate: per the V2 server docs, "context" hook edits
  // "affect only the outgoing model call, not persisted history or
  // configuration" and "context runs for the agent loop, including
  // tool-driven continuations" — i.e. it fires on every model request in a
  // session, and nothing we push here carries over to the next request. A
  // once-per-session gate (the V1 approach) would make the instruction
  // appear in the first request's system prompt only and silently vanish
  // from every later request in the same session. Injecting unconditionally
  // on every qualifying call is therefore the correct V2 behavior, not a
  // performance shortcut gone wrong — it's still idempotent in the sense
  // that matters: each call pushes exactly one instruction into that call's
  // own (fresh, non-accumulating) system array.
  const contextReg = await ctx.session.hook("context", async (event) => {
    const providerID = event.model?.providerID
    const modelID = event.model?.id
    const capable = await isImageCapable(ctx, providerID, modelID)
    if (capable === true) return
    if (!isBridgeProvider(providerID, bridgeProviders)) return

    const name = await resolveObserver(ctx)
    event.system.push({ type: "text", text: visionPrompt(name) })
  })

  // V1 "chat.message" -> V2 "prompt" hook. No model is resolved yet at
  // prompt-admission time, so look up the session's configured model
  // instead of reading it off the event (the prompt hook also doesn't
  // accept a providerID scoping option, confirming model resolution hasn't
  // happened yet at this stage).
  const promptReg = await ctx.session.hook("prompt", async (event) => {
    const files = event.prompt?.files
    if (!Array.isArray(files) || files.length === 0) return

    const remaining = []
    const imageFiles = []
    for (const file of files) {
      const parsed = parseImageDataUri(file?.uri)
      if (parsed) imageFiles.push(parsed)
      else remaining.push(file)
    }
    if (imageFiles.length === 0) return

    const sessionID = event.sessionID
    let providerID
    let modelID
    try {
      const session = await ctx.session.get({ sessionID })
      providerID = session?.model?.providerID
      modelID = session?.model?.id
    } catch (err) {
      console.error("[observer-bridge] session.get failed:", err?.message || err)
    }

    const capable = await isImageCapable(ctx, providerID, modelID)
    if (capable === true) return
    // Safe direction, symmetric with the context hook above: only bridge
    // when the provider is both resolved AND explicitly listed as a bridge
    // provider. isBridgeProvider(undefined, ...) is false, so if
    // session.get() threw or the session has no model yet, we leave the
    // prompt untouched rather than guessing — a possibly image-capable
    // model keeps its image, and the native V2 "unsupported attachment"
    // fallback applies if it turns out not to support it.
    if (!isBridgeProvider(providerID, bridgeProviders)) return

    const name = await resolveObserver(ctx)
    const note = name ? "" : " (Note: No vision key configured for @observer)"
    const notes = []
    for (const parsed of imageFiles) {
      const ext = extensionForMime(parsed.mime)
      const filename = `${PASTED_PREFIX}${randomUUID()}.${ext}`
      const filepath = join(tempDir, filename)
      try {
        writeFileSync(filepath, Buffer.from(parsed.data, "base64"), { mode: 0o600 })
        notes.push(`[Image saved to: ${filepath}]${note}`)
      } catch (err) {
        notes.push(`[Image saved error: ${err.message}]`)
      }
    }

    event.prompt.files = remaining
    // Append only — never prepend. Existing mention offsets (Prompt.Mention
    // start/end) index into event.prompt.text; prepending would shift them.
    event.prompt.text = `${event.prompt.text ?? ""}\n\n${notes.join("\n")}`

    if (name) {
      event.prompt.agents = Array.isArray(event.prompt.agents) ? event.prompt.agents : []
      event.prompt.agents.push({ name })
    }
  })

  return async () => {
    const results = await Promise.allSettled([contextReg.dispose(), promptReg.dispose()])
    for (const result of results) {
      if (result.status === "rejected") {
        console.error("[observer-bridge] hook dispose failed:", result.reason?.message || result.reason)
      }
    }
  }
}
