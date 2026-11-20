#!/usr/bin/env python3
"""Template validator for the Supervisor OpenCode template.

Validates, using only the Python standard library:

* All 46 agent files (1 in ``agent/``, 45 in ``agents/``):
  - valid YAML frontmatter, non-empty description, correct mode
    (``primary`` for supervisor, ``subagent`` for everyone else),
    and a valid model.
  - ``hidden: true`` on all 13 mules (``*-mule.md``) plus ``observer``
    and ``observer-claude``; NOT on any other agent (role agents,
    ``designer``, the addon workers ``grok-worker`` / ``gemini-worker``,
    and ``supervisor`` stay @-mentionable).
  - NO ``steps`` key on any agent: step caps are no longer used anywhere
    in the template — every agent runs uncapped.
  - NO V2-conflicting frontmatter keys (``permissions``, ``request``,
    ``system``, ``disabled``) on any agent file: OpenCode V2 silently
    drops that file's V1 ``permission`` block when any of these sibling
    keys are also present (only a log warning — not a hard error from
    OpenCode itself).
  - mules, ``observer``, and ``observer-claude``: ``permission.task``
    must be EXACTLY ``{"*": "deny"}`` (or the bare string ``"deny"``) —
    any extra key (e.g. a leaked ``"*-mule": allow``) is rejected, since
    these agents must be structurally unable to spawn anything.
  - role agents (junior/mid/senior tiers, ``designer``, ``grok-worker``,
    ``gemini-worker``): ``permission.task`` must be a mapping whose keys
    are exactly ``["*", "*-mule"]`` IN THAT ORDER, with ``"*": deny`` and
    ``"*-mule": allow``. Order is load-bearing — OpenCode permission
    globs are last-match-wins, so a reversed order silently removes mule
    spawning with no error from OpenCode.
  - role agents and mules (NOT ``observer``/``observer-claude``/
    ``supervisor``) must grant ``allow`` for ``webfetch``, ``websearch``,
    and ``playwright_*``, and must NOT set ``edit``/``bash`` to ``deny``
    (observers are exempt from the edit/bash rule and must stay denied).
  - ``supervisor`` must NOT declare a ``permission`` frontmatter block
    at all.
  - any agent whose model is a Grok model (``xai/...``) must NOT set
    ``variant: max`` — no Grok model exposes a ``max`` variant.
    Requesting one only fails at actual spawn time (a provider-side
    rejection this static frontmatter check cannot observe directly), so
    this only catches the known-bad combination ahead of time.
  - model per tier: junior → ``deepseek/deepseek-flash``, mid →
    ``anthropic/claude-sonnet-5-5``, senior → ``anthropic/claude-opus-5-5``,
    Grok agents → ``xai/grok-4.7``; Gemini agents (``gemini-worker``,
    ``gemini-mule``, ``observer``) → ``google/gemini-4-hydrogen``;
    ``observer-claude`` → ``anthropic/claude-sonnet-5-5``; ``supervisor`` →
    ``deepseek/deepseek-flash``.
* ``opencode.template.json`` (or ``opencode.json`` with ``--installed``):
  valid JSON, ``default_agent: supervisor``, ``experimental.subagent_depth``
  >= 2, ``experimental.todo: true``, no stray top-level ``subagent_depth``
  (OpenCode V2 ignores it with a warning), and no hardcoded API keys.
  ``experimental.*`` is labeled experimental by OpenCode and may change
  without notice.
* No private/OSINT skills (anything matching ``*osint*``) under
  ``skills/``.
* The observer-bridge plugin is on the OpenCode V2 layout:
  ``plugins/observer-bridge/index.js`` exists and calls ``Plugin.define``,
  no leftover V1 ``plugin/`` directory with ``.js`` files exists, and the
  config's top-level ``plugin`` key (the deprecated V1 name; OpenCode still
  reads it) does not contain the stale ``"observer-bridge.js"`` string —
  that specific entry makes OpenCode V2 try to npm-install a package
  literally named that (and 404). A ``plugin`` key with other entries is
  not an error: it is deprecated, not harmful, and this check does not
  require renaming it to ``plugins``.

Usage:
    python3 scripts/validate-template.py [--fix-hidden] [--installed DIR]

Exit codes: 0 = valid, 1 = validation failures, 2 = usage error.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Template specification constants
# ---------------------------------------------------------------------------

EXPECTED_PRIMARY_FILES = 1  # agent/ must contain exactly one file
EXPECTED_SUBAGENT_FILES = 45  # agents/ must contain exactly 45 files
PRIMARY_AGENT_NAME = "supervisor"

# V2 semantics: default is 1 (a subagent cannot spawn a subagent). 2 allows
# supervisor -> role agent -> mule (mules are leaf nodes and never spawn
# further). This lives under "experimental" — a bare top-level
# "subagent_depth" is ignored by OpenCode V2 with a warning.
MIN_SUBAGENT_DEPTH = 2

# Mid-tier role agents (bare names). ``designer`` and the addon workers are
# NOT mid-tier roles: they run on other providers.
MID_TIER_ROLES = {
    "worker",
    "architect",
    "planner",
    "reviewer",
    "debugger",
    "security",
    "editor",
    "researcher",
    "quote-auditor",
}

JUNIOR_MODEL = "deepseek/deepseek-flash"
MID_MODEL = "anthropic/claude-sonnet-5-5"
SENIOR_MODEL = "anthropic/claude-opus-5-5"
GROK_MODEL = "xai/grok-4.7"
GEMINI_MODEL = "google/gemini-4-hydrogen"
SUPERVISOR_MODEL = "deepseek/deepseek-flash"
OBSERVER_CLAUDE_NAME = "observer-claude"  # Claude Sonnet 5.5 fallback observer

# Gemini-modeled agents (bare names): the Gemini workers and the
# multimodal observer.
GEMINI_AGENTS = {"gemini-worker", "gemini-mule", "observer"}

# Agents that must be hidden in addition to every *-mule: the two
# observer leaves (``observer``, ``observer-claude``).
HIDDEN_EXTRA: set[str] = {"observer", "observer-claude"}

# Agents that must be denied the ability to spawn further agents
# (in addition to every *-mule): the observer leaves.
TASK_DENY_EXTRA = {"observer", "observer-claude"}

# The observer leaves by name. Defined independently of HIDDEN_EXTRA /
# TASK_DENY_EXTRA (even though the three sets are currently identical) so
# is_observer() below does not silently change meaning if either of those
# ever needs to diverge from "exactly the two observer agents".
OBSERVER_NAMES = {"observer", "observer-claude"}

# Identity-keyed expected model for EVERY template agent name — the single
# source of truth for check_model(). Each of the 46 names maps to exactly
# one expected model; there is no provider-prefix fallback, so an agent
# whose current (possibly wrong) model doesn't happen to start with a
# recognizable prefix can no longer slip through unchecked (that was the
# bug: 9 generic DeepSeek mules, ``designer``, ``designer-mule``,
# ``grok-worker``, and ``grok-mule`` previously had no real enforcement).
EXPECTED_MODEL_BY_NAME: Dict[str, str] = {
    PRIMARY_AGENT_NAME: SUPERVISOR_MODEL,
    OBSERVER_CLAUDE_NAME: MID_MODEL,
    "grok-worker": GROK_MODEL,
    "designer": GROK_MODEL,
    "grok-mule": GROK_MODEL,
    "designer-mule": GROK_MODEL,
    "claude-mule": MID_MODEL,
    **{name: GEMINI_MODEL for name in GEMINI_AGENTS},
    **{role: MID_MODEL for role in MID_TIER_ROLES},
    **{f"junior-{role}": JUNIOR_MODEL for role in MID_TIER_ROLES},
    **{f"senior-{role}": SENIOR_MODEL for role in MID_TIER_ROLES},
    **{f"{role}-mule": JUNIOR_MODEL for role in MID_TIER_ROLES},
}

# The 45 template subagent names (every EXPECTED_MODEL_BY_NAME key except
# the primary supervisor) — i.e. everything that belongs in agents/. Used
# by --installed mode to confirm every template agent is present even
# when the user has added their own extra agent files alongside them.
EXPECTED_SUBAGENT_NAMES = set(EXPECTED_MODEL_BY_NAME) - {PRIMARY_AGENT_NAME}

# Frontmatter keys that conflict with OpenCode V2: V2 silently drops a
# file's V1 "permission" block (log warning only, no hard error) when any
# of these sibling keys are also present in frontmatter.
V2_MARKER_KEYS = ("permissions", "request", "system", "disabled")

# Web-tool permission keys every role agent and mule must grant.
WEB_TOOL_KEYS = ("webfetch", "websearch", "playwright_*")

# Expected key ORDER for a role agent's permission.task mapping. OpenCode
# permission globs are last-match-wins, so "*" (deny) must be listed
# before "*-mule" (allow) — reversing the order silently removes mule
# spawning with no error from OpenCode.
ROLE_TASK_KEYS = ["*", "*-mule"]

# Config keys/values that look like hardcoded secrets.
KEY_NAME_RE = re.compile(
    r"\b(api[_\s-]?key|access[_\s-]?key|secret|token|password|passwd|"
    r"private[_\s-]?key|bearer)\b",
    re.IGNORECASE,
)
VALUE_PREFIX_RE = re.compile(
    r"^(sk-|rk-|xai-|ghp_|github_pat_|AKIA|AIza|eyJ|hf_|pk_|dckr_|glpat-)",
)
# ``{env:VAR}`` and ``{file:path}`` are OpenCode's own documented config
# substitutions (resolved at load time, e.g. ``"apiKey": "{env:OPENAI_API_KEY}"``)
# — not hardcoded secrets, so they must not be flagged in --installed mode.
PLACEHOLDER_RE = re.compile(r"^(YOUR_|\$\{|<|\{env:|\{file:)")


class FrontmatterError(Exception):
    """Raised when agent frontmatter is missing or malformed."""


# ---------------------------------------------------------------------------
# Minimal YAML-subset parser (frontmatter only: scalars + nested maps)
# ---------------------------------------------------------------------------


def indent_width(line: str) -> int:
    return len(line) - len(line.lstrip())


def parse_scalar(raw: str) -> str:
    """Parse a scalar value: strip quotes and trailing comments."""
    value = raw.strip()
    if value and value[0] not in "\"'":
        cut = re.search(r"\s+#", value)
        if cut:
            value = value[: cut.start()].rstrip()
    if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
        return value[1:-1]
    return value


def parse_line_key(
    stripped: str, leading: str, cur: int, indent: int, data: Dict[str, Any]
) -> Tuple[str, str]:
    """Validate and split one 'key: rest' frontmatter line for parse_map().

    Returns ``(key, rest)``. Raises :class:`FrontmatterError` for tab
    indentation, indentation deeper than *indent*, a missing colon, an
    empty key, or a key already present in *data* (a duplicate key at
    this nesting level).
    """
    if "\t" in leading:
        raise FrontmatterError("tab indentation is not valid YAML")
    if cur > indent:
        raise FrontmatterError(f"unexpected indentation: {stripped!r}")
    if ":" not in stripped:
        raise FrontmatterError(f"expected 'key: value', got: {stripped!r}")
    key, _, rest = stripped.partition(":")
    key = key.strip().strip("\"'")
    if not key:
        raise FrontmatterError(f"empty key: {stripped!r}")
    if key in data:
        raise FrontmatterError(f"duplicate key: {key!r}")
    return key, rest


def parse_map(lines: List[str], idx: int, indent: int) -> Tuple[Dict[str, Any], int]:
    """Parse a YAML-subset mapping from *lines* starting at *idx*.

    Supports ``key: scalar`` entries (quoted or unquoted scalars, quoted
    keys such as ``"*"``) and nested mappings indented with spaces.
    Raises :class:`FrontmatterError` on malformed input, including a
    duplicate key at the same nesting level.

    Intentionally unsupported: inline flow-style maps such as
    ``task: {"*": allow}``. Anything after ``key:`` on the same line is
    parsed as a scalar (see :func:`parse_scalar`), so a flow-style map
    would silently become a *string*, not a mapping, and downstream
    checks that expect ``permission.task`` to be a dict would then fail
    in a confusing way. Frontmatter like ``permission.task`` MUST use the
    nested block form instead::

        task:
          "*": deny
          "*-mule": allow

    This is why the template's own agent files never write inline
    ``{...}`` maps in frontmatter — only this nested block style
    round-trips correctly through this parser.
    """

    def next_nonblank(start: int) -> int:
        while start < len(lines) and not lines[start].strip():
            start += 1
        return start

    data: Dict[str, Any] = {}
    idx = next_nonblank(idx)
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        leading = line[: len(line) - len(line.lstrip())]
        cur = len(leading)
        if cur < indent:
            break
        key, rest = parse_line_key(stripped, leading, cur, indent, data)
        idx += 1
        if rest.strip():
            data[key] = parse_scalar(rest)
            idx = next_nonblank(idx)
            continue
        # Value is a nested mapping: skip blank lines, then recurse.
        child = next_nonblank(idx)
        if child < len(lines) and indent_width(lines[child]) > indent:
            nested, idx = parse_map(lines, child, indent_width(lines[child]))
            data[key] = nested
        else:
            data[key] = {}
        idx = next_nonblank(idx)
    return data, idx


def split_text(text: str) -> List[str]:
    if text.startswith("\ufeff"):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def extract_frontmatter(path: Path) -> Dict[str, Any]:
    """Extract and parse the YAML frontmatter of an agent file."""
    lines = split_text(path.read_text(encoding="utf-8"))
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("missing opening '---' frontmatter delimiter")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise FrontmatterError("unterminated frontmatter (missing closing '---')")
    data, _ = parse_map(lines[1:end], 0, 0)
    return data


# ---------------------------------------------------------------------------
# Value coercion helpers
# ---------------------------------------------------------------------------


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return isinstance(value, str) and value.strip().lower() == "true"


# ---------------------------------------------------------------------------
# Agent predicates
# ---------------------------------------------------------------------------


def is_mule(name: str) -> bool:
    return name.endswith("-mule")


def must_be_hidden(name: str) -> bool:
    return is_mule(name) or name in HIDDEN_EXTRA


def must_deny_task(name: str) -> bool:
    return is_mule(name) or name in TASK_DENY_EXTRA


def is_observer(name: str) -> bool:
    return name in OBSERVER_NAMES


def is_role_agent(name: str) -> bool:
    """True for every agent that is neither a mule, an observer, nor the
    supervisor — the 30 junior/mid/senior/designer/grok-worker/gemini-worker
    role agents that must be able to spawn mules (and only mules)."""
    return not is_mule(name) and not is_observer(name) and name != PRIMARY_AGENT_NAME


# ---------------------------------------------------------------------------
# Per-agent frontmatter checks
# ---------------------------------------------------------------------------


def check_description(fm: Dict[str, Any], rel: str, errors: List[str]) -> None:
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append(f"{rel}: missing or empty 'description'")


def check_mode(fm: Dict[str, Any], name: str, rel: str, errors: List[str]) -> None:
    mode = fm.get("mode")
    expected = "primary" if name == PRIMARY_AGENT_NAME else "subagent"
    if mode != expected:
        errors.append(f"{rel}: mode must be '{expected}', got {mode!r}")


def check_model(
    fm: Dict[str, Any],
    name: str,
    rel: str,
    errors: List[str],
    *,
    installed: bool = False,
) -> None:
    """Check 'model' against the identity-keyed EXPECTED_MODEL_BY_NAME map.

    Every one of the template's 46 agent names maps to exactly one
    expected model there — no provider-prefix fallback — so an agent
    whose current (possibly wrong) model string doesn't happen to start
    with a recognizable prefix can no longer slip through unchecked (the
    bug this replaces: the 9 generic DeepSeek mules, ``designer``,
    ``designer-mule``, ``grok-worker``, and ``grok-mule`` previously had
    no real model enforcement at all).

    A name absent from the map is a hard error in repo (template) mode:
    the template defines all 46 names exhaustively, so an unrecognized
    name there is itself a bug. In ``--installed`` mode a user may have
    added their own custom agent file alongside the template's; an
    unrecognized name there is simply skipped — this check has nothing
    to enforce for an agent the template doesn't define.
    """
    model = fm.get("model")
    if not isinstance(model, str) or not model.strip():
        errors.append(f"{rel}: missing or empty 'model'")
        return
    expected = EXPECTED_MODEL_BY_NAME.get(name)
    if expected is None:
        if not installed:
            errors.append(
                f"{rel}: '{name}' is not a recognized template agent name — "
                "no expected model is defined for it"
            )
        return
    if model != expected:
        errors.append(f"{rel}: '{name}' must use '{expected}', got '{model}'")


def check_hidden(fm: Dict[str, Any], name: str, rel: str, errors: List[str]) -> None:
    hidden = as_bool(fm.get("hidden"))
    if must_be_hidden(name) and not hidden:
        errors.append(f"{rel}: must have 'hidden: true'")
    elif not must_be_hidden(name) and hidden:
        errors.append(f"{rel}: must NOT have 'hidden: true'")


def check_steps(fm: Dict[str, Any], rel: str, errors: List[str]) -> None:
    """No agent may declare ``steps``: step caps are no longer used."""
    if "steps" in fm:
        errors.append(
            f"{rel}: agents must not declare 'steps' — step caps are no longer used"
        )


def check_task_deny(fm: Dict[str, Any], name: str, rel: str, errors: List[str]) -> None:
    """Mules, ``observer``, and ``observer-claude`` must deny ALL task
    spawning — ``task: deny`` or ``task: {"*": deny}`` with NO other key.
    An extra key (e.g. a leaked ``"*-mule": allow``) must fail: that would
    let a structural leaf spawn mules, which the mule tier must never do.
    """
    if not must_deny_task(name):
        return
    perm = fm.get("permission")
    task = perm.get("task") if isinstance(perm, dict) else None
    if task == "deny":
        return
    if (
        isinstance(task, dict)
        and list(task.keys()) == ["*"]
        and task.get("*") == "deny"
    ):
        return
    errors.append(
        f"{rel}: must deny ALL task spawning ('task: deny' or "
        f"'task: {{\"*\": deny}}' with no other keys), got {task!r}"
    )


def check_no_v2_markers(fm: Dict[str, Any], rel: str, errors: List[str]) -> None:
    """Agent files must not contain the V2-conflicting frontmatter keys
    ``permissions``, ``request``, ``system``, ``disabled``: OpenCode V2
    silently drops a file's V1 ``permission`` block when any of these
    sibling keys are present — only a log warning, not a hard error."""
    present = [key for key in V2_MARKER_KEYS if key in fm]
    if present:
        errors.append(
            f"{rel}: frontmatter must not contain V2-conflicting key(s) "
            f"{', '.join(sorted(present))} — OpenCode V2 silently drops "
            "the V1 'permission' block when any of these are present "
            "(only a log warning)"
        )


def check_role_task_permission(
    fm: Dict[str, Any], name: str, rel: str, errors: List[str]
) -> None:
    """Role agents must have ``permission.task`` as a mapping with keys
    EXACTLY ``["*", "*-mule"]`` in that order: ``"*": deny`` then
    ``"*-mule": allow``. OpenCode permission globs are last-match-wins, so
    reversing the order silently removes mule spawning with no error from
    OpenCode — order is load-bearing, not cosmetic.
    """
    if not is_role_agent(name):
        return
    perm = fm.get("permission")
    task = perm.get("task") if isinstance(perm, dict) else None
    if not isinstance(task, dict):
        errors.append(
            f"{rel}: role agents must have 'permission.task' as a mapping "
            f"{{'*': deny, '*-mule': allow}}, got {task!r}"
        )
        return
    keys = list(task.keys())
    if keys != ROLE_TASK_KEYS:
        errors.append(
            f"{rel}: 'permission.task' keys must be exactly {ROLE_TASK_KEYS} "
            "in that order (last-match-wins — a reversed order silently "
            f"removes mule spawning), got {keys!r}"
        )
        return
    if task.get("*") != "deny" or task.get("*-mule") != "allow":
        errors.append(
            f"{rel}: 'permission.task' must be {{'*': deny, '*-mule': allow}}, "
            f"got {task!r}"
        )


def check_web_tools_allowed(
    fm: Dict[str, Any], name: str, rel: str, errors: List[str]
) -> None:
    """Role agents and mules (NOT observer/observer-claude/supervisor)
    must grant 'allow' for webfetch, websearch, and playwright_*."""
    if not (is_role_agent(name) or is_mule(name)):
        return
    perm = fm.get("permission")
    perm = perm if isinstance(perm, dict) else {}
    missing = [key for key in WEB_TOOL_KEYS if perm.get(key) != "allow"]
    if missing:
        errors.append(
            f"{rel}: must grant 'allow' for {', '.join(missing)} "
            "(role agents and mules require web-tool access)"
        )


def check_edit_bash_not_denied(
    fm: Dict[str, Any], name: str, rel: str, errors: List[str]
) -> None:
    """edit/bash must not be 'deny' on any role agent or mule; observers
    are exempt from this rule (see check_observer_edit_bash_denied for
    their opposite requirement)."""
    if not (is_role_agent(name) or is_mule(name)):
        return
    perm = fm.get("permission")
    perm = perm if isinstance(perm, dict) else {}
    denied = [key for key in ("edit", "bash") if perm.get(key) == "deny"]
    if denied:
        errors.append(
            f"{rel}: {', '.join(denied)} must not be 'deny' for role agents and mules"
        )


def check_observer_edit_bash_denied(
    fm: Dict[str, Any], name: str, rel: str, errors: List[str]
) -> None:
    """Observers must keep BOTH edit and bash denied — they are read-only
    analysis agents. This is the enforcement side of the exemption granted
    to observers in check_edit_bash_not_denied above; without this, a
    template drift that dropped 'edit: deny'/'bash: deny' from observer.md
    or observer-claude.md would go uncaught."""
    if not is_observer(name):
        return
    perm = fm.get("permission")
    perm = perm if isinstance(perm, dict) else {}
    not_denied = [key for key in ("edit", "bash") if perm.get(key) != "deny"]
    if not_denied:
        errors.append(f"{rel}: {', '.join(not_denied)} must be 'deny' for observers")


def check_supervisor_no_permission(
    fm: Dict[str, Any], name: str, rel: str, errors: List[str]
) -> None:
    """The supervisor must not declare a 'permission' frontmatter block
    at all."""
    if name != PRIMARY_AGENT_NAME:
        return
    if "permission" in fm:
        errors.append(
            f"{rel}: '{PRIMARY_AGENT_NAME}' must NOT have a 'permission' "
            "frontmatter block"
        )


def check_grok_variant(fm: Dict[str, Any], rel: str, errors: List[str]) -> None:
    """Flag 'variant: max' on any Grok-modeled (``xai/...``) agent.

    No Grok model currently exposes a "max" variant. Requesting one only
    fails at actual spawn time — a provider-side rejection that this
    static frontmatter check cannot observe directly — so this only
    catches the known-bad 'variant: max' + Grok-model combination ahead
    of time; it cannot catch other invalid variants a provider might add
    or remove later.
    """
    model = fm.get("model")
    variant = fm.get("variant")
    if isinstance(model, str) and model.startswith("xai/") and variant == "max":
        errors.append(
            f"{rel}: Grok agents must not set 'variant: max' — no Grok "
            "model exposes a 'max' variant (this only fails at spawn "
            "time; static validation can only catch the frontmatter "
            "combination itself)"
        )


def validate_agent(
    name: str, rel: str, path: Path, errors: List[str], *, installed: bool = False
) -> None:
    try:
        fm = extract_frontmatter(path)
    except FrontmatterError as exc:
        errors.append(f"{rel}: {exc}")
        return
    check_description(fm, rel, errors)
    check_mode(fm, name, rel, errors)
    check_model(fm, name, rel, errors, installed=installed)
    check_hidden(fm, name, rel, errors)
    check_steps(fm, rel, errors)
    check_task_deny(fm, name, rel, errors)
    check_no_v2_markers(fm, rel, errors)
    check_role_task_permission(fm, name, rel, errors)
    check_web_tools_allowed(fm, name, rel, errors)
    check_observer_edit_bash_denied(fm, name, rel, errors)
    check_edit_bash_not_denied(fm, name, rel, errors)
    check_supervisor_no_permission(fm, name, rel, errors)
    check_grok_variant(fm, rel, errors)


# ---------------------------------------------------------------------------
# Directory structure, config, and skills checks
# ---------------------------------------------------------------------------


def iter_agent_files(root: Path) -> List[Tuple[str, str, Path]]:
    """Return (name, relpath, path) for every agent file under *root*."""
    found: List[Tuple[str, str, Path]] = []
    for sub in ("agent", "agents"):
        directory = root / sub
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            found.append((path.stem, f"{sub}/{path.name}", path))
    return found


def validate_structure(
    root: Path,
    errors: List[str],
    infos: List[str],
    *,
    installed: bool = False,
) -> None:
    """Check the agent/ and agents/ directory contents.

    ``agent/`` (the primary supervisor) is always strict: exactly one
    file, named ``supervisor.md``, in both repo and --installed mode.

    ``agents/`` (the 45 subagents) is strict-count in repo (template)
    mode: exactly ``EXPECTED_SUBAGENT_FILES``. In --installed mode a user
    may have added their own extra agent files alongside the template's,
    so the exact-count check is replaced with a presence check: every
    template subagent name must exist; anything beyond that is reported
    via *infos* (not an error) rather than failing validation.
    """
    agent_dir = root / "agent"
    if not agent_dir.is_dir():
        errors.append("missing 'agent/' directory")
    else:
        files = sorted(agent_dir.glob("*.md"))
        if len(files) != EXPECTED_PRIMARY_FILES:
            errors.append(
                f"'agent/' must contain exactly {EXPECTED_PRIMARY_FILES} file, "
                f"found {len(files)}"
            )
        elif files[0].name != f"{PRIMARY_AGENT_NAME}.md":
            errors.append(f"'agent/' must contain '{PRIMARY_AGENT_NAME}.md'")

    agents_dir = root / "agents"
    if not agents_dir.is_dir():
        errors.append("missing 'agents/' directory")
        return
    names = {path.stem for path in agents_dir.glob("*.md")}
    if not installed:
        if len(names) != EXPECTED_SUBAGENT_FILES:
            errors.append(
                f"'agents/' must contain exactly {EXPECTED_SUBAGENT_FILES} files, "
                f"found {len(names)}"
            )
        return
    missing = sorted(EXPECTED_SUBAGENT_NAMES - names)
    if missing:
        errors.append(
            f"'agents/' is missing {len(missing)} template agent file(s): "
            f"{', '.join(missing)}"
        )
    extra = sorted(names - EXPECTED_SUBAGENT_NAMES)
    if extra:
        infos.append(
            f"'agents/' has {len(extra)} extra user-added agent file(s) beyond "
            f"the template's {EXPECTED_SUBAGENT_FILES}: {', '.join(extra)}"
        )


def flag_secret_value(key: str, value: str, where: str) -> Optional[str]:
    """Return an error message if (key, value) looks like a hardcoded secret."""
    if not value or PLACEHOLDER_RE.match(value):
        return None
    if KEY_NAME_RE.search(key):
        return f"hardcoded secret in config key '{where}'"
    if VALUE_PREFIX_RE.match(value):
        return f"secret-looking value in config key '{where}'"
    return None


def find_hardcoded_keys(node: Any, path: str = "") -> List[str]:
    """Return messages for values that look like real secrets."""
    found: List[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            where = f"{path}/{key}" if path else str(key)
            if isinstance(value, str):
                message = flag_secret_value(key, value, where)
                if message:
                    found.append(message)
            else:
                found.extend(find_hardcoded_keys(value, where))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            found.extend(find_hardcoded_keys(value, f"{path}[{i}]"))
    return found


def validate_config(config_path: Path, errors: List[str]) -> None:
    if not config_path.exists():
        errors.append(f"missing config file: {config_path.name}")
        return
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{config_path.name}: invalid JSON: {exc}")
        return
    if data.get("default_agent") != PRIMARY_AGENT_NAME:
        errors.append(
            f"{config_path.name}: 'default_agent' must be "
            f"'{PRIMARY_AGENT_NAME}', got {data.get('default_agent')!r}"
        )
    if "subagent_depth" in data:
        errors.append(
            f"{config_path.name}: top-level 'subagent_depth' is ignored by "
            "OpenCode V2 (with a warning) and must be removed — use "
            "'experimental.subagent_depth' instead"
        )
    plugin_value = data.get("plugin")
    plugin_has_stale_entry = plugin_value == "observer-bridge.js" or (
        isinstance(plugin_value, list) and "observer-bridge.js" in plugin_value
    )
    if plugin_has_stale_entry:
        errors.append(
            f"{config_path.name}: top-level 'plugin' contains the stale "
            '"observer-bridge.js" entry — OpenCode V2 tries to npm-install '
            "it as a package (and 404s) — remove just that entry; V2 "
            "auto-discovers 'plugins/<name>/index.js' with no config entry "
            "needed for it. Other 'plugin' entries are not flagged by this "
            "check (the V1 'plugin' key itself is deprecated, not harmful)."
        )
    experimental = data.get("experimental")
    exp_depth = (
        experimental.get("subagent_depth") if isinstance(experimental, dict) else None
    )
    if (
        not isinstance(exp_depth, int)
        or isinstance(exp_depth, bool)
        or exp_depth < MIN_SUBAGENT_DEPTH
    ):
        errors.append(
            f"{config_path.name}: 'experimental.subagent_depth' must be an "
            f"int >= {MIN_SUBAGENT_DEPTH}, got {exp_depth!r}"
        )
    exp_todo = experimental.get("todo") if isinstance(experimental, dict) else None
    if exp_todo is not True:
        errors.append(
            f"{config_path.name}: 'experimental.todo' must be true, got {exp_todo!r}"
        )
    for message in find_hardcoded_keys(data):
        errors.append(f"{config_path.name}: {message}")


def validate_skills(skills_dir: Path, errors: List[str]) -> bool:
    """Validate the skills directory; return False if it does not exist."""
    if not skills_dir.is_dir():
        return False
    for path in skills_dir.rglob("*"):
        if fnmatch.fnmatch(path.name.lower(), "*osint*"):
            errors.append(f"skills/: private/OSINT skill found: {path.name}")
    return True


def validate_plugin(root: Path, errors: List[str]) -> None:
    """OpenCode V2 plugin layout for the observer-bridge plugin.

    ``plugins/observer-bridge/index.js`` must exist and call
    ``Plugin.define`` (the V2 plugin API), and no leftover V1 ``plugin/``
    directory with ``.js`` files may exist alongside it — V2 auto-discovers
    ``plugins/<name>/index.js`` and would also try (and fail) to load a
    stray V1 file found in a discovered plugin directory.
    """
    entry = root / "plugins" / "observer-bridge" / "index.js"
    if not entry.is_file():
        errors.append(
            "missing 'plugins/observer-bridge/index.js' (OpenCode V2 plugin "
            "entry point)"
        )
    else:
        text = entry.read_text(encoding="utf-8")
        if "Plugin.define" not in text:
            errors.append(
                "plugins/observer-bridge/index.js: must call 'Plugin.define' "
                "(OpenCode V2 plugin API)"
            )

    v1_dir = root / "plugin"
    if v1_dir.is_dir():
        leftovers = sorted(p.name for p in v1_dir.glob("*.js"))
        if leftovers:
            errors.append(
                "found a V1 'plugin/' directory with leftover .js file(s): "
                f"{', '.join(leftovers)} — OpenCode V2 auto-discovers "
                "'plugins/<name>/index.js' instead"
            )


# ---------------------------------------------------------------------------
# --fix-hidden support
# ---------------------------------------------------------------------------


def frontmatter_span(lines: List[str]) -> Optional[Tuple[int, int]]:
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return (0, i)
    return None


def mode_line_index(lines: List[str], lo: int, hi: int) -> Optional[int]:
    """Return the index of the frontmatter ``mode:`` line, if any."""
    for i in range(lo + 1, hi):
        if re.match(r"^mode:", lines[i].strip()):
            return i
    return None


def fix_hidden_for_file(name: str, rel: str, path: Path) -> Optional[str]:
    """Repair one file's hidden field; return 'added', 'removed', or None."""
    lines = split_text(path.read_text(encoding="utf-8"))
    span = frontmatter_span(lines)
    if span is None:
        return None  # malformed file; validation reports it
    lo, hi = span
    hidden_lines = [
        i for i in range(lo + 1, hi) if re.match(r"^hidden:", lines[i].strip())
    ]
    wants_hidden = must_be_hidden(name)
    if wants_hidden and not hidden_lines:
        mode_idx = mode_line_index(lines, lo, hi)
        lines.insert(mode_idx + 1 if mode_idx is not None else hi, "hidden: true")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return "added"
    if not wants_hidden and hidden_lines:
        for i in reversed(hidden_lines):
            del lines[i]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return "removed"
    return None


def apply_hidden_fixes(root: Path) -> None:
    """Add/remove ``hidden: true`` in agent frontmatter to match the spec."""
    added: List[str] = []
    removed: List[str] = []
    for name, rel, path in iter_agent_files(root):
        action = fix_hidden_for_file(name, rel, path)
        if action == "added":
            added.append(rel)
        elif action == "removed":
            removed.append(rel)
    for rel in added:
        print(f"FIXED: added 'hidden: true' to {rel}")
    for rel in removed:
        print(f"FIXED: removed 'hidden: true' from {rel}")
    if not added and not removed:
        print("No hidden-field fixes were needed.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the Supervisor OpenCode template.",
    )
    parser.add_argument(
        "--fix-hidden",
        action="store_true",
        help=(
            "add 'hidden: true' to agent files that require it and remove it "
            "from agent files that forbid it, then re-validate"
        ),
    )
    parser.add_argument(
        "--installed",
        type=Path,
        metavar="DIR",
        help=(
            "validate an installed copy of the template under DIR instead of "
            "the repository (uses DIR/opencode.json if present)"
        ),
    )
    return parser


def validate(
    root: Path, config_path: Path, *, installed: bool = False
) -> Tuple[List[str], bool, List[str]]:
    errors: List[str] = []
    infos: List[str] = []
    validate_structure(root, errors, infos, installed=installed)
    for name, rel, path in iter_agent_files(root):
        validate_agent(name, rel, path, errors, installed=installed)
    validate_config(config_path, errors)
    validate_plugin(root, errors)
    skills_present = validate_skills(root / "skills", errors)
    return errors, skills_present, infos


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    installed = bool(args.installed)

    if args.installed:
        root = args.installed.resolve()
        if (root / "opencode.json").exists():
            config_path = root / "opencode.json"
        else:
            config_path = root / "opencode.template.json"
    else:
        root = Path(__file__).resolve().parent.parent
        config_path = root / "opencode.template.json"

    if args.fix_hidden:
        apply_hidden_fixes(root)

    errors, skills_present, infos = validate(root, config_path, installed=installed)
    files = iter_agent_files(root)
    total = len(files)

    print(f"Validating template in {root}")
    for message in infos:
        print(f"INFO: {message}")
    if errors:
        for message in errors:
            print(f"ERROR: {message}")
        print(
            f"VALIDATION FAILED: {len(errors)} error(s) across "
            f"{total} agent files, config, and skills"
        )
        return 1

    print(f"OK: {total} agent files validated")
    print(
        f"OK: {config_path.name} (default_agent={PRIMARY_AGENT_NAME!r}, "
        f"experimental.subagent_depth>={MIN_SUBAGENT_DEPTH}, experimental.todo=true)"
    )
    print("OK: plugins/observer-bridge/ (V2 Plugin.define API, no V1 leftovers)")
    if skills_present:
        print("OK: skills/ contains no *osint* entries")
    else:
        print("SKIP: no skills/ directory found")
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
