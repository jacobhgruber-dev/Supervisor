#!/usr/bin/env node
/**
 * merge-config.mjs - safely merge Supervisor defaults into an existing
 * opencode.json. Zero npm dependencies; Node 18+.
 *
 * Only four keys are ever touched:
 *   - subagent_depth      -> set to 3 if missing or < 3 (left alone if >= 3)
 *   - default_agent       -> set to "supervisor"
 *   - plugin              -> ensure "observer-bridge.js" is included
 *   - mcp.a11y-color-contrast -> added (enabled) if absent, enabled if present
 *
 * Everything else (provider, model, custom MCPs, custom keys, ...) is
 * preserved byte-for-byte in value, including ordering of existing keys.
 * If the target is not valid JSON, it is backed up (`.corrupt-<stamp>.bak`)
 * and the script exits non-zero without writing anything.
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

  // subagent_depth: set only when missing or too shallow.
  if (typeof cfg.subagent_depth !== "number" || !Number.isFinite(cfg.subagent_depth)) {
    cfg.subagent_depth = 3;
    changes.push("subagent_depth: set to 3 (was unset)");
  } else if (cfg.subagent_depth < 3) {
    const old = cfg.subagent_depth;
    cfg.subagent_depth = 3;
    changes.push(`subagent_depth: ${old} -> 3`);
  }

  // default_agent: always ensure supervisor.
  if (cfg.default_agent !== "supervisor") {
    const old = cfg.default_agent === undefined ? "unset" : String(cfg.default_agent);
    cfg.default_agent = "supervisor";
    changes.push(`default_agent: ${old} -> "supervisor"`);
  }

  // plugin: ensure observer-bridge.js is present without removing others.
  if (cfg.plugin === undefined || cfg.plugin === null) {
    cfg.plugin = [];
  }
  if (typeof cfg.plugin === "string") {
    cfg.plugin = [cfg.plugin]; // tolerate single-plugin string configs
  }
  if (!Array.isArray(cfg.plugin)) {
    fail(`"plugin" must be an array (or string), got ${typeof cfg.plugin}`);
  }
  if (!cfg.plugin.includes("observer-bridge.js")) {
    cfg.plugin.push("observer-bridge.js");
    changes.push(`plugin: added "observer-bridge.js" (${cfg.plugin.length} total)`);
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
