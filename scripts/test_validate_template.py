"""Tests for scripts/validate-template.py.

Property-based tests (hypothesis) cover the YAML-subset frontmatter
parser: round-trip rendering of arbitrary nested maps and crash-freedom
on arbitrary input. Unit tests cover the malformed-input error paths and
smoke checks against the real ``agents/worker.md`` and
``agents/claude-mule.md``.
"""

import importlib.util
import string
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

_VALIDATOR = Path(__file__).resolve().parent / "validate-template.py"
_spec = importlib.util.spec_from_file_location("validate_template", _VALIDATOR)
assert _spec is not None and _spec.loader is not None
vt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vt)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def render(data, indent=0):
    """Render a dict of scalars/nested dicts in the parser's input format."""
    out = []
    for key, value in data.items():
        if isinstance(value, dict):
            out.append(" " * indent + f"{key}:")
            out.extend(render(value, indent + 2))
        else:
            out.append(" " * indent + f"{key}: {value}")
    return out


keys = st.one_of(
    st.just("*"),
    st.text(
        alphabet=string.ascii_lowercase + "0123456789_",
        min_size=1,
        max_size=10,
    ),
)
scalars = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_.,:/-",
    min_size=1,
    max_size=30,
)
maps = st.recursive(
    st.dictionaries(keys, scalars, min_size=1, max_size=4),
    lambda children: st.dictionaries(keys, children, min_size=1, max_size=4),
    max_leaves=20,
)


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


@given(maps)
def test_round_trip_parse_of_render(data):
    lines = render(data)
    parsed, idx = vt.parse_map(lines, 0, 0)
    assert parsed == data
    assert idx == len(lines)


@given(st.text(max_size=500))
def test_arbitrary_text_only_raises_frontmatter_error(text):
    try:
        vt.parse_map(text.split("\n"), 0, 0)
    except vt.FrontmatterError:
        pass  # the only acceptable exception


@given(st.recursive(scalars, lambda c: st.lists(c, max_size=4), max_leaves=15))
def test_find_hardcoded_keys_never_crashes(data):
    found = vt.find_hardcoded_keys(data)
    assert isinstance(found, list)
    assert all(isinstance(item, str) for item in found)


# ---------------------------------------------------------------------------
# Unit tests: malformed frontmatter
# ---------------------------------------------------------------------------


def test_tab_indentation_rejected():
    with pytest.raises(vt.FrontmatterError, match="tab"):
        vt.parse_map(["permission:", "\tedit: deny"], 0, 0)


def test_line_without_colon_rejected():
    with pytest.raises(vt.FrontmatterError, match="key: value"):
        vt.parse_map(["description"], 0, 0)


def test_unexpected_indentation_rejected():
    with pytest.raises(vt.FrontmatterError, match="unexpected indentation"):
        vt.parse_map(["a: 1", "  b: 2", "    c: 3", " d: 4"], 0, 0)


def test_missing_opening_delimiter(tmp_path):
    path = tmp_path / "agent.md"
    path.write_text("description: hi\n", encoding="utf-8")
    with pytest.raises(vt.FrontmatterError, match="missing opening"):
        vt.extract_frontmatter(path)


def test_unterminated_frontmatter(tmp_path):
    path = tmp_path / "agent.md"
    path.write_text("---\ndescription: hi\n", encoding="utf-8")
    with pytest.raises(vt.FrontmatterError, match="unterminated"):
        vt.extract_frontmatter(path)


# ---------------------------------------------------------------------------
# Unit tests: validation rules
# ---------------------------------------------------------------------------


def test_task_deny_accepts_both_forms():
    errors = []
    vt.check_task_deny({"permission": {"task": "deny"}}, "worker-mule", "w", errors)
    vt.check_task_deny(
        {"permission": {"task": {"*": "deny"}}}, "worker-mule", "w", errors
    )
    assert errors == []


def test_task_deny_rejects_allow():
    errors = []
    vt.check_task_deny(
        {"permission": {"task": {"*": "allow"}}}, "worker-mule", "w", errors
    )
    assert len(errors) == 1


def test_hidden_rules():
    errors = []
    vt.check_hidden({}, "worker-mule", "w", errors)  # mule must be hidden
    assert len(errors) == 1
    errors = []
    vt.check_hidden({"hidden": "true"}, "worker", "w", errors)  # mid must not
    assert len(errors) == 1
    errors = []
    vt.check_hidden({"hidden": "true"}, "observer", "w", errors)  # hidden ok
    assert errors == []


def test_observer_claude_must_be_hidden():
    errors = []
    vt.check_hidden({}, "observer-claude", "w", errors)
    assert len(errors) == 1


def test_observer_claude_must_deny_task():
    errors = []
    vt.check_task_deny(
        {"permission": {"task": {"*": "allow"}}}, "observer-claude", "w", errors
    )
    assert len(errors) == 1


def test_observer_claude_model_enforced():
    errors = []
    vt.check_model({"model": "google/gemini-3.8-flash"}, "observer-claude", "w", errors)
    assert len(errors) == 1
    errors = []
    vt.check_model(
        {"model": "anthropic/claude-sonnet-5"}, "observer-claude", "w", errors
    )
    assert errors == []


def test_gemini_agents_model_enforced():
    for name in ("gemini-worker", "gemini-mule", "observer"):
        errors = []
        vt.check_model({"model": "deepseek/deepseek-flash"}, name, "w", errors)
        assert len(errors) == 1
        errors = []
        vt.check_model({"model": "google/gemini-3.8-flash"}, name, "w", errors)
        assert errors == []


def test_supervisor_model_enforced():
    errors = []
    vt.check_model({"model": "anthropic/claude-opus-5"}, "supervisor", "w", errors)
    assert len(errors) == 1
    errors = []
    vt.check_model({"model": "deepseek/deepseek-flash"}, "supervisor", "w", errors)
    assert errors == []


def test_agent_with_steps_rejected():
    errors = []
    vt.check_steps({"steps": 30}, "agents/worker-mule.md", errors)
    assert errors == [
        "agents/worker-mule.md: agents must not declare 'steps' — "
        "step caps are no longer used"
    ]


def test_agent_without_steps_passes():
    errors = []
    vt.check_steps({}, "agents/worker-mule.md", errors)
    assert errors == []


def test_validate_agent_flags_steps_end_to_end(tmp_path):
    path = tmp_path / "worker-mule.md"
    path.write_text(
        "---\n"
        "description: Bounded leaf agent.\n"
        "mode: subagent\n"
        "hidden: true\n"
        "model: deepseek/deepseek-flash\n"
        "steps: 30\n"
        "permission:\n"
        "  task: deny\n"
        "---\n",
        encoding="utf-8",
    )
    errors = []
    vt.validate_agent("worker-mule", "agents/worker-mule.md", path, errors)
    assert len(errors) == 1
    assert "must not declare 'steps'" in errors[0]


# ---------------------------------------------------------------------------
# Smoke test against the real template
# ---------------------------------------------------------------------------


def test_real_worker_agent_passes():
    path = Path(__file__).resolve().parent.parent / "agents" / "worker.md"
    fm = vt.extract_frontmatter(path)
    assert fm["mode"] == "subagent"
    assert fm["model"] == "anthropic/claude-sonnet-5"
    assert "steps" not in fm  # step caps are no longer used
    errors = []
    vt.validate_agent("worker", "agents/worker.md", path, errors)
    assert errors == []


def test_real_claude_mule_passes():
    path = Path(__file__).resolve().parent.parent / "agents" / "claude-mule.md"
    fm = vt.extract_frontmatter(path)
    assert fm["model"] == "anthropic/claude-sonnet-5"
    assert "steps" not in fm  # step caps are no longer used
    errors = []
    vt.validate_agent("claude-mule", "agents/claude-mule.md", path, errors)
    assert errors == []


def test_real_worker_mule_passes():
    path = Path(__file__).resolve().parent.parent / "agents" / "worker-mule.md"
    errors = []
    vt.validate_agent("worker-mule", "agents/worker-mule.md", path, errors)
    assert errors == []


def test_real_observer_claude_passes():
    path = Path(__file__).resolve().parent.parent / "agents" / "observer-claude.md"
    fm = vt.extract_frontmatter(path)
    assert fm["mode"] == "subagent"
    assert fm["model"] == "anthropic/claude-sonnet-5"
    errors = []
    vt.validate_agent("observer-claude", "agents/observer-claude.md", path, errors)
    assert errors == []


def test_real_supervisor_passes():
    path = Path(__file__).resolve().parent.parent / "agent" / "supervisor.md"
    fm = vt.extract_frontmatter(path)
    assert fm["mode"] == "primary"
    assert fm["model"] == "deepseek/deepseek-flash"
    errors = []
    vt.validate_agent("supervisor", "agent/supervisor.md", path, errors)
    assert errors == []


def test_real_observer_passes():
    path = Path(__file__).resolve().parent.parent / "agents" / "observer.md"
    fm = vt.extract_frontmatter(path)
    assert fm["mode"] == "subagent"
    assert fm["model"] == "google/gemini-3.8-flash"
    errors = []
    vt.validate_agent("observer", "agents/observer.md", path, errors)
    assert errors == []


def test_real_gemini_agents_pass():
    base = Path(__file__).resolve().parent.parent / "agents"
    for name in ("gemini-worker", "gemini-mule"):
        path = base / f"{name}.md"
        fm = vt.extract_frontmatter(path)
        assert fm["model"] == "google/gemini-3.8-flash"
        errors = []
        vt.validate_agent(name, f"agents/{name}.md", path, errors)
        assert errors == []
