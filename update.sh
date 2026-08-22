#!/usr/bin/env bash
#
# update.sh - update an installed Supervisor template in place.
#
# macOS/Linux counterpart of update.ps1. Classifies every managed file with
# a 3-way hash comparison (installed vs baseline vs repo) and only writes
# what changed:
#
#   install          - destination missing             -> copied
#   managed          - hash matches the baseline       -> updated silently
#   modified         - hash differs from the baseline  -> NEVER overwritten
#                       without --interactive; skipped otherwise
#   unmanaged        - exists but not in the baseline  -> treated as user-owned
#   removed-upstream - baseline file no longer in repo -> left in place
#
# Everything replaced is snapshotted first into
# <config-dir>/backups/supervisor-<timestamp>/ with a manifest.json, and can
# be restored with --rollback <timestamp>.
#
# opencode.json is handled separately: missing -> created from
# opencode.template.json; managed -> merged via scripts/merge-config.mjs
# (only subagent_depth, default_agent, plugin and the a11y-color-contrast MCP
# are ever touched); modified -> skipped unless --interactive.
#
# Usage:
#   ./update.sh                          # update everything (safe defaults)
#   ./update.sh --only-agents            # only agent files
#   ./update.sh --interactive --diff     # prompt + show diffs first
#   ./update.sh --dry-run                # print the plan, write nothing
#   ./update.sh --tier mule              # full update, agents limited to mule tier
#   ./update.sh --rollback 20260821-154530
#
# Requirements: bash 3.2+ (macOS/Linux), Node.js (state file + config merge).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_FILE=".supervisor-state.json"
MERGE_SCRIPT="$REPO_ROOT/scripts/merge-config.mjs"
CONFIG_TEMPLATE="$REPO_ROOT/opencode.template.json"

INTERACTIVE=0
DIFF=0
DRY_RUN=0
ONLY_AGENTS=0
ONLY_SKILLS=0
ONLY_PLUGIN=0
ROLLBACK=""
TIER=""
CONFIG_DIR=""

NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

info()  { printf '%s\n' "  [update] $*"; }
warn()  { printf '%s\n' "  [update] WARN: $*" >&2; }
error() { printf '%s\n' "  [update] ERROR: $*" >&2; }

usage() {
  cat <<EOF
Usage: ./update.sh [options]

Update an installed Supervisor template in place. Classifies every managed
file (agents, skills, plugin) with a 3-way hash comparison; user-modified
files are never overwritten without --interactive. Every replaced file is
snapshotted into <config-dir>/backups/supervisor-<timestamp>/ first.

Options:
  --interactive, -i   Prompt before overwriting user-modified files (one y/N
                      for all) and before merging a modified opencode.json.
  --diff, -d          Show a per-file unified diff for every file that would
                      change (git --no-index when git is available).
  --dry-run           Compute and print the plan (what would update, skip, or
                      conflict) but write nothing: no backups, no file copies,
                      no state rewrite. Can still show diffs with --diff.
  --tier TIER         Restrict agent file candidates to one tier:
                        junior  = agents/junior-*.md
                        mid     = bare role files (worker.md, architect.md,
                                  reviewer.md, debugger.md, security.md,
                                  researcher.md, editor.md, planner.md,
                                  quote-auditor.md)
                        mule    = agents/*-mule.md
                        senior  = agents/senior-*.md
                      agent/supervisor.md is only included when no --tier is
                      given. Agents must be in scope (use --tier alone or
                      with --only-agents).
  --only-agents       Only update agent/, agents/, and AGENTS.md.
  --only-skills       Only update skills/.
  --only-plugin       Only update plugin/observer-bridge.js.
  --rollback TS       Restore files from <config-dir>/backups/supervisor-TS
                      (TS format: YYYYMMDD-HHMMSS). Combines with nothing else.
  --config-dir DIR    Override the target config directory.
  --help, -h          Show this help.
EOF
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

while [ "$#" -gt 0 ]; do
  case "$1" in
    --interactive | -i) INTERACTIVE=1 ;;
    --diff | -d) DIFF=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --tier)
      [ "$#" -ge 2 ] || { error "--tier requires a value"; exit 2; }
      TIER="$2"
      shift
      ;;
    --tier=*) TIER="${1#*=}" ;;
    --only-agents) ONLY_AGENTS=1 ;;
    --only-skills) ONLY_SKILLS=1 ;;
    --only-plugin) ONLY_PLUGIN=1 ;;
    --rollback)
      [ "$#" -ge 2 ] || { error "--rollback requires a timestamp"; exit 2; }
      ROLLBACK="$2"
      shift
      ;;
    --rollback=*) ROLLBACK="${1#*=}" ;;
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

if [ -n "$ROLLBACK" ] && { [ "$INTERACTIVE" = 1 ] || [ "$DIFF" = 1 ] \
  || [ "$DRY_RUN" = 1 ] || [ -n "$TIER" ] \
  || [ "$ONLY_AGENTS" = 1 ] || [ "$ONLY_SKILLS" = 1 ] || [ "$ONLY_PLUGIN" = 1 ]; }; then
  error "--rollback combines with nothing else"
  exit 2
fi
if [ -n "$TIER" ]; then
  case "$TIER" in
    junior | mid | senior | mule) ;;
    *) error "invalid --tier '$TIER' (expected junior, mid, senior, or mule)"; exit 2 ;;
  esac
  if [ "$ONLY_SKILLS" = 1 ] || [ "$ONLY_PLUGIN" = 1 ]; then
    error "--tier only applies when agents are in scope (use it alone or with --only-agents)"
    exit 2
  fi
  # --tier implies agents-only scope (do not also pull skills/plugin into the plan)
  ONLY_AGENTS=1
fi
if [ -n "$ROLLBACK" ]; then
  printf '%s' "$ROLLBACK" | grep -Eq '^[0-9]{8}-[0-9]{6}$' \
    || { error "invalid --rollback timestamp '$ROLLBACK' (expected YYYYMMDD-HHMMSS)"; exit 2; }
fi

[ -n "$CONFIG_DIR" ] || CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"

if ! command -v node >/dev/null 2>&1; then
  error "Node.js is required (state file + config merge)"
  error "Install it first, e.g.: brew install node  |  sudo apt install -y nodejs"
  exit 1
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

sha256() {
  # sha256 PATH -> lowercase hex digest; empty when the file is absent
  if [ ! -f "$1" ]; then
    return 0
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

json_escape() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }

# PLAN_DIR holds the working state for one run:
#   state.tsv     rel<TAB>sha256  (baseline; loaded then mutated)
#   files.tsv     rel<TAB>src_abs (managed repo files in scope)
#   status.tsv    rel<TAB>status<TAB>src_hash<TAB>dest_hash
#   to_install.tsv  one rel per line (new + changed managed files)
PLAN_DIR="$(mktemp -d "${TMPDIR:-/tmp}/supervisor-update.XXXXXX")"
trap 'rm -rf "$PLAN_DIR"' EXIT

state_get() {
  # state_get REL -> baseline sha256 (empty if unknown)
  awk -F '\t' -v k="$1" '$1 == k { print $2 }' "$PLAN_DIR/state.tsv" 2>/dev/null || true
}

state_set() {
  # state_set REL SHA — update or insert a baseline entry
  if state_get "$1" | grep -q .; then
    awk -F '\t' -v OFS='\t' -v k="$1" -v v="$2" '$1 == k { $2 = v } 1' \
      "$PLAN_DIR/state.tsv" > "$PLAN_DIR/state.tsv.new"
    mv "$PLAN_DIR/state.tsv.new" "$PLAN_DIR/state.tsv"
  else
    printf '%s\t%s\n' "$1" "$2" >> "$PLAN_DIR/state.tsv"
  fi
}

load_state() {
  : > "$PLAN_DIR/state.tsv"
  local state_path="$CONFIG_DIR/$STATE_FILE"
  if [ ! -f "$state_path" ]; then
    return 0
  fi
  if ! node -e '
const fs = require("node:fs");
const j = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
for (const [k, v] of Object.entries(j.files ?? {})) {
  if (typeof v === "object" && v !== null && typeof v.sha256 === "string") {
    console.log(k + "\t" + v.sha256);
  }
}' "$state_path" > "$PLAN_DIR/state.tsv" 2>/dev/null; then
    warn "could not parse $state_path (treating as no baseline)"
    : > "$PLAN_DIR/state.tsv"
  fi
}

write_state() {
  local out="$PLAN_DIR/state.json" tmp
  LC_ALL=C sort -u -t "$(printf '\t')" -k1,1 "$PLAN_DIR/state.tsv" > "$PLAN_DIR/state.sorted"
  {
    printf '{\n'
    printf '  "schema_version": 1,\n'
    printf '  "installed_at": "%s",\n' "$NOW_UTC"
    printf '  "source": "%s",\n' "$(json_escape "$REPO_ROOT")"
    printf '  "files": {\n'
    local n=0 rel hash
    while IFS="$(printf '\t')" read -r rel hash; do
      [ -n "$rel" ] || continue
      if [ "$n" -gt 0 ]; then printf ',\n'; fi
      printf '    "%s": {"sha256": "%s"}' "$(json_escape "$rel")" "$(json_escape "$hash")"
      n=$((n + 1))
    done < "$PLAN_DIR/state.sorted"
    if [ "$n" -gt 0 ]; then printf '\n'; fi
    printf '  }\n}\n'
  } > "$out"
  if ! node -e 'JSON.parse(require("node:fs").readFileSync(process.argv[1], "utf8"))' "$out"; then
    error "internal error: generated invalid state JSON"
    exit 1
  fi
  mkdir -p "$CONFIG_DIR"
  tmp="$CONFIG_DIR/.supervisor-state.json.tmp"
  cp "$out" "$tmp"
  mv "$tmp" "$CONFIG_DIR/$STATE_FILE"
}

# ---------------------------------------------------------------------------
# Managed file enumeration (mirrors supervisor-install-common.ps1 Get-RepoFiles)
# ---------------------------------------------------------------------------

# tier_of REL -> junior | mid | senior | mule | "" (not a tier role file)
tier_of() {
  local base="${1##*/}"
  case "$base" in
    junior-*.md) printf 'junior' ;;
    senior-*.md) printf 'senior' ;;
    *-mule.md) printf 'mule' ;;
    worker.md | architect.md | reviewer.md | debugger.md | security.md \
      | researcher.md | editor.md | planner.md | quote-auditor.md)
      printf 'mid' ;;
    *) printf '' ;;
  esac
}

collect_files() {
  : > "$PLAN_DIR/files.tsv"
  if [ "$ONLY_AGENTS" = 1 ] || { [ "$ONLY_SKILLS" = 0 ] && [ "$ONLY_PLUGIN" = 0 ]; }; then
    local f rel
    for f in "$REPO_ROOT"/agent/*.md "$REPO_ROOT"/agents/*.md; do
      [ -f "$f" ] || continue
      rel="${f#"$REPO_ROOT"/}"
      # With --tier, only tier-matching role files are candidates;
      # agent/supervisor.md (and any other non-role file) is excluded.
      [ -z "$TIER" ] || [ "$(tier_of "$rel")" = "$TIER" ] || continue
      printf '%s\t%s\n' "$rel" "$f" >> "$PLAN_DIR/files.tsv"
    done
    [ -f "$REPO_ROOT/AGENTS.md" ] \
      && printf 'AGENTS.md\t%s\n' "$REPO_ROOT/AGENTS.md" >> "$PLAN_DIR/files.tsv"
  fi
  if [ "$ONLY_SKILLS" = 1 ] || { [ "$ONLY_AGENTS" = 0 ] && [ "$ONLY_PLUGIN" = 0 ]; }; then
    while IFS= read -r f; do
      [ "$(basename "$f")" = ".DS_Store" ] && continue
      printf '%s\t%s\n' "${f#"$REPO_ROOT"/}" "$f" >> "$PLAN_DIR/files.tsv"
    done < <(find "$REPO_ROOT/skills" -type f | LC_ALL=C sort)
  fi
  if [ "$ONLY_PLUGIN" = 1 ] || { [ "$ONLY_AGENTS" = 0 ] && [ "$ONLY_SKILLS" = 0 ]; }; then
    [ -f "$REPO_ROOT/plugin/observer-bridge.js" ] \
      && printf 'plugin/observer-bridge.js\t%s\n' "$REPO_ROOT/plugin/observer-bridge.js" >> "$PLAN_DIR/files.tsv"
  fi
}

# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

# Classification buckets (relative paths):
TO_INSTALL=()   # new files + changed managed files
TO_PROMPT=()    # modified / unmanaged files needing a decision
UP_TO_DATE=()   # managed and identical
LEFT_BEHIND=()  # in baseline but no longer shipped by the repo

classify() {
  local rel src_abs dest_abs
  while IFS="$(printf '\t')" read -r rel src_abs; do
    [ -n "$rel" ] || continue
    dest_abs="$CONFIG_DIR/$rel"
    local src_hash dest_hash base_hash status=""
    src_hash="$(sha256 "$src_abs")"
    [ -n "$src_hash" ] || { error "cannot hash $src_abs"; exit 1; }
    if [ ! -f "$dest_abs" ]; then
      TO_INSTALL+=("$rel")
      printf '%s\n' "$rel" >> "$PLAN_DIR/to_install.tsv"
      status="install"
    else
      dest_hash="$(sha256 "$dest_abs")"
      base_hash="$(state_get "$rel")"
      if [ -n "$base_hash" ]; then
        if [ "$base_hash" = "$dest_hash" ]; then
          if [ "$src_hash" = "$dest_hash" ]; then
            UP_TO_DATE+=("$rel")
          else
            TO_INSTALL+=("$rel")
            printf '%s\n' "$rel" >> "$PLAN_DIR/to_install.tsv"
          fi
        else
          TO_PROMPT+=("$rel")
          status="modified"
        fi
      else
        TO_PROMPT+=("$rel")
        status="unmanaged"
      fi
    fi
    printf '%s\t%s\t%s\t%s\n' "$rel" "$status" "$src_hash" "${dest_hash:-}" \
      >> "$PLAN_DIR/status.tsv"
  done < "$PLAN_DIR/files.tsv"
}

classify_removed() {
  # Baseline entries no longer shipped by the repo (dest still present).
  # A file that still exists in the repo is never LEFT_BEHIND, even when it
  # is out of scope for this run (e.g. filtered by --tier or --only-*).
  local rel
  while IFS="$(printf '\t')" read -r rel _; do
    [ -n "$rel" ] || continue
    [ -f "$REPO_ROOT/$rel" ] && continue
    [ -e "$CONFIG_DIR/$rel" ] || continue
    LEFT_BEHIND+=("$rel")
  done < "$PLAN_DIR/state.sorted" 2>/dev/null || true
}

print_plan() {
  printf '\n'
  info "Supervisor update"
  info "repo:   $REPO_ROOT"
  info "config: $CONFIG_DIR"
  local scope="everything (agents, skills, plugin, config)"
  if [ "$ONLY_AGENTS" = 1 ]; then scope="agents"; fi
  if [ "$ONLY_SKILLS" = 1 ]; then scope="skills"; fi
  if [ "$ONLY_PLUGIN" = 1 ]; then scope="plugin"; fi
  if [ -n "$TIER" ]; then
    if [ "$ONLY_AGENTS" = 1 ]; then
      scope="agents ($TIER tier)"
    else
      scope="$scope (agents limited to $TIER tier)"
    fi
  fi
  info "scope:  $scope"
  printf '\n'

  local rel status src_hash _
  while IFS="$(printf '\t')" read -r rel status src_hash _; do
    case "$status" in
      install)
        printf '  %-16s %s\n' "[INSTALL]" "$rel (new file)"
        ;;
      modified)
        printf '  %-16s %s\n' "[USER-MODIFIED]" "$rel (skipped unless --interactive)"
        ;;
      unmanaged)
        printf '  %-16s %s\n' "[USER FILE]" "$rel (not managed; skipped unless --interactive)"
        ;;
      *)
        if grep -qxF "$rel" "$PLAN_DIR/to_install.tsv" 2>/dev/null; then
          printf '  %-16s %s\n' "[UPDATE]" "$rel (managed; will replace)"
        else
          printf '  %-16s %s\n' "[OK]" "$rel (up to date)"
        fi
        ;;
    esac
  done < "$PLAN_DIR/status.tsv"
  for rel in ${LEFT_BEHIND[@]+"${LEFT_BEHIND[@]}"}; do
    printf '  %-16s %s\n' "[LEFT]" "$rel (no longer shipped upstream; keeping your file)"
  done
  printf '\n'
}

# ---------------------------------------------------------------------------
# Diffs
# ---------------------------------------------------------------------------

show_diffs() {
  local rel src_abs dest_abs
  local have_git=0
  command -v git >/dev/null 2>&1 && have_git=1
  for rel in ${TO_INSTALL[@]+"${TO_INSTALL[@]}"} ${TO_PROMPT[@]+"${TO_PROMPT[@]}"}; do
    src_abs="$REPO_ROOT/$rel"
    dest_abs="$CONFIG_DIR/$rel"
    printf '\n--- diff: %s ---\n' "$rel"
    if [ ! -f "$dest_abs" ]; then
      printf '(new file: %s)\n' "$src_abs"
      continue
    fi
    if [ "$have_git" = 1 ]; then
      git --no-pager diff --no-index -- "$dest_abs" "$src_abs" || true
    else
      diff -u "$dest_abs" "$src_abs" || true
    fi
  done
}

# ---------------------------------------------------------------------------
# Backup snapshots
# ---------------------------------------------------------------------------

unique_ts() {
  local ts suffix=""
  ts="$(date +%Y%m%d-%H%M%S)"
  while [ -e "$CONFIG_DIR/backups/supervisor-$ts$suffix" ]; do
    suffix="-$(( ${suffix#-} + 1 ))"
  done
  printf '%s%s' "$ts" "$suffix"
}

snapshot() {
  # snapshot BACKUP_ROOT REL... — copies existing dest files + writes manifest.json
  local root="$1"
  shift
  local rel dest_abs
  mkdir -p "$root"
  {
    printf '{\n  "version": 1,\n  "createdAt": "%s",\n  "files": {\n' "$NOW_UTC"
    local n=0
    for rel in "$@"; do
      dest_abs="$CONFIG_DIR/$rel"
      [ -f "$dest_abs" ] || continue
      mkdir -p "$root/$(dirname "$rel")"
      cp "$dest_abs" "$root/$rel"
      if [ "$n" -gt 0 ]; then printf ',\n'; fi
      printf '    "%s": {"hash": "%s", "bytes": %s}' \
        "$(json_escape "$rel")" "$(sha256 "$dest_abs")" "$(wc -c < "$dest_abs" | tr -d ' ')"
      n=$((n + 1))
    done
    if [ "$n" -gt 0 ]; then printf '\n'; fi
    printf '  }\n}\n'
  } > "$root/manifest.json"
  node -e 'JSON.parse(require("node:fs").readFileSync(process.argv[1], "utf8"))' \
    "$root/manifest.json" || { error "internal error: invalid manifest JSON"; exit 1; }
}

# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

do_rollback() {
  local root="$CONFIG_DIR/backups/supervisor-$ROLLBACK"
  local manifest="$root/manifest.json"
  if [ ! -f "$manifest" ]; then
    error "no backup manifest found at $manifest"
    if [ -d "$CONFIG_DIR/backups" ] && [ -n "$(ls -A "$CONFIG_DIR/backups" 2>/dev/null)" ]; then
      info "available snapshots:"
      for d in "$CONFIG_DIR"/backups/supervisor-*; do
        [ -d "$d" ] && printf '    %s\n' "$(basename "$d")"
      done
    else
      info "no snapshots exist yet"
    fi
    exit 1
  fi

  local rels
  rels="$(node -e '
const j = JSON.parse(require("node:fs").readFileSync(process.argv[1], "utf8"));
console.log(Object.keys(j.files ?? {}).join("\n"));' "$manifest")" || exit 1

  printf '\n'
  info "rollback will restore $(printf '%s\n' "$rels" | sed '/^$/d' | wc -l | tr -d ' ') file(s) from: $root"
  printf '%s\n' "$rels" | sed '/^$/d' | while IFS= read -r rel; do
    printf '    restore  %s\n' "$rel"
  done
  if [ ! -t 0 ]; then
    info "rollback cancelled (no terminal input available)"
    exit 0
  fi
  printf 'Proceed? Current versions will be overwritten. [y/N] '
  local ans=""
  read -r ans || ans="n"
  case "$ans" in y | Y | yes | YES) ;; *) info "rollback cancelled"; exit 0 ;; esac

  printf '%s\n' "$rels" | sed '/^$/d' | while IFS= read -r rel; do
    local src_file="$root/$rel" dest_file="$CONFIG_DIR/$rel"
    if [ ! -f "$src_file" ]; then
      warn "backup file missing, skipping: $rel"
      continue
    fi
    mkdir -p "$(dirname "$dest_file")"
    cp "$src_file" "$dest_file"
    printf '  restored: %s\n' "$rel"
  done

  # Refresh baselines for the restored files (hash the destination).
  printf '%s\n' "$rels" | sed '/^$/d' | while IFS= read -r rel; do
    [ -f "$CONFIG_DIR/$rel" ] && state_set "$rel" "$(sha256 "$CONFIG_DIR/$rel")"
  done
  write_state
  printf '\n'
  info "rollback complete: restored $(printf '%s\n' "$rels" | sed '/^$/d' | wc -l | tr -d ' ') file(s) from $root"
  info "state baseline refreshed: $CONFIG_DIR/$STATE_FILE"
  exit 0
}

# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

apply() {
  local rel

  # User-modified decision (files first, mirroring update.ps1).
  if [ "${#TO_PROMPT[@]}" -gt 0 ]; then
    printf '\n'
    if [ "$INTERACTIVE" = 1 ]; then
      printf '%s user-modified file(s) differ from the repo. Overwrite with the repo versions? They will be backed up first. [y/N] ' \
        "${#TO_PROMPT[@]}"
      local ans=""
      read -r ans || ans="n"
      case "$ans" in
        y | Y | yes | YES)
          for rel in ${TO_PROMPT[@]+"${TO_PROMPT[@]}"}; do
            TO_INSTALL+=("$rel")
          done
          ;;
        *) info "keeping your versions (${#TO_PROMPT[@]} file(s) skipped)" ;;
      esac
    else
      info "${#TO_PROMPT[@]} user-modified file(s) skipped (never overwritten without a prompt). Re-run with --interactive to decide, or keep your versions."
    fi
  fi

  # Config decision (full updates only).
  local cfg_status="none"   # none | create | merge | skip
  if [ "$ONLY_AGENTS" = 0 ] && [ "$ONLY_SKILLS" = 0 ] && [ "$ONLY_PLUGIN" = 0 ]; then
    local cfg_dest="$CONFIG_DIR/opencode.json"
    if [ ! -f "$cfg_dest" ]; then
      info "config: opencode.json is missing - creating from opencode.template.json"
      cfg_status="create"
    else
      local cfg_base cfg_cur
      cfg_base="$(state_get "opencode.json")"
      cfg_cur="$(sha256 "$cfg_dest")"
      if [ -n "$cfg_base" ] && [ "$cfg_base" = "$cfg_cur" ]; then
        info "config: opencode.json is managed - merging template defaults (your settings always win)"
        cfg_status="merge"
      elif [ "$INTERACTIVE" = 1 ]; then
        printf 'config: opencode.json is user-modified. Merge template defaults into it? Your existing settings always win; only missing defaults are added. The file will be snapshotted first. [y/N] '
        local ans=""
        read -r ans || ans="n"
        case "$ans" in y | Y | yes | YES) cfg_status="merge" ;; *) cfg_status="skip" ;; esac
      else
        info "config: opencode.json is user-modified - skipped. Re-run with --interactive to merge the template in."
        cfg_status="skip"
      fi
    fi
  fi

  if [ "${#TO_INSTALL[@]}" -eq 0 ] && [ "$cfg_status" != "create" ] && [ "$cfg_status" != "merge" ]; then
    printf '\n'
    info "nothing to update: the workspace is up to date."
    exit 0
  fi

  # Snapshot everything that will be replaced.
  local backup_root="" ts
  local existing=()
  for rel in ${TO_INSTALL[@]+"${TO_INSTALL[@]}"}; do
    [ -f "$CONFIG_DIR/$rel" ] && existing+=("$rel")
  done
  if [ "${#existing[@]}" -gt 0 ]; then
    ts="$(unique_ts)"
    backup_root="$CONFIG_DIR/backups/supervisor-$ts"
    snapshot "$backup_root" ${existing[@]+"${existing[@]}"}
    info "backup: ${#existing[@]} file(s) snapshotted to $backup_root"
  fi

  # Apply content files.
  local updated=0
  for rel in ${TO_INSTALL[@]+"${TO_INSTALL[@]}"}; do
    mkdir -p "$CONFIG_DIR/$(dirname "$rel")"
    cp "$REPO_ROOT/$rel" "$CONFIG_DIR/$rel"
    state_set "$rel" "$(sha256 "$REPO_ROOT/$rel")"
    updated=$((updated + 1))
  done
  [ "$updated" -gt 0 ] && info "updated/installed: $updated file(s)."

  # Refresh baselines for managed files that were already up to date.
  for rel in ${UP_TO_DATE[@]+"${UP_TO_DATE[@]}"}; do
    state_set "$rel" "$(sha256 "$REPO_ROOT/$rel")"
  done

  # Config.
  if [ "$cfg_status" = "create" ]; then
    mkdir -p "$CONFIG_DIR"
    cp "$CONFIG_TEMPLATE" "$CONFIG_DIR/opencode.json"
    info "config: created opencode.json from opencode.template.json"
    state_set "opencode.json" "$(sha256 "$CONFIG_DIR/opencode.json")"
  elif [ "$cfg_status" = "merge" ]; then
    local cfg_ts
    cfg_ts="$(unique_ts)"
    local cfg_root="$CONFIG_DIR/backups/supervisor-$cfg_ts"
    snapshot "$cfg_root" "opencode.json"
    if [ "$cfg_root" != "$backup_root" ]; then
      info "backup: opencode.json snapshotted to $cfg_root"
    fi
    if ! node "$MERGE_SCRIPT" "$CONFIG_DIR/opencode.json"; then
      error "config merge failed"
      exit 1
    fi
    state_set "opencode.json" "$(sha256 "$CONFIG_DIR/opencode.json")"
  fi

  write_state

  printf '\n'
  info "summary:"
  info "  updated/installed: $updated file(s)."
  local skipped=0
  for rel in ${TO_PROMPT[@]+"${TO_PROMPT[@]}"}; do
    if ! printf '%s\n' ${TO_INSTALL[@]+"${TO_INSTALL[@]}"} | grep -qxF "$rel"; then
      skipped=$((skipped + 1))
    fi
  done
  if [ "$skipped" -gt 0 ]; then
    info "  skipped (user-modified): $skipped file(s) - run ./update.sh --interactive to decide."
  fi
  if [ -n "$backup_root" ]; then
    info "  backup:            $backup_root"
    info "  undo:              ./update.sh --rollback $(basename "$backup_root")"
  fi
  info "  state baseline:    $CONFIG_DIR/$STATE_FILE"
  exit 0
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

[ -f "$CONFIG_TEMPLATE" ] || { error "missing $CONFIG_TEMPLATE"; exit 1; }
[ -f "$MERGE_SCRIPT" ] || { error "missing $MERGE_SCRIPT"; exit 1; }

load_state

if [ -n "$ROLLBACK" ]; then
  do_rollback
fi

collect_files
: > "$PLAN_DIR/status.tsv"
: > "$PLAN_DIR/to_install.tsv"
classify
# Sort the state baseline once, before removed-upstream detection needs it.
LC_ALL=C sort -u -t "$(printf '\t')" -k1,1 "$PLAN_DIR/state.tsv" > "$PLAN_DIR/state.sorted"
classify_removed
print_plan

if [ "$DIFF" = 1 ]; then
  show_diffs
fi

if [ "$DRY_RUN" = 1 ]; then
  printf '\n'
  if [ "${#TO_INSTALL[@]}" -eq 0 ] && [ "${#TO_PROMPT[@]}" -eq 0 ]; then
    info "dry run: nothing to update (workspace is up to date)."
  else
    info "dry run: ${#TO_INSTALL[@]} file(s) would be installed/updated; ${#TO_PROMPT[@]} file(s) conflict (user-modified, skipped unless --interactive)."
  fi
  info "dry run: no changes written (no backups, no copies, no state update)."
  exit 0
fi

apply
