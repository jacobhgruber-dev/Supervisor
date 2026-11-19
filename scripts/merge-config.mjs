#!/usr/bin/env node
/**
 * merge-config.mjs - safely merge Supervisor defaults into an existing
 * opencode.json. Zero npm dependencies; Node 18+.
 *
 * Only these keys are ever touched:
 *   - experimental.subagent_depth -> set to max(existing, 2) (V2: default 1
 *     means a subagent cannot spawn a subagent; 2 enables
 *     supervisor -> role agent -> mule)
 *   - experimental.todo   -> set to true only if not already set explicitly
 *     (enables the todowrite tool)
 *   - subagent_depth (top-level) -> removed if present (OpenCode V2 ignores
 *     it with a warning; superseded by experimental.subagent_depth)
 *   - compaction.prune    -> removed if present (dead in V2, ignored with a
 *     warning)
 *   - default_agent       -> set to "supervisor"
 *   - plugin              -> the stale V1 "observer-bridge.js" entry is
 *     removed if present (the key itself is removed if that empties the
 *     array). OpenCode V2 auto-discovers plugins/observer-bridge/ with no
 *     config entry needed; leaving the V1 string in "plugin" makes V2 try
 *     to npm-install a package literally named "observer-bridge.js".
 *     Every other entry in the array is left untouched.
 *   - mcp.a11y-color-contrast -> added (enabled) if absent, enabled if present
 *
 * experimental.* is labeled experimental by OpenCode and may change without
 * notice.
 *
 * Everything else (provider, model, custom MCPs, custom keys, ...) is
 * preserved byte-for-byte in value, including ordering of existing keys.
 *
 * The target may be plain JSON or JSONC (OpenCode V2 itself accepts
 * opencode.json(c) with line/block comments and/or trailing commas). A
 * zero-dependency, string-aware reader strips both before parsing — text
 * inside a JSON string (e.g. a "https://example.com//path" value) is never
 * mistaken for a comment. A file with ONLY trailing commas (no comments) is
 * merged and written exactly like plain JSON. A file that contains comments
 * is never rewritten (that would delete them); instead the script computes
 * the exact manual changes needed, prints them, and exits non-zero with no
 * backup (nothing was wrong with the file). If the file still doesn't parse
 * even after stripping, it is genuinely corrupt: it is backed up
 * (`.corrupt-<stamp>.bak`) and the script exits non-zero without writing
 * anything. This script intentionally has zero npm dependencies; the JSONC
 * support above is a small hand-rolled reader, not a replacement for strict
 * JSON.parse, so pathological input simply falls through to the corrupt-file
 * path instead of silently producing the wrong result.
 *
 * Usage:
 *   node scripts/merge-config.mjs [path/to/opencode.json] [--dry-run]
 * Default target: ~/.config/opencode/opencode.json (Windows: %APPDATA%)
 */
import {
  copyFileSync,
  existsSync,
  readFileSync,
  renameSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const A11Y_ENTRY = {
  type: "local",
  command: ["npx", "-y", "a11y-color-contrast-mcp"],
  enabled: true,
};

// V2: default experimental.subagent_depth is 1 (a subagent cannot spawn a
// subagent). 2 enables supervisor -> role agent -> mule (mules are leaf
// nodes and never spawn further).
const MIN_SUBAGENT_DEPTH = 2;

function usage() {
  console.log(`merge-config: safely merge Supervisor defaults into opencode.json

Usage:
  node scripts/merge-config.mjs [path/to/opencode.json] [--dry-run]
  node scripts/merge-config.mjs --help

Options:
  --dry-run   report changes without writing anything
  --help      show this help

Default target: ${defaultTargetPath()}`);
}

function defaultTargetPath() {
  const base =
    process.platform === "win32"
      ? (process.env.APPDATA ?? join(homedir(), ".config"))
      : join(homedir(), ".config");
  return join(base, "opencode", "opencode.json");
}

function fail(message) {
  console.error(`merge-config: ERROR: ${message}`);
  process.exit(1);
}

function parseArgs(argv) {
  let target = null;
  let dryRun = false;
  for (const arg of argv) {
    if (arg === "--dry-run") {
      dryRun = true;
    } else if (arg === "--help" || arg === "-h") {
      usage();
      process.exit(0);
    } else if (arg.startsWith("--")) {
      console.error(`merge-config: unknown option: ${arg}`);
      process.exit(2);
    } else if (target === null) {
      target = arg;
    } else {
      console.error(`merge-config: unexpected extra argument: ${arg}`);
      process.exit(2);
    }
  }
  return { target: target ?? defaultTargetPath(), dryRun };
}

function backupCorruptFile(target) {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const backup = `${target}.corrupt-${stamp}.bak`;
  copyFileSync(target, backup);
  return backup;
}

// --- zero-dependency, string-aware JSONC reader -----------------------------
//
// Two independent, string-aware passes (comments, then trailing commas) are
// enough: removing comments can't change what is or isn't inside a string,
// and the only thing skipped while looking ahead for a trailing comma is
// whitespace, which can never open a string. Both passes track whether the
// scan is currently inside a JSON string literal so comment-like or
// comma-like text inside a quoted value (e.g. "https://example.com//path")
// is never mistaken for real // or /* */ syntax.

function stripComments(text) {
  let out = "";
  let inString = false;
  let hadComment = false;
  const n = text.length;
  for (let i = 0; i < n; i++) {
    const ch = text[i];
    if (inString) {
      out += ch;
      if (ch === "\\" && i + 1 < n) {
        out += text[i + 1];
        i += 1;
        continue;
      }
      if (ch === '"') inString = false;
      continue;
    }
    if (ch === '"') {
      inString = true;
      out += ch;
      continue;
    }
    if (ch === "/" && text[i + 1] === "/") {
      hadComment = true;
      i += 1;
      while (i + 1 < n && text[i + 1] !== "\n") i += 1;
      continue; // leaves the newline itself (if any) to be copied normally
    }
    if (ch === "/" && text[i + 1] === "*") {
      hadComment = true;
      i += 1;
      while (i + 1 < n && !(text[i + 1] === "*" && text[i + 2] === "/")) i += 1;
      i += 2; // consume the closing "*/" (safe even if unterminated at EOF)
      continue;
    }
    out += ch;
  }
  return { text: out, hadComment };
}

function stripTrailingCommas(text) {
  let out = "";
  let inString = false;
  let hadTrailingComma = false;
  const n = text.length;
  for (let i = 0; i < n; i++) {
    const ch = text[i];
    if (inString) {
      out += ch;
      if (ch === "\\" && i + 1 < n) {
        out += text[i + 1];
        i += 1;
        continue;
      }
      if (ch === '"') inString = false;
      continue;
    }
    if (ch === '"') {
      inString = true;
      out += ch;
      continue;
    }
    if (ch === ",") {
      let j = i + 1;
      while (j < n && /\s/.test(text[j])) j += 1;
      if (j < n && (text[j] === "}" || text[j] === "]")) {
        hadTrailingComma = true;
        continue; // drop the comma; the whitespace/bracket are copied as usual
      }
    }
    out += ch;
  }
  return { text: out, hadTrailingComma };
}

// Attempts to read `raw` as JSONC using only the two string-aware passes
// above (never a real parser dependency). Returns { ok: false } if it still
// doesn't parse even after stripping - genuinely corrupt, not just JSONC.
function readJsonc(raw) {
  const comments = stripComments(raw);
  const commas = stripTrailingCommas(comments.text);
  try {
    return {
      ok: true,
      value: JSON.parse(commas.text),
      hadComment: comments.hadComment,
      hadTrailingComma: commas.hadTrailingComma,
    };
  } catch {
    return { ok: false };
  }
}

// A file with comments can be read, but rewriting it as plain JSON would
// silently delete every comment - so nothing is written. Instead, compute
// what the merge would have done (on a disposable clone, never the real
// object) and tell the user exactly what to change by hand.
function reportCommentsNotModified(target, parsedCfg) {
  const clone = JSON.parse(JSON.stringify(parsedCfg));
  const changes = merge(clone);
  console.error(`merge-config: ERROR: ${target}: config contains comments; not modified`);
  console.error(
    "merge-config: OpenCode V2 accepts JSONC (comments) in opencode.json(c), but rewriting " +
      "this file would delete them, so nothing was written - no backup was created either, " +
      "since nothing is wrong with the file."
  );
  if (changes.length === 0) {
    console.error("merge-config: no changes needed - this file already matches the Supervisor defaults.");
    return;
  }
  console.error("merge-config: apply these changes by hand:");
  for (const change of changes) {
    console.error(`merge-config:   - ${change}`);
  }
}

function loadConfig(target, dryRun) {
  let raw;
  try {
    raw = readFileSync(target, "utf8");
  } catch (err) {
    fail(`cannot read ${target}: ${err.message}`);
  }
  try {
    return JSON.parse(raw);
  } catch (err) {
    const jsonc = readJsonc(raw);
    if (jsonc.ok) {
      if (jsonc.hadComment) {
        // Neither a dry run nor a real run writes anything here - this is
        // not corruption, so no .corrupt-<stamp>.bak is created either.
        reportCommentsNotModified(target, jsonc.value);
        process.exit(1);
      }
      // Only trailing commas: nothing of the user's is lost by writing this
      // back out as strict JSON, so merge and (maybe) write normally.
      return jsonc.value;
    }
    if (dryRun) {
      // Dry runs must write nothing - not even a backup.
      console.error(`merge-config: ERROR: ${target} is not valid JSON (${err.message})`);
      console.error("merge-config: dry-run - nothing was written (no backup created)");
      process.exit(1);
    }
    const backup = backupCorruptFile(target);
    console.error(`merge-config: ERROR: ${target} is not valid JSON (${err.message})`);
    console.error(`merge-config: original preserved at ${backup} - nothing was written`);
    process.exit(1);
  }
}

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** Merge defaults into cfg; returns human-readable change descriptions. */
function merge(cfg) {
  const changes = [];

  // experimental.subagent_depth: set to max(existing, MIN_SUBAGENT_DEPTH).
  if (cfg.experimental === undefined || cfg.experimental === null) {
    cfg.experimental = {};
  }
  if (!isPlainObject(cfg.experimental)) {
    fail(`"experimental" must be an object, got ${typeof cfg.experimental}`);
  }
  {
    const current = cfg.experimental.subagent_depth;
    const hasValidCurrent = typeof current === "number" && Number.isFinite(current);
    const next = Math.max(hasValidCurrent ? current : MIN_SUBAGENT_DEPTH, MIN_SUBAGENT_DEPTH);
    if (!hasValidCurrent) {
      cfg.experimental.subagent_depth = next;
      changes.push(`experimental.subagent_depth: set to ${next} (was unset)`);
    } else if (current !== next) {
      cfg.experimental.subagent_depth = next;
      changes.push(`experimental.subagent_depth: ${current} -> ${next}`);
    }
  }

  // experimental.todo: only set if the user hasn't set it explicitly.
  if (cfg.experimental.todo === undefined) {
    cfg.experimental.todo = true;
    changes.push("experimental.todo: set to true (was unset)");
  }

  // subagent_depth (top-level): stale, ignored by OpenCode V2 with a
  // warning. Remove it now that experimental.subagent_depth is in place.
  if (Object.prototype.hasOwnProperty.call(cfg, "subagent_depth")) {
    const old = cfg.subagent_depth;
    delete cfg.subagent_depth;
    changes.push(`subagent_depth: removed stale top-level key (was ${JSON.stringify(old)}; ignored by V2 — see experimental.subagent_depth)`);
  }

  // compaction.prune: dead in V2 (ignored with a warning) - drop if present.
  if (isPlainObject(cfg.compaction) && Object.prototype.hasOwnProperty.call(cfg.compaction, "prune")) {
    delete cfg.compaction.prune;
    changes.push("compaction.prune: removed (ignored by V2)");
  }

  // default_agent: always ensure supervisor.
  if (cfg.default_agent !== "supervisor") {
    const old = cfg.default_agent === undefined ? "unset" : String(cfg.default_agent);
    cfg.default_agent = "supervisor";
    changes.push(`default_agent: ${old} -> "supervisor"`);
  }

  // plugin (V1 key): remove the stale "observer-bridge.js" entry if present.
  // OpenCode V2 auto-discovers plugins/observer-bridge/ with no config entry
  // needed; leaving the V1 string behind makes V2 try (and fail, with a 404
  // warning) to npm-install a package literally named "observer-bridge.js".
  // Every other entry is preserved untouched; configs with no "plugin" key,
  // or an unrecognized shape, are left alone (this script no longer manages
  // the key's presence — only the stale entry's absence).
  if (Array.isArray(cfg.plugin)) {
    const before = cfg.plugin.length;
    cfg.plugin = cfg.plugin.filter((entry) => entry !== "observer-bridge.js");
    if (cfg.plugin.length !== before) {
      if (cfg.plugin.length === 0) {
        delete cfg.plugin;
        changes.push('plugin: removed stale "observer-bridge.js" entry (array now empty; key removed)');
      } else {
        changes.push(`plugin: removed stale "observer-bridge.js" entry (${cfg.plugin.length} entry/entries remaining)`);
      }
    }
  } else if (cfg.plugin === "observer-bridge.js") {
    delete cfg.plugin;
    changes.push('plugin: removed stale "observer-bridge.js" (was a bare string; key removed)');
  }

  // mcp: enable a11y-color-contrast if present, add it enabled if absent.
  if (cfg.mcp === undefined || cfg.mcp === null) {
    cfg.mcp = {};
  }
  if (!isPlainObject(cfg.mcp)) {
    fail(`"mcp" must be an object, got ${typeof cfg.mcp}`);
  }
  const a11y = cfg.mcp["a11y-color-contrast"];
  if (a11y === undefined) {
    cfg.mcp["a11y-color-contrast"] = {
      ...A11Y_ENTRY,
      command: [...A11Y_ENTRY.command],
    };
    changes.push('mcp: added "a11y-color-contrast" (enabled)');
  } else if (isPlainObject(a11y)) {
    if (a11y.enabled !== true) {
      a11y.enabled = true;
      changes.push('mcp: enabled "a11y-color-contrast"');
    }
  } else {
    console.warn(
      'merge-config: warning: "a11y-color-contrast" is not an object; left untouched'
    );
  }

  return changes;
}

function writeConfig(target, cfg) {
  const output = JSON.stringify(cfg, null, 2) + "\n";
  const tmp = `${target}.merge-${process.pid}.tmp`;
  writeFileSync(tmp, output, "utf8");
  try {
    renameSync(tmp, target);
  } catch {
    // Fallback for filesystems where rename-over-existing fails (e.g. Windows).
    writeFileSync(target, output, "utf8");
    try {
      unlinkSync(tmp);
    } catch {
      /* best effort */
    }
  }
}

function main() {
  const { target, dryRun } = parseArgs(process.argv.slice(2));
  if (!existsSync(target)) {
    fail(
      `${target} does not exist - copy opencode.template.json first ` +
        "(or run install.sh --with-config)"
    );
  }

  const cfg = loadConfig(target, dryRun);
  const changes = merge(cfg);

  console.log(`merge-config: target: ${target}`);
  if (changes.length === 0) {
    console.log("merge-config: no changes needed");
    return;
  }
  for (const change of changes) {
    console.log(`merge-config: ${change}`);
  }
  if (dryRun) {
    console.log("merge-config: dry-run - nothing was written");
    return;
  }
  writeConfig(target, cfg);
  console.log(`merge-config: wrote ${target}`);
}

main();
