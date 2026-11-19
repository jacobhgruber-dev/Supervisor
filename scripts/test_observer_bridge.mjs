// Plain node:test + node:assert test for plugins/observer-bridge/lib.mjs.
// Run: node scripts/test_observer_bridge.mjs
//
// Tests lib.mjs directly, not index.js: index.js imports "@opencode/plugin",
// a module the OpenCode host injects for loaded plugins and which does not
// resolve under a plain `node` process (no package.json/node_modules is
// shown for local plugins anywhere in the V2 docs). lib.mjs has zero
// non-builtin imports, so it is fully testable with a mock ctx.
import assert from "node:assert/strict"
import { test } from "node:test"
import { chmodSync, existsSync, mkdtempSync, readFileSync, rmSync, statSync, utimesSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join, resolve } from "node:path"
import { setup } from "../plugins/observer-bridge/lib.mjs"

function makeCtx({ connections = {}, models = [], sessions = {} } = {}) {
  const hooks = {}
  const disposed = {}
  const calls = { integrationActive: [], modelList: 0, sessionGet: [] }
  return {
    hooks,
    disposed,
    calls,
    session: {
      hook: async (name, cb) => {
        hooks[name] = cb
        disposed[name] = false
        return {
          dispose: async () => {
            disposed[name] = true
          },
        }
      },
      get: async ({ sessionID }) => {
        calls.sessionGet.push(sessionID)
        const s = sessions[sessionID]
        if (!s) throw new Error(`mock: no such session: ${sessionID}`)
        return s
      },
    },
    integration: {
      connection: {
        active: async (id) => {
          calls.integrationActive.push(id)
          return connections[id]
        },
      },
    },
    model: {
      list: async () => {
        calls.modelList++
        return models
      },
    },
  }
}

function dataUri(mime, bytes) {
  return `data:${mime};base64,${Buffer.from(bytes).toString("base64")}`
}

const deepseekModel = {
  providerID: "deepseek",
  id: "deepseek-flash",
  modelID: "deepseek-flash",
  capabilities: { input: ["text"], output: ["text"], tools: true },
}
const anthropicTextModel = {
  providerID: "anthropic",
  id: "claude-sonnet-5",
  modelID: "claude-sonnet-5",
  capabilities: { input: ["text"], output: ["text"], tools: true },
}
const anthropicImageModel = {
  providerID: "anthropic",
  id: "claude-sonnet-5",
  modelID: "claude-sonnet-5",
  capabilities: { input: ["text", "image"], output: ["text"], tools: true },
}

let scratchDirs = []
test.beforeEach(() => {
  const dir = mkdtempSync(join(tmpdir(), "observer-bridge-test-"))
  scratchDirs.push(dir)
  process.env.OBSERVER_BRIDGE_TMPDIR = dir
  delete process.env.OBSERVER_BRIDGE_PROVIDERS
  delete process.env.GOOGLE_API_KEY
  delete process.env.ANTHROPIC_API_KEY
})
test.afterEach(() => {
  delete process.env.OBSERVER_BRIDGE_TMPDIR
  for (const dir of scratchDirs) rmSync(dir, { recursive: true, force: true })
  scratchDirs = []
})

// --- (a) image stripped, saved with correct bytes/extension, note appended,
// observer chosen per credential matrix ---

test("(a) google connected: png saved, note appended (no missing-key note), observer chosen, text appended not prepended", async () => {
  const ctx = makeCtx({
    connections: { google: { id: "conn1" } },
    models: [deepseekModel],
    sessions: { s1: { model: { providerID: "deepseek", id: "deepseek-flash" } } },
  })
  await setup(ctx)
  const bytes = [137, 80, 78, 71, 1, 2, 3, 4]
  const event = {
    sessionID: "s1",
    prompt: { text: "look at this", files: [{ uri: dataUri("image/png", bytes) }], agents: [] },
  }
  await ctx.hooks.prompt(event)

  assert.equal(event.prompt.files.length, 0, "image removed from files")
  assert.ok(event.prompt.text.startsWith("look at this"), "original text preserved at the start (append, not prepend)")
  assert.match(event.prompt.text, /\[Image saved to: .*\.png\]/)
  assert.ok(!event.prompt.text.includes("No vision key"), "no missing-key note when google connected")
  assert.deepEqual(event.prompt.agents, [{ name: "observer" }])

  const savedPath = event.prompt.text.match(/\[Image saved to: (.*?)\]/)[1]
  assert.ok(existsSync(savedPath), "file exists on disk")
  assert.deepEqual([...readFileSync(savedPath)], bytes, "saved bytes match original")
  assert.ok(savedPath.endsWith(".png"))
})

test("(a) jpeg extension mapped to .jpg; anthropic-only credentials -> observer-claude", async () => {
  const ctx = makeCtx({
    connections: { anthropic: { id: "conn2" } },
    models: [deepseekModel],
    sessions: { s2: { model: { providerID: "deepseek", id: "deepseek-flash" } } },
  })
  await setup(ctx)
  const event = { sessionID: "s2", prompt: { text: "", files: [{ uri: dataUri("image/jpeg", [1, 2, 3]) }] } }
  await ctx.hooks.prompt(event)

  assert.deepEqual(event.prompt.agents, [{ name: "observer-claude" }])
  const savedPath = event.prompt.text.match(/\[Image saved to: (.*?)\]/)[1]
  assert.ok(savedPath.endsWith(".jpg"), `expected .jpg, got ${savedPath}`)
})

test("(a) neither credential connected: no agent pushed, missing-key note added", async () => {
  const ctx = makeCtx({
    connections: {},
    models: [deepseekModel],
    sessions: { s3: { model: { providerID: "deepseek", id: "deepseek-flash" } } },
  })
  await setup(ctx)
  const event = { sessionID: "s3", prompt: { text: "hi", files: [{ uri: dataUri("image/png", [9, 9]) }] } }
  await ctx.hooks.prompt(event)

  assert.equal(event.prompt.agents, undefined, "no agents array created when no observer available")
  assert.ok(event.prompt.text.includes("(Note: No vision key configured for @observer)"))
})

test("(a) multiple images in one prompt are all saved and noted", async () => {
  const ctx = makeCtx({
    connections: { google: {} },
    models: [deepseekModel],
    sessions: { s1b: { model: { providerID: "deepseek", id: "deepseek-flash" } } },
  })
  await setup(ctx)
  const event = {
    sessionID: "s1b",
    prompt: {
      text: "two images",
      files: [{ uri: dataUri("image/png", [1]) }, { uri: dataUri("image/jpeg", [2]) }],
    },
  }
  await ctx.hooks.prompt(event)
  assert.equal(event.prompt.files.length, 0)
  const matches = [...event.prompt.text.matchAll(/\[Image saved to: (.*?)\]/g)]
  assert.equal(matches.length, 2)
  assert.deepEqual(event.prompt.agents, [{ name: "observer" }], "agent pushed once, not once per image")
})

// --- (1) path traversal via mime-derived extension (BLOCKING fix) ---

test("(1) malicious mime cannot escape tempDir and only ever yields an allowlisted extension", async () => {
  const ctx = makeCtx({
    connections: { google: {} },
    models: [deepseekModel],
    sessions: { sT1: { model: { providerID: "deepseek", id: "deepseek-flash" } } },
  })
  await setup(ctx)
  const resolvedTempDir = resolve(process.env.OBSERVER_BRIDGE_TMPDIR)
  const maliciousMimes = ["image/x\\..\\..\\evil", "image/../../x", "image/../../../etc/passwd"]

  for (const mime of maliciousMimes) {
    const event = { sessionID: "sT1", prompt: { text: "", files: [{ uri: dataUri(mime, [1, 2, 3]) }] } }
    await ctx.hooks.prompt(event)
    const match = event.prompt.text.match(/\[Image saved to: (.*?)\]/)
    assert.ok(match, `expected a saved-image note for mime ${JSON.stringify(mime)}`)
    const savedPath = match[1]
    const resolvedSaved = resolve(savedPath)
    assert.ok(
      resolvedSaved.startsWith(resolvedTempDir + "/"),
      `file for mime ${JSON.stringify(mime)} escaped tempDir: ${resolvedSaved}`,
    )
    assert.match(
      savedPath,
      /\.(png|jpg|jpeg|gif|webp|bmp|tiff|svg|heic|heif|avif)$/,
      `expected an allowlisted extension for mime ${JSON.stringify(mime)}, got ${savedPath}`,
    )
    assert.ok(existsSync(savedPath), "file actually exists inside tempDir")
  }
})

test("(1) known mime types map to their expected extensions via the allowlist", async () => {
  const ctx = makeCtx({
    connections: { google: {} },
    models: [deepseekModel],
    sessions: { sT2: { model: { providerID: "deepseek", id: "deepseek-flash" } } },
  })
  await setup(ctx)
  const cases = [
    ["image/png", "png"],
    ["image/jpeg", "jpg"],
    ["image/gif", "gif"],
    ["image/webp", "webp"],
    ["image/svg+xml", "svg"],
  ]
  for (const [mime, ext] of cases) {
    const event = { sessionID: "sT2", prompt: { text: "", files: [{ uri: dataUri(mime, [1]) }] } }
    await ctx.hooks.prompt(event)
    const savedPath = event.prompt.text.match(/\[Image saved to: (.*?)\]/)[1]
    assert.ok(savedPath.endsWith(`.${ext}`), `mime ${mime} expected .${ext}, got ${savedPath}`)
  }
})

// --- (b) non-image files untouched ---

test("(b) non-image file attachments are left untouched", async () => {
  const ctx = makeCtx({
    connections: { google: {} },
    models: [deepseekModel],
    sessions: { s4: { model: { providerID: "deepseek", id: "deepseek-flash" } } },
  })
  await setup(ctx)
  const fileRef = { uri: "file:///project/README.md", name: "README.md" }
  const event = { sessionID: "s4", prompt: { text: "check this file", files: [fileRef] } }
  const beforeText = event.prompt.text
  await ctx.hooks.prompt(event)

  assert.equal(event.prompt.text, beforeText, "text untouched when no image present")
  assert.equal(event.prompt.files.length, 1)
  assert.equal(event.prompt.files[0], fileRef, "same object reference, untouched")
  assert.equal(ctx.calls.sessionGet.length, 0, "no session lookup needed when there are no images")
})

// --- (c) non-bridge provider / image-capable model: untouched ---

test("(c) non-bridge provider (anthropic, non-image model) leaves prompt untouched", async () => {
  const ctx = makeCtx({
    connections: { google: {}, anthropic: {} },
    models: [anthropicTextModel],
    sessions: { s5: { model: { providerID: "anthropic", id: "claude-sonnet-5" } } },
  })
  await setup(ctx)
  const event = { sessionID: "s5", prompt: { text: "look", files: [{ uri: dataUri("image/png", [1]) }] } }
  await ctx.hooks.prompt(event)

  assert.equal(event.prompt.files.length, 1, "image untouched for non-bridge provider")
  assert.equal(event.prompt.text, "look")
  assert.equal(event.prompt.agents, undefined)
})

test("(c) image-capable model leaves prompt untouched even for a bridge-listed provider", async () => {
  const ctx = makeCtx({
    connections: { anthropic: {} },
    models: [anthropicImageModel],
    sessions: { s5b: { model: { providerID: "anthropic", id: "claude-sonnet-5" } } },
  })
  await setup(ctx)
  process.env.OBSERVER_BRIDGE_PROVIDERS = "anthropic" // force anthropic into the bridge list
  const event = { sessionID: "s5b", prompt: { text: "look", files: [{ uri: dataUri("image/png", [1]) }] } }
  await ctx.hooks.prompt(event)

  assert.equal(event.prompt.files.length, 1, "image untouched when model reports image capability")
})

// --- (2) safe-direction prompt gating when the provider can't be resolved
// (HIGH fix — symmetric with the context hook) ---

test("(2) session.get throws -> prompt left untouched", async () => {
  const ctx = makeCtx({
    connections: { google: {} },
    models: [deepseekModel],
    sessions: {}, // "s8" intentionally absent -> session.get throws
  })
  await setup(ctx)
  const event = { sessionID: "s8", prompt: { text: "look", files: [{ uri: dataUri("image/png", [1]) }] } }
  await ctx.hooks.prompt(event)
  assert.equal(event.prompt.files.length, 1, "image left in place when the session can't be resolved")
  assert.equal(event.prompt.text, "look")
  assert.equal(event.prompt.agents, undefined)
})

test("(2) session without a model -> prompt left untouched", async () => {
  const ctx = makeCtx({
    connections: { google: {} },
    models: [deepseekModel],
    sessions: { s9: {} }, // resolves, but has no .model at all
  })
  await setup(ctx)
  const event = { sessionID: "s9", prompt: { text: "look", files: [{ uri: dataUri("image/png", [1]) }] } }
  await ctx.hooks.prompt(event)
  assert.equal(event.prompt.files.length, 1)
  assert.equal(event.prompt.text, "look")
  assert.equal(event.prompt.agents, undefined)
})

test("(2) resolved bridge provider is still bridged (sanity: the safe-direction fix didn't break the common path)", async () => {
  const ctx = makeCtx({
    connections: { google: {} },
    models: [deepseekModel],
    sessions: { s10: { model: { providerID: "deepseek", id: "deepseek-flash" } } },
  })
  await setup(ctx)
  const event = { sessionID: "s10", prompt: { text: "look", files: [{ uri: dataUri("image/png", [1]) }] } }
  await ctx.hooks.prompt(event)
  assert.equal(event.prompt.files.length, 0, "still bridged for a resolved, known bridge provider")
  assert.deepEqual(event.prompt.agents, [{ name: "observer" }])
})

// --- (d) system prompt injected exactly once per session, only for
// bridge-provider / non-image models ---

test("(d/6) context hook re-injects the vision instruction on every model request, not just the first", async () => {
  // V2 server docs ("Model requests"): context hook edits "affect only the
  // outgoing model call, not persisted history or configuration", and
  // "context runs for the agent loop, including tool-driven continuations".
  // A once-per-session gate would make the instruction vanish after the
  // session's first model call since nothing persists between calls —
  // each call must re-inject independently.
  const ctx = makeCtx({ connections: { google: {} }, models: [deepseekModel] })
  await setup(ctx)
  const event1 = { sessionID: "sX", model: { providerID: "deepseek", id: "deepseek-flash" }, system: [] }
  await ctx.hooks.context(event1)
  assert.equal(event1.system.length, 1)
  assert.equal(event1.system[0].type, "text")
  assert.match(event1.system[0].text, /@observer\b/)

  const event2 = { sessionID: "sX", model: { providerID: "deepseek", id: "deepseek-flash" }, system: [] }
  await ctx.hooks.context(event2)
  assert.equal(event2.system.length, 1, "instruction re-injected on the session's second model request too")
  assert.match(event2.system[0].text, /@observer\b/)

  const event3 = { sessionID: "sX", model: { providerID: "deepseek", id: "deepseek-flash" }, system: [] }
  await ctx.hooks.context(event3)
  assert.equal(event3.system.length, 1, "and on the third")
})

test("(d) context hook skips image-capable models", async () => {
  const ctx = makeCtx({ connections: {}, models: [anthropicImageModel] })
  await setup(ctx)
  const event = { sessionID: "sY", model: { providerID: "anthropic", id: "claude-sonnet-5" }, system: [] }
  await ctx.hooks.context(event)
  assert.equal(event.system.length, 0)
})

test("(d) context hook skips non-bridge providers", async () => {
  const ctx = makeCtx({ connections: {}, models: [anthropicTextModel] })
  await setup(ctx)
  const event = { sessionID: "sZ", model: { providerID: "anthropic", id: "claude-sonnet-5" }, system: [] }
  await ctx.hooks.context(event)
  assert.equal(event.system.length, 0, "anthropic is not in the default bridge list (deepseek only)")
})

test("(d) context hook injects no-vision-key variant when nothing is connected", async () => {
  const ctx = makeCtx({ connections: {}, models: [deepseekModel] })
  await setup(ctx)
  const event = { sessionID: "sW", model: { providerID: "deepseek", id: "deepseek-flash" }, system: [] }
  await ctx.hooks.context(event)
  assert.equal(event.system.length, 1)
  assert.match(event.system[0].text, /no vision model is connected/)
})

// --- (e) stale-file cleanup does not throw ---

test("(e) stale cleanup removes files older than 1h without throwing, keeps fresh files", async () => {
  const dir = mkdtempSync(join(tmpdir(), "observer-bridge-stale-"))
  scratchDirs.push(dir)
  process.env.OBSERVER_BRIDGE_TMPDIR = dir

  const staleFile = join(dir, "pasted_old.png")
  writeFileSync(staleFile, "x")
  const oldTime = new Date(Date.now() - 2 * 3600_000)
  utimesSync(staleFile, oldTime, oldTime)

  const freshFile = join(dir, "pasted_new.png")
  writeFileSync(freshFile, "y")

  const ctx = makeCtx({})
  await assert.doesNotReject(setup(ctx))
  assert.ok(!existsSync(staleFile), "stale (>1h) file removed")
  assert.ok(existsSync(freshFile), "fresh file kept")
})

test("(e) stale cleanup does not throw when the temp dir does not exist yet", async () => {
  const dir = join(tmpdir(), `observer-bridge-missing-${Date.now()}`)
  scratchDirs.push(dir)
  process.env.OBSERVER_BRIDGE_TMPDIR = dir
  const ctx = makeCtx({})
  await assert.doesNotReject(setup(ctx))
  assert.ok(existsSync(dir), "temp dir created")
})

// --- (3) cleanupStale must only delete its own pasted_* files (HIGH fix) ---

test("(3) cleanupStale leaves aged foreign files alone, removes aged pasted_* files", async () => {
  const dir = mkdtempSync(join(tmpdir(), "observer-bridge-foreign-"))
  scratchDirs.push(dir)
  process.env.OBSERVER_BRIDGE_TMPDIR = dir

  const foreignFile = join(dir, "screenshot_12345.png") // e.g. a macos-use/playwright capture
  writeFileSync(foreignFile, "x")
  const pastedFile = join(dir, "pasted_old.png")
  writeFileSync(pastedFile, "y")
  const oldTime = new Date(Date.now() - 2 * 3600_000)
  utimesSync(foreignFile, oldTime, oldTime)
  utimesSync(pastedFile, oldTime, oldTime)

  const ctx = makeCtx({})
  await setup(ctx)

  assert.ok(existsSync(foreignFile), "foreign (non pasted_*) aged file survives cleanup")
  assert.ok(!existsSync(pastedFile), "aged pasted_* file is removed")
})

// --- (4) restrictive permissions (MED fix) ---

test("(4) tempDir created with mode 0o700 and saved files written with mode 0o600", async () => {
  const dir = join(tmpdir(), `observer-bridge-perms-${Date.now()}-${Math.random().toString(36).slice(2)}`)
  scratchDirs.push(dir)
  process.env.OBSERVER_BRIDGE_TMPDIR = dir
  assert.ok(!existsSync(dir), "precondition: tempDir must not pre-exist so creation mode is exercised")

  const ctx = makeCtx({
    connections: { google: {} },
    models: [deepseekModel],
    sessions: { sP: { model: { providerID: "deepseek", id: "deepseek-flash" } } },
  })
  await setup(ctx)
  const dirMode = statSync(dir).mode & 0o777
  assert.equal(dirMode, 0o700, `expected tempDir mode 0o700, got 0o${dirMode.toString(8)}`)

  const event = { sessionID: "sP", prompt: { text: "", files: [{ uri: dataUri("image/png", [1, 2, 3]) }] } }
  await ctx.hooks.prompt(event)
  const savedPath = event.prompt.text.match(/\[Image saved to: (.*?)\]/)[1]
  const fileMode = statSync(savedPath).mode & 0o777
  assert.equal(fileMode, 0o600, `expected file mode 0o600, got 0o${fileMode.toString(8)}`)
})

test("(4) a pre-existing tempDir keeps its original mode (not chmod'd)", async () => {
  const dir = mkdtempSync(join(tmpdir(), "observer-bridge-preexist-"))
  scratchDirs.push(dir)
  chmodSync(dir, 0o755) // simulate a foreign/pre-existing dir with looser perms
  process.env.OBSERVER_BRIDGE_TMPDIR = dir

  const ctx = makeCtx({})
  await setup(ctx)
  const mode = statSync(dir).mode & 0o777
  assert.equal(mode, 0o755, "pre-existing directory mode must not be changed by setup")
})

// --- (f) cleanup function disposes hooks ---

test("(f) returned cleanup function disposes both hook registrations", async () => {
  const ctx = makeCtx({})
  const cleanup = await setup(ctx)
  assert.equal(ctx.disposed.context, false)
  assert.equal(ctx.disposed.prompt, false)
  await cleanup()
  assert.equal(ctx.disposed.context, true)
  assert.equal(ctx.disposed.prompt, true)
})

// --- (5) dispose resilience (Promise.allSettled) + case-insensitive
// provider matching in isImageCapable (LOW fix) ---

test("(5) cleanup disposes both hooks even if one dispose() throws", async () => {
  const promptDisposed = { value: false }
  const ctx = {
    session: {
      hook: async (name) => {
        if (name === "context") {
          return {
            dispose: async () => {
              throw new Error("boom")
            },
          }
        }
        return {
          dispose: async () => {
            promptDisposed.value = true
          },
        }
      },
      get: async () => {
        throw new Error("unused")
      },
    },
    integration: { connection: { active: async () => undefined } },
    model: { list: async () => [] },
  }
  const cleanup = await setup(ctx)
  await assert.doesNotReject(cleanup(), "cleanup must not throw even if one dispose() rejects")
  assert.equal(promptDisposed.value, true, "prompt hook still disposed even though context hook's dispose threw")
})

test("(5) isImageCapable/isBridgeProvider match provider id case-insensitively", async () => {
  const ctx = makeCtx({
    connections: {},
    models: [
      {
        providerID: "DeepSeek", // catalog reports different casing than the session/event
        id: "deepseek-flash",
        modelID: "deepseek-flash",
        capabilities: { input: ["text", "image"], output: ["text"], tools: true },
      },
    ],
  })
  await setup(ctx)
  const event = { sessionID: "sCase", model: { providerID: "deepseek", id: "deepseek-flash" }, system: [] }
  await ctx.hooks.context(event)
  // The model IS image-capable once matched case-insensitively, so no
  // vision instruction should be injected.
  assert.equal(event.system.length, 0, "image-capable model matched despite provider casing mismatch")
})

// --- bonus: env override sanity check ---

test("OBSERVER_BRIDGE_PROVIDERS env override changes the bridged provider set", async () => {
  process.env.OBSERVER_BRIDGE_PROVIDERS = "mycustom"
  const ctx = makeCtx({
    connections: { google: {} },
    models: [
      {
        providerID: "mycustom",
        id: "m1",
        modelID: "m1",
        capabilities: { input: ["text"], output: ["text"], tools: true },
      },
    ],
    sessions: { s6: { model: { providerID: "mycustom", id: "m1" } } },
  })
  await setup(ctx)
  const event = { sessionID: "s6", prompt: { text: "x", files: [{ uri: dataUri("image/png", [1]) }] } }
  await ctx.hooks.prompt(event)
  assert.equal(event.prompt.files.length, 0, "custom provider list honored")

  // deepseek (the default) is no longer in the bridge list once overridden.
  const ctx2 = makeCtx({
    connections: { google: {} },
    models: [deepseekModel],
    sessions: { s7: { model: { providerID: "deepseek", id: "deepseek-flash" } } },
  })
  await setup(ctx2)
  const event2 = { sessionID: "s7", prompt: { text: "x", files: [{ uri: dataUri("image/png", [1]) }] } }
  await ctx2.hooks.prompt(event2)
  assert.equal(event2.prompt.files.length, 1, "deepseek no longer bridged once provider list is overridden")
})
