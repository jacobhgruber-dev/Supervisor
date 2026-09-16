#!/usr/bin/env python3
"""Template validator for the Supervisor OpenCode template.

Validates, using only the Python standard library:

* All 48 agent files (1 in ``agent/``, 47 in ``agents/``):
  - valid YAML frontmatter, non-empty description, correct mode
    (``primary`` for supervisor, ``subagent`` for everyone else),
    and a valid model.
  - ``hidden: true`` on all 13 mules (``*-mule.md``), ``observer``,
    ``observer-claude``, ``local-coder``, and ``local-reasoner``; and NOT on
    junior/mid/senior role agents, ``designer``, ``grok-worker``,
    ``gemini-worker``, or ``supervisor``.
  - NO ``steps`` key on any agent: step caps are no longer used anywhere
    in the template — every agent runs uncapped.
  - ``task: {"*": "deny"}`` (or ``task: deny``) on all mules,
    ``observer``, ``observer-claude``, ``local-coder``, and
    ``local-reasoner``.
  - model per tier: junior → ``deepseek/deepseek-flash``, mid →
    ``anthropic/claude-sonnet-5``, senior → ``anthropic/claude-opus-5``,
    Grok agents → ``xai/grok-4.6``; ``observer-claude`` →
    ``anthropic/claude-sonnet-5``.
* ``opencode.template.json`` (or ``opencode.json`` with ``--installed``):
  valid JSON, ``default_agent: supervisor``, ``subagent_depth: 3``, and
  no hardcoded API keys.
* No private/OSINT skills (anything matching ``*osint*``) under
  ``skills/``.

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
EXPECTED_SUBAGENT_FILES = 47  # agents/ must contain exactly 47 files
PRIMARY_AGENT_NAME = "supervisor"

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
MID_MODEL = "anthropic/claude-sonnet-5"
SENIOR_MODEL = "anthropic/claude-opus-5"
GROK_MODEL = "xai/grok-4.6"
OBSERVER_CLAUDE_NAME = "observer-claude"  # Claude Sonnet 5 fallback observer

# Agents that must be hidden (in addition to every *-mule).
HIDDEN_EXTRA = {"observer", "observer-claude", "local-coder", "local-reasoner"}

# Agents that must be denied the ability to spawn further agents
# (in addition to every *-mule).
TASK_DENY_EXTRA = {"observer", "observer-claude", "local-coder", "local-reasoner"}

# Config keys/values that look like hardcoded secrets.
KEY_NAME_RE = re.compile(
    r"\b(api[_\s-]?key|access[_\s-]?key|secret|token|password|passwd|"
    r"private[_\s-]?key|bearer)\b",
    re.IGNORECASE,
)
VALUE_PREFIX_RE = re.compile(
    r"^(sk-|rk-|xai-|ghp_|github_pat_|AKIA|AIza|eyJ|hf_|pk_|dckr_|glpat-)",
)
PLACEHOLDER_RE = re.compile(r"^(YOUR_|\$\{|<)")


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


def parse_map(lines: List[str], idx: int, indent: int) -> Tuple[Dict[str, Any], int]:
    """Parse a YAML-subset mapping from *lines* starting at *idx*.

    Supports ``key: scalar`` entries (quoted or unquoted scalars, quoted
    keys such as ``"*"``) and nested mappings indented with spaces.
    Raises :class:`FrontmatterError` on malformed input.
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
        if "\t" in leading:
            raise FrontmatterError("tab indentation is not valid YAML")
        cur = len(leading)
        if cur < indent:
            break
        if cur > indent:
            raise FrontmatterError(f"unexpected indentation: {stripped!r}")
        if ":" not in stripped:
            raise FrontmatterError(f"expected 'key: value', got: {stripped!r}")
        key, _, rest = stripped.partition(":")
        key = key.strip().strip("\"'")
        if not key:
            raise FrontmatterError(f"empty key: {stripped!r}")
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


def expected_model(name: str) -> Optional[Tuple[str, str]]:
    """Return (tier label, expected model) for tiered agents, else None."""
    if name.startswith("junior-"):
        return ("junior-tier agents", JUNIOR_MODEL)
    if name.startswith("senior-"):
        return ("senior-tier agents", SENIOR_MODEL)
    if name in MID_TIER_ROLES:
        return ("mid-tier agents", MID_MODEL)
    return None


def check_model(fm: Dict[str, Any], name: str, rel: str, errors: List[str]) -> None:
    model = fm.get("model")
    if not isinstance(model, str) or not model.strip():
        errors.append(f"{rel}: missing or empty 'model'")
        return
    if name == OBSERVER_CLAUDE_NAME:
        if model != MID_MODEL:
            errors.append(
                f"{rel}: '{OBSERVER_CLAUDE_NAME}' must use '{MID_MODEL}', got '{model}'"
            )
        return
    tier = expected_model(name)
    if tier is not None:
        label, expected = tier
        if model != expected:
            errors.append(f"{rel}: {label} must use '{expected}', got '{model}'")
    elif model.startswith("xai/") and model != GROK_MODEL:
        errors.append(f"{rel}: Grok agents must use '{GROK_MODEL}', got '{model}'")


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
    if not must_deny_task(name):
        return
    perm = fm.get("permission")
    task = perm.get("task") if isinstance(perm, dict) else None
    ok = task == "deny" or (isinstance(task, dict) and task.get("*") == "deny")
    if not ok:
        errors.append(
            f"{rel}: must deny task spawning ('task: deny' or 'task: {{\"*\": deny}}')"
        )


def validate_agent(name: str, rel: str, path: Path, errors: List[str]) -> None:
    try:
        fm = extract_frontmatter(path)
    except FrontmatterError as exc:
        errors.append(f"{rel}: {exc}")
        return
    check_description(fm, rel, errors)
    check_mode(fm, name, rel, errors)
    check_model(fm, name, rel, errors)
    check_hidden(fm, name, rel, errors)
    check_steps(fm, rel, errors)
    check_task_deny(fm, name, rel, errors)


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


def validate_structure(root: Path, errors: List[str]) -> None:
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
    else:
        files = sorted(agents_dir.glob("*.md"))
        if len(files) != EXPECTED_SUBAGENT_FILES:
            errors.append(
                f"'agents/' must contain exactly {EXPECTED_SUBAGENT_FILES} files, "
                f"found {len(files)}"
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
    if data.get("subagent_depth") != 3:
        errors.append(
            f"{config_path.name}: 'subagent_depth' must be 3, "
            f"got {data.get('subagent_depth')!r}"
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


def validate(root: Path, config_path: Path) -> Tuple[List[str], bool]:
    errors: List[str] = []
    validate_structure(root, errors)
    for name, rel, path in iter_agent_files(root):
        validate_agent(name, rel, path, errors)
    validate_config(config_path, errors)
    skills_present = validate_skills(root / "skills", errors)
    return errors, skills_present


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

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

    errors, skills_present = validate(root, config_path)
    files = iter_agent_files(root)
    total = len(files)

    print(f"Validating template in {root}")
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
        f"OK: {config_path.name} (default_agent={PRIMARY_AGENT_NAME!r}, subagent_depth=3)"
    )
    if skills_present:
        print("OK: skills/ contains no *osint* entries")
    else:
        print("SKIP: no skills/ directory found")
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
