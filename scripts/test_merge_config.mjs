// node:test suite for scripts/merge-config.mjs, run as a subprocess against
// temp fixture files. Run: node --test scripts/test_merge_config.mjs
//
// merge-config.mjs calls main() unconditionally at load time (reading
// process.argv and calling process.exit() on failure paths) — importing it
// directly as a module would hijack the test runner's own argv and could
// kill the whole test process. Driving it as a CLI subprocess avoids that
// entirely and also exercises the real --dry-run / exit-code behavior.
import assert from "node:assert/strict"
import { test } from "node:test"
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { fileURLToPath } from "node:url"
import { spawnSync } from "node:child_process"

const SCRIPT = fileURLToPath(new URL("./merge-config.mjs", import.meta.url))

let scratchDirs = []
test.beforeEach(() => {
  scratchDirs.push(mkdtempSync(join(tmpdir(), "merge-config-test-")))
})
test.afterEach(() => {
  for (const dir of scratchDirs) rmSync(dir, { recursive: true, force: true })
  scratchDirs = []
})

function fixture(data) {
  const dir = scratchDirs[scratchDirs.length - 1]
  const path = join(dir, "opencode.json")
  writeFileSync(path, JSON.stringify(data, null, 2) + "\n", "utf8")
  return path
}

function rawFixture(text) {
  const dir = scratchDirs[scratchDirs.length - 1]
  const path = join(dir, "opencode.json")
  writeFileSync(path, text, "utf8")
  return path
}

function corruptBackupCount(path) {
  const dir = scratchDirs[scratchDirs.length - 1]
  const base = path.split("/").pop()
  return readdirSync(dir).filter((name) => name.startsWith(base) && name.includes(".corrupt-")).length
}

function run(path, extraArgs = []) {
  const result = spawnSync(process.execPath, [SCRIPT, path, ...extraArgs], {
    encoding: "utf8",
  })
  return result
}

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"))
}

// --- stale entry removed, other entries preserved ---------------------------

test("removes the stale observer-bridge.js entry and keeps other plugin entries", () => {
  const path = fixture({ plugin: ["observer-bridge.js", "opencode-wakelock"] })
  const result = run(path)
  assert.equal(result.status, 0, result.stderr)
  const cfg = readJson(path)
  assert.deepEqual(cfg.plugin, ["opencode-wakelock"])
  assert.match(result.stdout, /removed stale "observer-bridge\.js"/)
})

test("deletes the plugin key entirely when removing the stale entry empties the array", () => {
  const path = fixture({ plugin: ["observer-bridge.js"] })
  const result = run(path)
  assert.equal(result.status, 0, result.stderr)
  const cfg = readJson(path)
  assert.ok(!("plugin" in cfg), "plugin key should be removed, not left as []")
  assert.match(result.stdout, /key removed/)
})

test("removes a bare-string observer-bridge.js plugin value", () => {
  const path = fixture({ plugin: "observer-bridge.js" })
  const result = run(path)
  assert.equal(result.status, 0, result.stderr)
  const cfg = readJson(path)
  assert.ok(!("plugin" in cfg))
})

test("leaves a plugin array untouched when it does not contain the stale entry", () => {
  const path = fixture({ plugin: ["opencode-wakelock", "opencode-pty"] })
  const result = run(path)
  assert.equal(result.status, 0, result.stderr)
  const cfg = readJson(path)
  assert.deepEqual(cfg.plugin, ["opencode-wakelock", "opencode-pty"])
})

test("does not create a plugin key when none exists", () => {
  const path = fixture({ default_agent: "supervisor" })
  const result = run(path)
  assert.equal(result.status, 0, result.stderr)
  const cfg = readJson(path)
  assert.ok(!("plugin" in cfg))
})

// --- idempotent ---------------------------------------------------------

test("is idempotent: a second run reports no further changes", () => {
  const path = fixture({ plugin: ["observer-bridge.js", "keep-me"] })
  const first = run(path)
  assert.equal(first.status, 0, first.stderr)
  const afterFirst = readJson(path)
  assert.deepEqual(afterFirst.plugin, ["keep-me"])

  const second = run(path)
  assert.equal(second.status, 0, second.stderr)
  assert.match(second.stdout, /no changes needed/)
  const afterSecond = readJson(path)
  assert.deepEqual(afterSecond, afterFirst, "second run must not alter the config")
})

// --- --dry-run writes nothing --------------------------------------------

test("--dry-run computes the stale-entry removal but writes nothing", () => {
  const path = fixture({ plugin: ["observer-bridge.js", "keep-me"] })
  const before = readFileSync(path, "utf8")
  const result = run(path, ["--dry-run"])
  assert.equal(result.status, 0, result.stderr)
  assert.match(result.stdout, /removed stale "observer-bridge\.js"/)
  assert.match(result.stdout, /dry-run - nothing was written/)
  const after = readFileSync(path, "utf8")
  assert.equal(after, before, "file bytes must be unchanged after --dry-run")
})

test("--dry-run on an already-clean config writes nothing and reports no changes", () => {
  const path = fixture({
    default_agent: "supervisor",
    experimental: { subagent_depth: 2, todo: true },
  })
  const before = readFileSync(path, "utf8")
  const result = run(path, ["--dry-run"])
  assert.equal(result.status, 0, result.stderr)
  const after = readFileSync(path, "utf8")
  assert.equal(after, before)
  assert.ok(existsSync(path), "fixture file still exists")
})

// --- JSONC: trailing commas merge normally, comments are never rewritten --

test("a trailing comma with no comments is parsed, merged, and written like plain JSON", () => {
  const text = '{\n  "default_agent": "supervisor",\n  "custom_key": "keep me",\n}\n'
  const path = rawFixture(text)
  const result = run(path)
  assert.equal(result.status, 0, result.stderr)
  assert.match(result.stdout, /experimental\.subagent_depth/)
  assert.match(result.stdout, /experimental\.todo/)
  const cfg = readJson(path)
  assert.equal(cfg.default_agent, "supervisor")
  assert.equal(cfg.custom_key, "keep me", "arbitrary keys survive the JSONC->JSON rewrite")
  assert.equal(cfg.experimental.subagent_depth, 2)
  assert.equal(cfg.experimental.todo, true)
  assert.notEqual(readFileSync(path, "utf8"), text, "file was rewritten as strict JSON (trailing comma gone)")
})

test("--dry-run on a trailing-comma-only file computes changes but writes nothing", () => {
  const text = '{\n  "default_agent": "supervisor",\n  "custom_key": "keep me",\n}\n'
  const path = rawFixture(text)
  const result = run(path, ["--dry-run"])
  assert.equal(result.status, 0, result.stderr)
  assert.match(result.stdout, /experimental\.subagent_depth/)
  assert.match(result.stdout, /dry-run - nothing was written/)
  assert.equal(readFileSync(path, "utf8"), text, "file bytes unchanged under --dry-run")
})

test("a // inside a string value in an already-valid JSON file needs no stripping and merges normally", () => {
  const path = fixture({ default_agent: "supervisor", note: "https://example.com//ok" })
  const result = run(path)
  assert.equal(result.status, 0, result.stderr)
  const cfg = readJson(path)
  assert.equal(cfg.note, "https://example.com//ok")
})

test("// and /* */ sequences inside a string value are not mistaken for comments, even with a real trailing comma elsewhere", () => {
  const note = "see https://example.com/x//y and /* not a comment */ inside a string"
  const text = `{\n  "default_agent": "supervisor",\n  "note": "${note}",\n}\n`
  const path = rawFixture(text)
  const result = run(path)
  assert.equal(result.status, 0, result.stderr)
  assert.doesNotMatch(
    result.stderr,
    /config contains comments/,
    "a // or /* */ inside a string must not be treated as a real comment"
  )
  const cfg = readJson(path)
  assert.equal(cfg.note, note, "the string value must survive byte-for-byte")
  assert.equal(cfg.default_agent, "supervisor")
})

test("a // comment is never rewritten: exact manual changes are reported, no backup, nothing changed", () => {
  const text = '{\n  // a comment\n  "default_agent": "supervisor"\n}\n'
  const path = rawFixture(text)
  const result = run(path)
  assert.equal(result.status, 1)
  assert.match(result.stderr, /config contains comments; not modified/)
  assert.match(result.stderr, /experimental\.subagent_depth/)
  assert.match(result.stderr, /experimental\.todo/)
  assert.equal(readFileSync(path, "utf8"), text, "original file bytes untouched")
  assert.equal(corruptBackupCount(path), 0, "no .corrupt-*.bak should be created - nothing is wrong with the file")
})

test("a /* block */ comment's message lists the exact manual changes needed for this file", () => {
  const text =
    '{\n  /* block comment */\n  "subagent_depth": 1,\n  "compaction": { "prune": true },\n' +
    '  "plugin": ["observer-bridge.js", "keep-me"],\n  "default_agent": "supervisor"\n}\n'
  const path = rawFixture(text)
  const result = run(path)
  assert.equal(result.status, 1)
  assert.match(result.stderr, /config contains comments; not modified/)
  assert.match(result.stderr, /experimental\.subagent_depth/)
  assert.match(result.stderr, /experimental\.todo/)
  assert.match(result.stderr, /removed stale top-level key/)
  assert.match(result.stderr, /compaction\.prune/)
  assert.match(result.stderr, /observer-bridge\.js/)
  assert.doesNotMatch(result.stderr, /default_agent:/, "default_agent already matched - must not be listed as a change")
  assert.equal(readFileSync(path, "utf8"), text, "original file bytes untouched")
  assert.equal(corruptBackupCount(path), 0)
})

test("--dry-run on a commented file also writes nothing and reports the same honest message", () => {
  const text = '{\n  "default_agent": "supervisor" // trailing comment\n}\n'
  const path = rawFixture(text)
  const result = run(path, ["--dry-run"])
  assert.equal(result.status, 1)
  assert.match(result.stderr, /config contains comments; not modified/)
  assert.equal(readFileSync(path, "utf8"), text)
  assert.equal(corruptBackupCount(path), 0)
})

test("a real comment takes precedence over a trailing comma in the same file: left untouched", () => {
  const text = '{\n  // real comment\n  "default_agent": "supervisor",\n}\n'
  const path = rawFixture(text)
  const result = run(path)
  assert.equal(result.status, 1)
  assert.match(result.stderr, /config contains comments; not modified/)
  assert.equal(readFileSync(path, "utf8"), text, "original file bytes untouched, trailing comma included")
  assert.equal(corruptBackupCount(path), 0)
})

test("genuinely non-JSON content (no comments/trailing commas) still backs up as corrupt (unchanged behavior)", () => {
  const text = "this is not json at all\n"
  const path = rawFixture(text)
  const result = run(path)
  assert.equal(result.status, 1)
  assert.match(result.stderr, /is not valid JSON/)
  assert.doesNotMatch(result.stderr, /JSONC/)
  assert.doesNotMatch(result.stderr, /contains comments/)
  assert.equal(readFileSync(path, "utf8"), text, "original preserved")
  assert.equal(corruptBackupCount(path), 1, "a .corrupt-*.bak should still be made for genuinely broken content")
})

test("--dry-run on genuinely non-JSON content still writes nothing and creates no backup", () => {
  const text = "this is not json at all\n"
  const path = rawFixture(text)
  const result = run(path, ["--dry-run"])
  assert.equal(result.status, 1)
  assert.match(result.stderr, /is not valid JSON/)
  assert.match(result.stderr, /dry-run - nothing was written/)
  assert.equal(readFileSync(path, "utf8"), text)
  assert.equal(corruptBackupCount(path), 0, "dry-run must never create a backup, even for genuinely corrupt content")
})
