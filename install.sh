#!/usr/bin/env bash
#
# install.sh - install the Supervisor OpenCode template into your OpenCode
# config directory. Safe, non-destructive, and idempotent.
#
#   ./install.sh                          # interactive install (default dir)
#   ./install.sh --yes --with-config      # non-interactive, copy template config
#   ./install.sh --doctor                 # dependency scan (exit code is always 0)
#   ./install.sh --dry-run                # show what would happen, write nothing
#   ./install.sh --config-dir DIR ...     # override target config directory
#
# Requirements: bash 3.2+ (macOS or Linux), Node.js (config merge + doctor).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPS_JSON="$REPO_ROOT/deps.json"
MERGE_SCRIPT="$REPO_ROOT/scripts/merge-config.mjs"
CONFIG_TEMPLATE="$REPO_ROOT/opencode.template.json"

EXPECTED_AGENTS=45
EXPECTED_SKILL_DIRS=22

DOCTOR=0
DRY_RUN=0
YES=0
WITH_CONFIG=0
CONFIG_DIR=""

NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
STAMP="$(date +%Y%m%d-%H%M%S)"

info()  { printf '%s\n' "  [install] $*"; }
warn()  { printf '%s\n' "  [install] WARN: $*" >&2; }
error() { printf '%s\n' "  [install] ERROR: $*" >&2; }

usage() {
  cat <<EOF
Usage: ./install.sh [options]

Install the Supervisor agent template (agents, skills, plugin, AGENTS.md,
config) into your OpenCode config directory (default: ~/.config/opencode).

Options:
  --doctor           Scan installed vs missing dependencies and print tailored
                     install commands. Never fails, writes nothing.
  --dry-run          Print what would be copied and merged without writing.
  --yes, -y          Non-interactive mode (skip the confirmation prompt).
  --with-config      Copy opencode.template.json when opencode.json is
                     missing. Existing configs are always safely merged.
  --config-dir DIR   Override the target config directory (useful for testing).
  --help, -h         Show this help.
EOF
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

while [ "$#" -gt 0 ]; do
  case "$1" in
    --doctor) DOCTOR=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --yes | -y) YES=1 ;;
    --with-config) WITH_CONFIG=1 ;;
    --config-dir)
      [ "$#" -ge 2 ] || { error "--config-dir requires a value"; exit 2; }
      CONFIG_DIR="$2"
      shift
      ;;
    --config-dir=*) CONFIG_DIR="${1#*=}" ;;
    --help | -h) usage; exit 0 ;;
    --*) error "unknown option: $1"; usage >&2; exit 2 ;;
    *) error "unexpected argument: $1"; usage >&2; exit 2 ;;
  esac
  shift
done

[ -n "$CONFIG_DIR" ] || CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"

# ---------------------------------------------------------------------------
# OS detection and pre-flight checks
# ---------------------------------------------------------------------------

OS_NAME="$(uname -s)"
case "$OS_NAME" in
  Darwin) ;;
  Linux) ;;
  *)
    error "unsupported OS: $OS_NAME (this installer supports macOS and Linux)"
    exit 1
    ;;
esac

if ! command -v node >/dev/null 2>&1; then
  error "Node.js is required (config merge + dependency doctor)"
  error "Install it first, e.g.: brew install node  |  sudo apt install -y nodejs"
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  warn "python3 not found - many quality tools need it; the installer can continue"
fi

# ---------------------------------------------------------------------------
# Dependency doctor
# ---------------------------------------------------------------------------

run_doctor() {
  info "Dependency doctor (scanning against deps.json)"
  DEPS_JSON="$DEPS_JSON" node --input-type=module - <<'NODE'
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

function has(cmd) {
  return spawnSync("sh", ["-c", `command -v '${cmd}' >/dev/null 2>&1`]).status === 0;
}

function main() {
  const manifest = JSON.parse(readFileSync(process.env.DEPS_JSON, "utf8"));
  const platform = process.platform; // darwin | linux | win32
  const platformKey =
    platform === "darwin" ? "darwin" : platform === "win32" ? "windows" : "linux";
  const priority = {
    darwin: ["brew", "pip3", "npm"],
    linux: ["apt-get", "pacman", "pip3", "npm"],
    win32: ["winget", "choco", "scoop", "pip", "npm"],
  }[platform] ?? ["pip3", "npm"];

  const available = new Set(priority.filter(has));
  const py = has("python3") ? "python3" : has("python") ? "python" : null;

  console.log(`Platform: ${platformKey}`);
  console.log(
    `Package managers detected: ${available.size > 0 ? [...available].join(", ") : "none"}`
  );
  console.log(`python3: ${py ?? "MISSING"}`);

  function toolInstalled(tool) {
    for (const cmd of tool.detect?.commands ?? []) {
      if (has(cmd)) return true;
    }
    for (const mod of tool.detect?.python_modules ?? []) {
      if (py && spawnSync(py, ["-c", `import ${mod}`]).status === 0) return true;
    }
    return false;
  }

  function pickCommand(tool) {
    const perPlat = tool.install?.[platformKey] ?? {};
    for (const mgr of priority) {
      if (perPlat[mgr]) {
        return { argv: perPlat[mgr], mgr, detected: available.has(mgr) };
      }
    }
    const entries = Object.entries(perPlat);
    if (entries.length > 0) {
      return { argv: entries[0][1], mgr: entries[0][0], detected: false };
    }
    return null;
  }

  let total = 0;
  let missing = 0;
  for (const [key, cat] of Object.entries(manifest.categories ?? {})) {
    console.log(`\n== ${cat.label ?? key} ==`);
    for (const [name, tool] of Object.entries(cat.tools ?? {})) {
      total += 1;
      if (toolInstalled(tool)) {
        console.log(`  [ok] ${name}`);
        continue;
      }
      missing += 1;
      const pick = pickCommand(tool);
      const how = pick
        ? `${pick.mgr}: ${pick.argv.join(" ")}${pick.detected ? "" : " (package manager not detected)"}`
        : "manual install - see DEPENDENCIES.md";
      console.log(`  [--] ${name}`);
      console.log(`       install: ${how}`);
      if (tool.notes) console.log(`       note: ${tool.notes}`);
    }
  }

  console.log(`\nSummary: ${total - missing}/${total} tools available.`);
  if (missing > 0) {
    console.log(`Run the listed commands for the ${missing} missing tool(s), then re-run --doctor.`);
  } else {
    console.log("All tools present.");
  }
  console.log("Next step: opencode auth login (see PROVIDERS.md)");
}

try {
  main();
} catch (err) {
  console.error(`doctor: ${err.message}`);
}
process.exit(0); // the doctor never fails
NODE
}

if [ "$DOCTOR" -eq 1 ]; then
  run_doctor
  exit 0
fi

# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------

if [ "$DRY_RUN" -eq 1 ]; then
  info "DRY RUN - nothing will be written"
  info "config dir: $CONFIG_DIR"
  info "files that would be copied:"
  printf '    %s\n' "agent/supervisor.md"
  for f in "$REPO_ROOT"/agents/*.md; do
    [ -e "$f" ] || continue
    printf '    agents/%s\n' "$(basename "$f")"
  done
  printf '    %s\n' "skills/ (recursive; $(find "$REPO_ROOT/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ') skill dirs)"
  printf '    %s\n' "plugin/observer-bridge.js" "AGENTS.md"
  echo
  if [ -e "$CONFIG_DIR/opencode.json" ]; then
    info "existing opencode.json found - merge would apply:"
    if node "$MERGE_SCRIPT" --dry-run "$CONFIG_DIR/opencode.json"; then
      :
    else
      warn "config merge would fail - is opencode.json valid JSON?"
    fi
  elif [ "$WITH_CONFIG" -eq 1 ]; then
    info "no opencode.json - would copy opencode.template.json"
  else
    warn "no opencode.json and --with-config not given - config would be left untouched"
  fi
  echo
  info "existing opencode.json/AGENTS.md would be backed up to $CONFIG_DIR/backups/"
  info "would write $CONFIG_DIR/.supervisor-state.json"
  exit 0
fi

# ---------------------------------------------------------------------------
# Confirmation
# ---------------------------------------------------------------------------

if [ "$YES" -eq 0 ]; then
  if [ -t 0 ]; then
    printf 'Install Supervisor template into %s? [y/N] ' "$CONFIG_DIR"
    read -r answer
    case "$answer" in
      y | Y | yes | YES) ;;
      *) info "aborted"; exit 0 ;;
    esac
  else
    error "stdin is not a terminal and --yes was not given; aborting"
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# Backup, copy, config merge
# ---------------------------------------------------------------------------

mkdir -p "$CONFIG_DIR/agent" "$CONFIG_DIR/agents" "$CONFIG_DIR/plugin" \
  "$CONFIG_DIR/skills" "$CONFIG_DIR/backups"

if [ -e "$CONFIG_DIR/opencode.json" ]; then
  cp "$CONFIG_DIR/opencode.json" "$CONFIG_DIR/backups/opencode.json.$STAMP.bak"
  info "backed up opencode.json -> backups/opencode.json.$STAMP.bak"
fi
if [ -e "$CONFIG_DIR/AGENTS.md" ]; then
  cp "$CONFIG_DIR/AGENTS.md" "$CONFIG_DIR/backups/AGENTS.md.$STAMP.bak"
  info "backed up AGENTS.md -> backups/AGENTS.md.$STAMP.bak"
fi

cp "$REPO_ROOT/agent/supervisor.md" "$CONFIG_DIR/agent/supervisor.md"
AGENT_COUNT=0
for f in "$REPO_ROOT"/agents/*.md; do
  [ -e "$f" ] || continue
  cp "$f" "$CONFIG_DIR/agents/"
  AGENT_COUNT=$((AGENT_COUNT + 1))
done
cp -R "$REPO_ROOT/skills/." "$CONFIG_DIR/skills/"
cp "$REPO_ROOT/plugin/observer-bridge.js" "$CONFIG_DIR/plugin/observer-bridge.js"
cp "$REPO_ROOT/AGENTS.md" "$CONFIG_DIR/AGENTS.md"
info "copied agent/supervisor.md, $AGENT_COUNT agents/*.md, skills/, plugin/observer-bridge.js, AGENTS.md"

if [ -e "$CONFIG_DIR/opencode.json" ]; then
  node "$MERGE_SCRIPT" "$CONFIG_DIR/opencode.json"
elif [ "$WITH_CONFIG" -eq 1 ]; then
  cp "$CONFIG_TEMPLATE" "$CONFIG_DIR/opencode.json"
  info "copied opencode.template.json -> $CONFIG_DIR/opencode.json"
else
  warn "no opencode.json in $CONFIG_DIR and --with-config not given; config left untouched"
fi

# ---------------------------------------------------------------------------
# .supervisor-state.json (baseline file hashes for future updates)
# ---------------------------------------------------------------------------

STATE_ENTRIES=()

add_state_entry() {
  local rel="$1" abs="$2" hash
  if command -v sha256sum >/dev/null 2>&1; then
    hash="$(sha256sum "$abs" | awk '{print $1}')"
  else
    hash="$(shasum -a 256 "$abs" | awk '{print $1}')"
  fi
  STATE_ENTRIES+=("    \"$rel\": {\"sha256\": \"$hash\"}")
}

write_state_file() {
  if ! command -v sha256sum >/dev/null 2>&1 && ! command -v shasum >/dev/null 2>&1; then
    warn "no sha256 tool found (sha256sum/shasum) - skipping .supervisor-state.json"
    return 0
  fi
  STATE_ENTRIES=()
  local f target tmp count
  target="$CONFIG_DIR/.supervisor-state.json"
  tmp="$CONFIG_DIR/.supervisor-state.json.tmp"

  add_state_entry "agent/supervisor.md" "$REPO_ROOT/agent/supervisor.md"
  for f in "$REPO_ROOT"/agents/*.md; do
    [ -e "$f" ] || continue
    add_state_entry "agents/$(basename "$f")" "$f"
  done
  while IFS= read -r f; do
    add_state_entry "${f#"$REPO_ROOT/"}" "$f"
  done < <(find "$REPO_ROOT/skills" -type f | sort)
  add_state_entry "plugin/observer-bridge.js" "$REPO_ROOT/plugin/observer-bridge.js"
  add_state_entry "AGENTS.md" "$REPO_ROOT/AGENTS.md"

  count=${#STATE_ENTRIES[@]}
  {
    printf '{\n'
    printf '  "schema_version": 1,\n'
    printf '  "installed_at": "%s",\n' "$NOW_UTC"
    printf '  "source": "%s",\n' "${REPO_ROOT//\"/\\\"}"
    printf '  "files": {\n'
    local i
    for i in "${!STATE_ENTRIES[@]}"; do
      printf '%s' "${STATE_ENTRIES[$i]}"
      if [ "$i" -lt "$((count - 1))" ]; then printf ','; fi
      printf '\n'
    done
    printf '  }\n'
    printf '}\n'
  } > "$tmp"
  mv "$tmp" "$target"
  info "wrote $target ($count files hashed)"
}

if ! command -v sha256sum >/dev/null 2>&1 && ! command -v shasum >/dev/null 2>&1; then
  warn "no sha256 tool found (sha256sum/shasum) - skipping .supervisor-state.json"
else
  write_state_file
fi

# ---------------------------------------------------------------------------
# Post-install verification
# ---------------------------------------------------------------------------

FAILS=0
AGENTS_ACTUAL="$(find "$CONFIG_DIR/agents" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
SKILLS_ACTUAL="$(find "$CONFIG_DIR/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"

if [ -f "$CONFIG_DIR/agent/supervisor.md" ]; then
  info "verify OK: agent/supervisor.md"
else
  error "verify FAIL: agent/supervisor.md missing"
  FAILS=$((FAILS + 1))
fi
if [ "$AGENTS_ACTUAL" -eq "$EXPECTED_AGENTS" ]; then
  info "verify OK: agents/ contains $AGENTS_ACTUAL files"
else
  error "verify FAIL: agents/ has $AGENTS_ACTUAL files, expected $EXPECTED_AGENTS"
  FAILS=$((FAILS + 1))
fi
if [ "$SKILLS_ACTUAL" -ge "$EXPECTED_SKILL_DIRS" ]; then
  info "verify OK: skills/ contains $SKILLS_ACTUAL dirs (>= $EXPECTED_SKILL_DIRS bundled)"
else
  error "verify FAIL: skills/ has $SKILLS_ACTUAL dirs, expected at least $EXPECTED_SKILL_DIRS"
  FAILS=$((FAILS + 1))
fi
if [ -f "$CONFIG_DIR/plugin/observer-bridge.js" ]; then
  info "verify OK: plugin/observer-bridge.js"
else
  error "verify FAIL: plugin/observer-bridge.js missing"
  FAILS=$((FAILS + 1))
fi
if [ -f "$CONFIG_DIR/AGENTS.md" ]; then
  info "verify OK: AGENTS.md"
else
  error "verify FAIL: AGENTS.md missing"
  FAILS=$((FAILS + 1))
fi
if [ -f "$CONFIG_DIR/opencode.json" ]; then
  if OPC_CONFIG="$CONFIG_DIR/opencode.json" node -e \
    'JSON.parse(require("node:fs").readFileSync(process.env.OPC_CONFIG, "utf8"))' \
    2>/dev/null; then
    info "verify OK: opencode.json is valid JSON"
  else
    error "verify FAIL: opencode.json is not valid JSON"
    FAILS=$((FAILS + 1))
  fi
else
  info "verify SKIP: no opencode.json (pass --with-config to add one)"
fi
if [ -f "$CONFIG_DIR/.supervisor-state.json" ]; then
  info "verify OK: .supervisor-state.json"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo
info "Install complete."
info "Summary:"
info "  config dir: $CONFIG_DIR"
if [ "$WITH_CONFIG" -eq 1 ] || [ -f "$CONFIG_DIR/opencode.json" ]; then
  info "  config: opencode.json"
else
  info "  config: untouched (pass --with-config next time)"
fi
info "  state: .supervisor-state.json"
if [ -d "$CONFIG_DIR/backups" ] && ls "$CONFIG_DIR/backups"/*.bak >/dev/null 2>&1; then
  info "  backups: $CONFIG_DIR/backups/"
fi

if [ "$FAILS" -gt 0 ]; then
  error "post-install verification found $FAILS problem(s)"
  exit 1
fi
info "Verification passed."
info "Next steps:"
info "  1. opencode auth login          # sign in to your providers (see PROVIDERS.md)"
info "  2. opencode                      # start working with the supervisor agent"
info "  3. ./install.sh --doctor         # re-check remaining dependencies"
exit 0
