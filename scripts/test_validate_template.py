"""Tests for scripts/validate-template.py.

Property-based tests (hypothesis) cover the YAML-subset frontmatter
parser: round-trip rendering of arbitrary nested maps and crash-freedom
on arbitrary input. Unit tests cover the malformed-input error paths and
smoke checks against the real ``agents/worker.md`` and
``agents/claude-mule.md``.
"""

import importlib.util
import json
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
# Unit tests: PLACEHOLDER_RE / flag_secret_value must treat OpenCode's
# documented config substitutions, '{env:VAR}' and '{file:path}', as
# placeholders — not hardcoded secrets (false positive in --installed mode).
# ---------------------------------------------------------------------------


def test_placeholder_re_matches_env_substitution():
    assert vt.PLACEHOLDER_RE.match("{env:OPENAI_API_KEY}")


def test_placeholder_re_matches_file_substitution():
    assert vt.PLACEHOLDER_RE.match("{file:./secrets/anthropic.key}")


def test_placeholder_re_still_matches_existing_forms():
    assert vt.PLACEHOLDER_RE.match("YOUR_API_KEY_HERE")
    assert vt.PLACEHOLDER_RE.match("${ANTHROPIC_API_KEY}")
    assert vt.PLACEHOLDER_RE.match("<your-key>")


def test_flag_secret_value_allows_env_substitution():
    assert vt.flag_secret_value("apiKey", "{env:OPENAI_API_KEY}", "where") is None


def test_flag_secret_value_allows_file_substitution():
    assert (
        vt.flag_secret_value("apiKey", "{file:./secrets/anthropic.key}", "where")
        is None
    )


def test_flag_secret_value_still_flags_secret_key_name():
    assert vt.flag_secret_value("apiKey", "sk-abcdef1234567890", "where") is not None


def test_flag_secret_value_still_flags_secret_looking_value():
    assert (
        vt.flag_secret_value("someSetting", "sk-abcdef1234567890", "where") is not None
    )


def test_flag_secret_value_allows_plain_non_secret_value():
    assert vt.flag_secret_value("timeout", "30", "where") is None


def test_find_hardcoded_keys_ignores_env_and_file_placeholders():
    config = {
        "provider": {
            "anthropic": {"options": {"apiKey": "{env:ANTHROPIC_API_KEY}"}},
            "openai": {"options": {"apiKey": "{file:./secrets/openai.key}"}},
        }
    }
    assert vt.find_hardcoded_keys(config) == []


def test_validate_config_allows_env_and_file_secret_placeholders(tmp_path):
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": 2, "todo": True},
            "provider": {
                "anthropic": {"options": {"apiKey": "{env:ANTHROPIC_API_KEY}"}},
                "openai": {"options": {"apiKey": "{file:./secrets/openai.key}"}},
            },
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert errors == []


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


def test_duplicate_top_level_key_rejected():
    with pytest.raises(vt.FrontmatterError, match="duplicate key"):
        vt.parse_map(["description: a", "description: b"], 0, 0)


def test_duplicate_nested_key_rejected():
    with pytest.raises(vt.FrontmatterError, match="duplicate key"):
        vt.parse_map(["permission:", "  task: deny", "  task: allow"], 0, 0)


def test_duplicate_key_error_names_the_key():
    with pytest.raises(vt.FrontmatterError, match="'webfetch'"):
        vt.parse_map(["webfetch: allow", "webfetch: deny"], 0, 0)


def test_non_duplicate_keys_still_parse_fine():
    data, idx = vt.parse_map(["a: 1", "b: 2"], 0, 0)
    assert data == {"a": "1", "b": "2"}
    assert idx == 2


def test_extract_frontmatter_rejects_duplicate_key_end_to_end(tmp_path):
    path = tmp_path / "agent.md"
    path.write_text(
        "---\ndescription: a\ndescription: b\nmode: subagent\n---\n",
        encoding="utf-8",
    )
    with pytest.raises(vt.FrontmatterError, match="duplicate key"):
        vt.extract_frontmatter(path)


def test_inline_flow_style_map_parses_as_string_not_dict():
    """Pins the behavior documented in parse_map()'s docstring: a
    flow-style map like 'task: {"*": allow}' is NOT parsed as a nested
    mapping — anything after 'key:' on the same line is a scalar, so it
    silently becomes a string. permission.task MUST use the nested block
    form, which is exactly why real agent frontmatter never uses '{...}'
    inline maps."""
    data, idx = vt.parse_map(['task: {"*": allow}'], 0, 0)
    assert data == {"task": '{"*": allow}'}
    assert isinstance(data["task"], str)
    assert idx == 1


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


def test_task_deny_rejects_leaked_mule_key():
    """A mule with '*-mule': allow alongside '*': deny must FAIL — the
    extra key would let a structural leaf spawn mules."""
    errors = []
    vt.check_task_deny(
        {"permission": {"task": {"*": "deny", "*-mule": "allow"}}},
        "worker-mule",
        "w",
        errors,
    )
    assert len(errors) == 1
    errors = []
    vt.check_task_deny(
        {"permission": {"task": {"*": "deny", "*-mule": "allow"}}},
        "observer",
        "w",
        errors,
    )
    assert len(errors) == 1


def test_hidden_rules():
    errors = []
    vt.check_hidden({}, "worker-mule", "w", errors)  # mule must be hidden
    assert len(errors) == 1
    errors = []
    vt.check_hidden({"hidden": "true"}, "worker", "w", errors)  # non-mule must not
    assert len(errors) == 1
    errors = []
    vt.check_hidden({}, "observer", "w", errors)  # observer must be hidden
    assert len(errors) == 1
    errors = []
    vt.check_hidden({"hidden": "true"}, "observer", "w", errors)
    assert errors == []


def test_observer_claude_must_be_hidden():
    errors = []
    vt.check_hidden({}, "observer-claude", "w", errors)
    assert len(errors) == 1
    errors = []
    vt.check_hidden({"hidden": "true"}, "observer-claude", "w", errors)
    assert errors == []


def test_policy_constants():
    """hidden covers mules + observers; counts match the template."""
    assert vt.HIDDEN_EXTRA == {"observer", "observer-claude"}
    assert vt.TASK_DENY_EXTRA == {"observer", "observer-claude"}
    assert vt.EXPECTED_PRIMARY_FILES == 1
    assert vt.EXPECTED_SUBAGENT_FILES == 45  # matches agents/ (45 .md files)
    assert vt.V2_MARKER_KEYS == ("permissions", "request", "system", "disabled")
    assert vt.WEB_TOOL_KEYS == ("webfetch", "websearch", "playwright_*")
    assert vt.OBSERVER_NAMES == {"observer", "observer-claude"}
    # Order is load-bearing: "*" (deny) must come before "*-mule" (allow).
    assert vt.ROLE_TASK_KEYS == ["*", "*-mule"]


def test_observer_claude_must_deny_task():
    errors = []
    vt.check_task_deny(
        {"permission": {"task": {"*": "allow"}}}, "observer-claude", "w", errors
    )
    assert len(errors) == 1


def test_observer_claude_model_enforced():
    errors = []
    vt.check_model(
        {"model": "google/gemini-4-hydrogen"}, "observer-claude", "w", errors
    )
    assert len(errors) == 1
    errors = []
    vt.check_model(
        {"model": "anthropic/claude-sonnet-5-5"}, "observer-claude", "w", errors
    )
    assert errors == []


def test_gemini_agents_model_enforced():
    for name in ("gemini-worker", "gemini-mule", "observer"):
        errors = []
        vt.check_model({"model": "deepseek/deepseek-flash"}, name, "w", errors)
        assert len(errors) == 1
        errors = []
        vt.check_model({"model": "google/gemini-4-hydrogen"}, name, "w", errors)
        assert errors == []


def test_supervisor_model_enforced():
    errors = []
    vt.check_model({"model": "anthropic/claude-opus-5-5"}, "supervisor", "w", errors)
    assert len(errors) == 1
    errors = []
    vt.check_model({"model": "deepseek/deepseek-flash"}, "supervisor", "w", errors)
    assert errors == []


# ---------------------------------------------------------------------------
# Unit tests: check_model identity-keyed EXPECTED_MODEL_BY_NAME map.
#
# Before this map existed, check_model() fell back to a provider-prefix
# check keyed on the *given* (possibly wrong) model string, so these 13
# names had NO real enforcement: a wrong model that didn't happen to
# start with 'xai/' silently passed.
# ---------------------------------------------------------------------------

GENERIC_DEEPSEEK_MULES = [
    "worker-mule",
    "architect-mule",
    "researcher-mule",
    "debugger-mule",
    "reviewer-mule",
    "security-mule",
    "planner-mule",
    "editor-mule",
    "quote-auditor-mule",
]

GROK_IDENTITY_AGENTS = ["designer", "designer-mule", "grok-worker", "grok-mule"]

PREVIOUSLY_UNENFORCED_AGENTS = GENERIC_DEEPSEEK_MULES + GROK_IDENTITY_AGENTS


def test_generic_deepseek_mules_reject_wrong_model():
    for name in GENERIC_DEEPSEEK_MULES:
        errors = []
        vt.check_model({"model": "xai/grok-4.7"}, name, "w", errors)
        assert len(errors) == 1, name


def test_generic_deepseek_mules_accept_correct_model():
    for name in GENERIC_DEEPSEEK_MULES:
        errors = []
        vt.check_model({"model": "deepseek/deepseek-flash"}, name, "w", errors)
        assert errors == [], name


def test_grok_identity_agents_reject_wrong_model():
    for name in GROK_IDENTITY_AGENTS:
        errors = []
        vt.check_model({"model": "deepseek/deepseek-flash"}, name, "w", errors)
        assert len(errors) == 1, name


def test_grok_identity_agents_accept_correct_model():
    for name in GROK_IDENTITY_AGENTS:
        errors = []
        vt.check_model({"model": "xai/grok-4.7"}, name, "w", errors)
        assert errors == [], name


def test_check_model_unknown_agent_errors_in_repo_mode():
    errors = []
    vt.check_model({"model": "deepseek/deepseek-flash"}, "my-custom-agent", "w", errors)
    assert len(errors) == 1
    assert "not a recognized template agent" in errors[0]


def test_check_model_unknown_agent_skipped_in_installed_mode():
    errors = []
    vt.check_model(
        {"model": "deepseek/deepseek-flash"},
        "my-custom-agent",
        "w",
        errors,
        installed=True,
    )
    assert errors == []


def test_check_model_still_flags_missing_model_for_unknown_agent():
    """installed=True skips the identity-map check, but an unknown agent
    with no model at all must still fail the basic 'model is present'
    check — installed mode is lenient about *which* model, not about
    having one."""
    errors = []
    vt.check_model({}, "my-custom-agent", "w", errors, installed=True)
    assert len(errors) == 1
    assert "missing or empty 'model'" in errors[0]


def test_expected_model_by_name_covers_every_template_agent():
    assert len(vt.EXPECTED_MODEL_BY_NAME) == 46
    assert len(vt.EXPECTED_SUBAGENT_NAMES) == 45
    assert vt.PRIMARY_AGENT_NAME not in vt.EXPECTED_SUBAGENT_NAMES
    for name in PREVIOUSLY_UNENFORCED_AGENTS:
        assert name in vt.EXPECTED_MODEL_BY_NAME, name


def test_real_previously_unenforced_agents_pass():
    """Regression guard: the 13 real template files that used to have no
    real model enforcement must still validate cleanly now that they do."""
    base = Path(__file__).resolve().parent.parent / "agents"
    for name in PREVIOUSLY_UNENFORCED_AGENTS:
        path = base / f"{name}.md"
        errors: list = []
        vt.validate_agent(name, f"agents/{name}.md", path, errors)
        assert errors == [], (name, errors)


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
        "  edit: allow\n"
        "  bash: allow\n"
        "  webfetch: allow\n"
        "  websearch: allow\n"
        "  playwright_*: allow\n"
        "---\n",
        encoding="utf-8",
    )
    errors = []
    vt.validate_agent("worker-mule", "agents/worker-mule.md", path, errors)
    assert len(errors) == 1
    assert "must not declare 'steps'" in errors[0]


# ---------------------------------------------------------------------------
# Unit tests: is_role_agent / is_observer predicates
# ---------------------------------------------------------------------------


def test_is_role_agent_true_for_role_names():
    for name in (
        "worker",
        "architect",
        "quote-auditor",
        "junior-worker",
        "senior-security",
        "designer",
        "grok-worker",
        "gemini-worker",
    ):
        assert vt.is_role_agent(name), name


def test_is_role_agent_false_for_mules_observers_and_supervisor():
    for name in (
        "worker-mule",
        "claude-mule",
        "observer",
        "observer-claude",
        "supervisor",
    ):
        assert not vt.is_role_agent(name), name


def test_is_observer_only_matches_observer_names():
    assert vt.is_observer("observer")
    assert vt.is_observer("observer-claude")
    assert not vt.is_observer("worker")
    assert not vt.is_observer("worker-mule")


# ---------------------------------------------------------------------------
# Unit tests: check_no_v2_markers (V1 'permission' block silently dropped
# by OpenCode V2 when a conflicting sibling key is present)
# ---------------------------------------------------------------------------


def test_no_v2_markers_rejects_each_conflicting_key():
    for key in ("permissions", "request", "system", "disabled"):
        errors = []
        vt.check_no_v2_markers({"description": "x", key: "y"}, "w", errors)
        assert len(errors) == 1, key


def test_no_v2_markers_passes_clean_frontmatter():
    errors = []
    vt.check_no_v2_markers(
        {"description": "x", "permission": {"task": "deny"}}, "w", errors
    )
    assert errors == []


def test_no_v2_markers_reports_multiple_keys_in_one_error():
    errors = []
    vt.check_no_v2_markers({"system": "x", "disabled": "true"}, "w", errors)
    assert len(errors) == 1
    assert "disabled" in errors[0] and "system" in errors[0]


# ---------------------------------------------------------------------------
# Unit tests: check_role_task_permission (role agents: task = {"*": deny,
# "*-mule": allow} with "*" BEFORE "*-mule" — order is load-bearing)
# ---------------------------------------------------------------------------


def test_role_task_permission_accepts_correct_order():
    errors = []
    vt.check_role_task_permission(
        {"permission": {"task": {"*": "deny", "*-mule": "allow"}}},
        "worker",
        "w",
        errors,
    )
    assert errors == []


def test_role_task_permission_rejects_reversed_order():
    """Reversed key order silently removes mule spawning under OpenCode's
    last-match-wins glob semantics — must be rejected even though the
    key/value *set* is identical to the accepted form."""
    errors = []
    vt.check_role_task_permission(
        {"permission": {"task": {"*-mule": "allow", "*": "deny"}}},
        "worker",
        "w",
        errors,
    )
    assert len(errors) == 1
    assert "order" in errors[0]


def test_role_task_permission_rejects_single_key_allow():
    errors = []
    vt.check_role_task_permission(
        {"permission": {"task": {"*": "allow"}}}, "worker", "w", errors
    )
    assert len(errors) == 1


def test_role_task_permission_rejects_extra_key():
    errors = []
    vt.check_role_task_permission(
        {"permission": {"task": {"*": "deny", "*-mule": "allow", "foo": "bar"}}},
        "worker",
        "w",
        errors,
    )
    assert len(errors) == 1


def test_role_task_permission_rejects_wrong_values_in_right_order():
    errors = []
    vt.check_role_task_permission(
        {"permission": {"task": {"*": "allow", "*-mule": "deny"}}},
        "worker",
        "w",
        errors,
    )
    assert len(errors) == 1


def test_role_task_permission_rejects_missing_permission():
    errors = []
    vt.check_role_task_permission({}, "worker", "w", errors)
    assert len(errors) == 1


def test_role_task_permission_ignores_mules_observers_and_supervisor():
    for name in ("worker-mule", "observer", "observer-claude", "supervisor"):
        errors = []
        vt.check_role_task_permission({}, name, "w", errors)
        assert errors == [], name


# ---------------------------------------------------------------------------
# Unit tests: check_web_tools_allowed (role agents + mules must grant
# webfetch/websearch/playwright_*; observers/supervisor are exempt)
# ---------------------------------------------------------------------------


def test_web_tools_allowed_rejects_missing_grant():
    errors = []
    vt.check_web_tools_allowed(
        {"permission": {"webfetch": "allow", "websearch": "allow"}},
        "worker",
        "w",
        errors,
    )
    assert len(errors) == 1
    assert "playwright_*" in errors[0]


def test_web_tools_allowed_rejects_missing_permission_block():
    errors = []
    vt.check_web_tools_allowed({}, "worker-mule", "w", errors)
    assert len(errors) == 1


def test_web_tools_allowed_passes_full_grant():
    full_perm = {
        "permission": {
            "webfetch": "allow",
            "websearch": "allow",
            "playwright_*": "allow",
        }
    }
    for name in ("worker", "worker-mule", "designer", "grok-mule"):
        errors = []
        vt.check_web_tools_allowed(full_perm, name, "w", errors)
        assert errors == [], name


def test_web_tools_allowed_ignores_observers_and_supervisor():
    for name in ("observer", "observer-claude", "supervisor"):
        errors = []
        vt.check_web_tools_allowed({}, name, "w", errors)
        assert errors == [], name


# ---------------------------------------------------------------------------
# Unit tests: check_edit_bash_not_denied (role agents + mules must not
# deny edit/bash; observers are exempt and must stay denied)
# ---------------------------------------------------------------------------


def test_edit_bash_not_denied_rejects_deny():
    errors = []
    vt.check_edit_bash_not_denied(
        {"permission": {"edit": "deny", "bash": "allow"}}, "worker", "w", errors
    )
    assert len(errors) == 1
    assert "edit" in errors[0]


def test_edit_bash_not_denied_rejects_both_denied():
    errors = []
    vt.check_edit_bash_not_denied(
        {"permission": {"edit": "deny", "bash": "deny"}}, "worker-mule", "w", errors
    )
    assert len(errors) == 1
    assert "edit" in errors[0] and "bash" in errors[0]


def test_edit_bash_not_denied_passes_allow():
    errors = []
    vt.check_edit_bash_not_denied(
        {"permission": {"edit": "allow", "bash": "allow"}}, "worker-mule", "w", errors
    )
    assert errors == []


def test_edit_bash_not_denied_exempts_observers_and_supervisor():
    """check_edit_bash_not_denied applies only to role agents/mules — it
    must not fire for observers or supervisor either way (their edit/bash
    requirements are enforced elsewhere: check_observer_edit_bash_denied
    and check_supervisor_no_permission respectively)."""
    for name in ("observer", "observer-claude", "supervisor"):
        errors = []
        vt.check_edit_bash_not_denied(
            {"permission": {"edit": "deny", "bash": "deny"}}, name, "w", errors
        )
        assert errors == [], name
        errors = []
        vt.check_edit_bash_not_denied(
            {"permission": {"edit": "allow", "bash": "allow"}}, name, "w", errors
        )
        assert errors == [], name


# ---------------------------------------------------------------------------
# Unit tests: check_observer_edit_bash_denied (the enforcement side of the
# exemption above — observers must stay denied, not just be allowed to)
# ---------------------------------------------------------------------------


def test_observer_edit_bash_denied_passes_when_denied():
    errors = []
    vt.check_observer_edit_bash_denied(
        {"permission": {"edit": "deny", "bash": "deny"}}, "observer", "w", errors
    )
    assert errors == []
    errors = []
    vt.check_observer_edit_bash_denied(
        {"permission": {"edit": "deny", "bash": "deny"}},
        "observer-claude",
        "w",
        errors,
    )
    assert errors == []


def test_observer_edit_bash_denied_rejects_not_denied():
    """Observers are exempt from check_edit_bash_not_denied, but the spec
    says they 'must stay denied' — that direction must be enforced too,
    not just assumed from the template's current file contents."""
    errors = []
    vt.check_observer_edit_bash_denied(
        {"permission": {"edit": "allow", "bash": "allow"}}, "observer", "w", errors
    )
    assert len(errors) == 1
    assert "edit" in errors[0] and "bash" in errors[0]
    errors = []
    vt.check_observer_edit_bash_denied({}, "observer-claude", "w", errors)
    assert len(errors) == 1


def test_observer_edit_bash_denied_ignores_role_agents_mules_and_supervisor():
    for name in ("worker", "worker-mule", "supervisor"):
        errors = []
        vt.check_observer_edit_bash_denied(
            {"permission": {"edit": "allow", "bash": "allow"}}, name, "w", errors
        )
        assert errors == [], name


# ---------------------------------------------------------------------------
# Unit tests: check_supervisor_no_permission (supervisor must not declare
# a 'permission' frontmatter block at all)
# ---------------------------------------------------------------------------


def test_supervisor_no_permission_passes_without_block():
    errors = []
    vt.check_supervisor_no_permission({"mode": "primary"}, "supervisor", "w", errors)
    assert errors == []


def test_supervisor_no_permission_rejects_presence():
    errors = []
    vt.check_supervisor_no_permission(
        {"mode": "primary", "permission": {"edit": "allow"}},
        "supervisor",
        "w",
        errors,
    )
    assert len(errors) == 1


def test_supervisor_no_permission_ignores_other_agents():
    errors = []
    vt.check_supervisor_no_permission(
        {"permission": {"edit": "allow"}}, "worker", "w", errors
    )
    assert errors == []


# ---------------------------------------------------------------------------
# Unit tests: check_grok_variant (no Grok model exposes a 'max' variant;
# this only catches the frontmatter combination — the real failure
# happens at spawn time, which static validation cannot observe)
# ---------------------------------------------------------------------------


def test_grok_variant_max_rejected():
    errors = []
    vt.check_grok_variant({"model": "xai/grok-4.7", "variant": "max"}, "w", errors)
    assert len(errors) == 1


def test_grok_variant_non_max_passes():
    errors = []
    vt.check_grok_variant({"model": "xai/grok-4.7", "variant": "fast"}, "w", errors)
    assert errors == []
    errors = []
    vt.check_grok_variant({"model": "xai/grok-4.7"}, "w", errors)
    assert errors == []


def test_grok_variant_max_ignored_for_non_grok_models():
    errors = []
    vt.check_grok_variant(
        {"model": "anthropic/claude-sonnet-5-5", "variant": "max"}, "w", errors
    )
    assert errors == []
    errors = []
    vt.check_grok_variant(
        {"model": "deepseek/deepseek-flash", "variant": "max"}, "w", errors
    )
    assert errors == []


# ---------------------------------------------------------------------------
# End-to-end tests via validate_agent for the new policy checks
# ---------------------------------------------------------------------------


def _write_agent(tmp_path, filename, frontmatter_lines):
    path = tmp_path / filename
    path.write_text(
        "---\n" + "\n".join(frontmatter_lines) + "\n---\n", encoding="utf-8"
    )
    return path


def test_validate_agent_accepts_fully_compliant_role_agent(tmp_path):
    path = _write_agent(
        tmp_path,
        "worker.md",
        [
            "description: General-purpose worker.",
            "mode: subagent",
            "model: anthropic/claude-sonnet-5-5",
            "permission:",
            "  task:",
            '    "*": deny',
            '    "*-mule": allow',
            "  edit: allow",
            "  bash: allow",
            "  webfetch: allow",
            "  websearch: allow",
            "  playwright_*: allow",
        ],
    )
    errors = []
    vt.validate_agent("worker", "agents/worker.md", path, errors)
    assert errors == []


def test_validate_agent_flags_reversed_role_task_order_end_to_end(tmp_path):
    path = _write_agent(
        tmp_path,
        "worker.md",
        [
            "description: General-purpose worker.",
            "mode: subagent",
            "model: anthropic/claude-sonnet-5-5",
            "permission:",
            "  task:",
            '    "*-mule": allow',
            '    "*": deny',
            "  edit: allow",
            "  bash: allow",
            "  webfetch: allow",
            "  websearch: allow",
            "  playwright_*: allow",
        ],
    )
    errors = []
    vt.validate_agent("worker", "agents/worker.md", path, errors)
    assert len(errors) == 1
    assert "order" in errors[0]


def test_validate_agent_flags_leaky_mule_end_to_end(tmp_path):
    path = _write_agent(
        tmp_path,
        "worker-mule.md",
        [
            "description: Leaf agent.",
            "mode: subagent",
            "hidden: true",
            "model: deepseek/deepseek-flash",
            "permission:",
            "  task:",
            '    "*": deny',
            '    "*-mule": allow',
            "  edit: allow",
            "  bash: allow",
            "  webfetch: allow",
            "  websearch: allow",
            "  playwright_*: allow",
        ],
    )
    errors = []
    vt.validate_agent("worker-mule", "agents/worker-mule.md", path, errors)
    assert len(errors) == 1
    assert "deny ALL task spawning" in errors[0]


def test_validate_agent_flags_v2_marker_end_to_end(tmp_path):
    path = _write_agent(
        tmp_path,
        "worker-mule.md",
        [
            "description: Leaf agent.",
            "mode: subagent",
            "hidden: true",
            "model: deepseek/deepseek-flash",
            "disabled: true",
            "permission:",
            "  task: deny",
            "  edit: allow",
            "  bash: allow",
            "  webfetch: allow",
            "  websearch: allow",
            "  playwright_*: allow",
        ],
    )
    errors = []
    vt.validate_agent("worker-mule", "agents/worker-mule.md", path, errors)
    assert len(errors) == 1
    assert "disabled" in errors[0]


def test_validate_agent_flags_supervisor_permission_block_end_to_end(tmp_path):
    path = _write_agent(
        tmp_path,
        "supervisor.md",
        [
            "description: Senior supervisor.",
            "mode: primary",
            "model: deepseek/deepseek-flash",
            "permission:",
            "  edit: allow",
        ],
    )
    errors = []
    vt.validate_agent("supervisor", "agent/supervisor.md", path, errors)
    assert len(errors) == 1
    assert "must NOT have a 'permission'" in errors[0]


def test_validate_agent_flags_grok_variant_max_end_to_end(tmp_path):
    path = _write_agent(
        tmp_path,
        "designer.md",
        [
            "description: Design subagent.",
            "mode: subagent",
            "model: xai/grok-4.7",
            "variant: max",
            "permission:",
            "  task:",
            '    "*": deny',
            '    "*-mule": allow',
            "  edit: allow",
            "  bash: allow",
            "  webfetch: allow",
            "  websearch: allow",
            "  playwright_*: allow",
        ],
    )
    errors = []
    vt.validate_agent("designer", "agents/designer.md", path, errors)
    assert len(errors) == 1
    assert "variant: max" in errors[0]


# ---------------------------------------------------------------------------
# Unit tests: opencode.json / opencode.template.json config validation
# (V2: experimental.subagent_depth >= 2, experimental.todo: true, no stale
# top-level subagent_depth)
# ---------------------------------------------------------------------------


def write_config(tmp_path, data):
    path = tmp_path / "opencode.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_validate_config_accepts_v2_depth_and_todo(tmp_path):
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": 2, "todo": True},
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert errors == []


def test_validate_config_accepts_deeper_than_minimum(tmp_path):
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": 5, "todo": True},
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert errors == []


def test_validate_config_rejects_stale_top_level_subagent_depth(tmp_path):
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "subagent_depth": 2,
            "experimental": {"subagent_depth": 2, "todo": True},
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert len(errors) == 1
    assert "top-level 'subagent_depth'" in errors[0]


def test_validate_config_rejects_low_experimental_depth(tmp_path):
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": 1, "todo": True},
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert len(errors) == 1
    assert "experimental.subagent_depth" in errors[0]


def test_validate_config_rejects_missing_experimental(tmp_path):
    path = write_config(tmp_path, {"default_agent": "supervisor"})
    errors: list = []
    vt.validate_config(path, errors)
    messages = " ".join(errors)
    assert "experimental.subagent_depth" in messages
    assert "experimental.todo" in messages


def test_validate_config_rejects_todo_false(tmp_path):
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": 2, "todo": False},
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert len(errors) == 1
    assert "experimental.todo" in errors[0]


def test_validate_config_rejects_bool_as_depth(tmp_path):
    """JSON ``true``/``false`` parse to Python ``bool``, an ``int`` subclass —
    must not be accepted as a valid depth value."""
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": True, "todo": True},
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert len(errors) == 1
    assert "experimental.subagent_depth" in errors[0]


def test_validate_config_reports_both_depth_and_todo_problems(tmp_path):
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": 1, "todo": False},
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert len(errors) == 2


def test_real_template_config_passes():
    path = Path(__file__).resolve().parent.parent / "opencode.template.json"
    errors: list = []
    vt.validate_config(path, errors)
    assert errors == []


# ---------------------------------------------------------------------------
# Smoke test against the real template
# ---------------------------------------------------------------------------


def test_real_worker_agent_passes():
    path = Path(__file__).resolve().parent.parent / "agents" / "worker.md"
    fm = vt.extract_frontmatter(path)
    assert fm["mode"] == "subagent"
    assert fm["model"] == "anthropic/claude-sonnet-5-5"
    assert "steps" not in fm  # step caps are no longer used
    errors = []
    vt.validate_agent("worker", "agents/worker.md", path, errors)
    assert errors == []


def test_real_claude_mule_passes():
    path = Path(__file__).resolve().parent.parent / "agents" / "claude-mule.md"
    fm = vt.extract_frontmatter(path)
    assert fm["model"] == "anthropic/claude-sonnet-5-5"
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
    assert fm["model"] == "anthropic/claude-sonnet-5-5"
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
    assert fm["model"] == "google/gemini-4-hydrogen"
    errors = []
    vt.validate_agent("observer", "agents/observer.md", path, errors)
    assert errors == []


def test_real_gemini_agents_pass():
    base = Path(__file__).resolve().parent.parent / "agents"
    for name in ("gemini-worker", "gemini-mule"):
        path = base / f"{name}.md"
        fm = vt.extract_frontmatter(path)
        assert fm["model"] == "google/gemini-4-hydrogen"
        errors = []
        vt.validate_agent(name, f"agents/{name}.md", path, errors)
        assert errors == []


# ---------------------------------------------------------------------------
# Unit tests: validate_plugin (OpenCode V2 observer-bridge plugin layout)
# ---------------------------------------------------------------------------


def test_validate_plugin_passes_on_real_repo():
    root = Path(__file__).resolve().parent.parent
    errors: list = []
    vt.validate_plugin(root, errors)
    assert errors == []


def test_validate_plugin_flags_missing_entry_point(tmp_path):
    errors: list = []
    vt.validate_plugin(tmp_path, errors)
    assert len(errors) == 1
    assert "plugins/observer-bridge/index.js" in errors[0]


def test_validate_plugin_flags_missing_plugin_define(tmp_path):
    plugin_dir = tmp_path / "plugins" / "observer-bridge"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "index.js").write_text("export default {}\n", encoding="utf-8")
    errors: list = []
    vt.validate_plugin(tmp_path, errors)
    assert len(errors) == 1
    assert "Plugin.define" in errors[0]


def test_validate_plugin_accepts_plugin_define(tmp_path):
    plugin_dir = tmp_path / "plugins" / "observer-bridge"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "index.js").write_text(
        'import { Plugin } from "@opencode/plugin"\n'
        'export default Plugin.define({ id: "observer-bridge" })\n',
        encoding="utf-8",
    )
    errors: list = []
    vt.validate_plugin(tmp_path, errors)
    assert errors == []


def test_validate_plugin_flags_v1_leftover_dir(tmp_path):
    plugin_dir = tmp_path / "plugins" / "observer-bridge"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "index.js").write_text("Plugin.define({})", encoding="utf-8")
    v1_dir = tmp_path / "plugin"
    v1_dir.mkdir()
    (v1_dir / "observer-bridge.js").write_text("stale", encoding="utf-8")
    errors: list = []
    vt.validate_plugin(tmp_path, errors)
    assert len(errors) == 1
    assert "V1 'plugin/' directory" in errors[0]


def test_validate_plugin_ignores_v1_dir_without_js_files(tmp_path):
    plugin_dir = tmp_path / "plugins" / "observer-bridge"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "index.js").write_text("Plugin.define({})", encoding="utf-8")
    v1_dir = tmp_path / "plugin"
    v1_dir.mkdir()
    (v1_dir / "README.md").write_text("notes", encoding="utf-8")
    errors: list = []
    vt.validate_plugin(tmp_path, errors)
    assert errors == []


def test_validate_config_rejects_stale_observer_bridge_plugin_entry(tmp_path):
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": 2, "todo": True},
            "plugin": ["observer-bridge.js"],
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert len(errors) == 1
    assert "top-level 'plugin'" in errors[0]
    assert "observer-bridge.js" in errors[0]
    assert "V1" in errors[0]


def test_validate_config_rejects_stale_entry_among_other_plugin_entries(tmp_path):
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": 2, "todo": True},
            "plugin": ["opencode-wakelock", "observer-bridge.js"],
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert len(errors) == 1
    assert "observer-bridge.js" in errors[0]


def test_validate_config_rejects_bare_string_stale_plugin(tmp_path):
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": 2, "todo": True},
            "plugin": "observer-bridge.js",
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert len(errors) == 1
    assert "observer-bridge.js" in errors[0]


def test_validate_config_accepts_plugin_key_with_other_entries(tmp_path):
    """A 'plugin' array WITHOUT the stale entry must not error — the V1 key
    itself is deprecated, not harmful; only the known-bad entry is flagged."""
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": 2, "todo": True},
            "plugin": ["opencode-wakelock", "opencode-pty"],
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert errors == []


def test_validate_config_accepts_bare_string_other_plugin(tmp_path):
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": 2, "todo": True},
            "plugin": "opencode-wakelock",
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert errors == []


def test_validate_config_accepts_config_with_no_plugin_key(tmp_path):
    path = write_config(
        tmp_path,
        {
            "default_agent": "supervisor",
            "experimental": {"subagent_depth": 2, "todo": True},
        },
    )
    errors: list = []
    vt.validate_config(path, errors)
    assert errors == []


def test_real_repo_has_no_v1_plugin_directory():
    root = Path(__file__).resolve().parent.parent
    assert not (root / "plugin").exists(), (
        "V1 'plugin/' directory should have been deleted in favor of "
        "'plugins/observer-bridge/'"
    )


# ---------------------------------------------------------------------------
# Unit tests: validate_structure — repo (template) mode stays strict at
# exactly 45 subagent files; --installed mode replaces that exact-count
# check with "all 45 template agents present, extras allowed (info, not
# error)" so a user's own extra agent files don't fail validation.
# ---------------------------------------------------------------------------


def _make_agent_tree(tmp_path, agent_names):
    (tmp_path / "agent").mkdir()
    (tmp_path / "agent" / "supervisor.md").write_text("x", encoding="utf-8")
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    for name in agent_names:
        (agents_dir / f"{name}.md").write_text("x", encoding="utf-8")
    return tmp_path


def test_validate_structure_repo_mode_passes_with_exact_45(tmp_path):
    root = _make_agent_tree(tmp_path, vt.EXPECTED_SUBAGENT_NAMES)
    errors: list = []
    infos: list = []
    vt.validate_structure(root, errors, infos, installed=False)
    assert errors == []
    assert infos == []


def test_validate_structure_repo_mode_rejects_count_other_than_45(tmp_path):
    short = sorted(vt.EXPECTED_SUBAGENT_NAMES)[:-1]  # 44 names
    root = _make_agent_tree(tmp_path, short)
    errors: list = []
    infos: list = []
    vt.validate_structure(root, errors, infos, installed=False)
    assert len(errors) == 1
    assert "exactly 45" in errors[0]
    assert infos == []  # repo mode never emits infos


def test_validate_structure_repo_mode_strict_even_with_extra_agent(tmp_path):
    """Template (repo) mode must stay strict: an extra user-added agent
    file is still a hard count error, unlike --installed mode."""
    names = list(vt.EXPECTED_SUBAGENT_NAMES) + ["my-custom-agent"]
    root = _make_agent_tree(tmp_path, names)
    errors: list = []
    infos: list = []
    vt.validate_structure(root, errors, infos, installed=False)
    assert len(errors) == 1
    assert "exactly 45" in errors[0]
    assert infos == []


def test_validate_structure_installed_mode_passes_with_exact_45(tmp_path):
    root = _make_agent_tree(tmp_path, vt.EXPECTED_SUBAGENT_NAMES)
    errors: list = []
    infos: list = []
    vt.validate_structure(root, errors, infos, installed=True)
    assert errors == []
    assert infos == []


def test_validate_structure_installed_mode_allows_extra_agent_as_info(tmp_path):
    names = list(vt.EXPECTED_SUBAGENT_NAMES) + ["my-custom-agent"]
    root = _make_agent_tree(tmp_path, names)
    errors: list = []
    infos: list = []
    vt.validate_structure(root, errors, infos, installed=True)
    assert errors == []
    assert len(infos) == 1
    assert "my-custom-agent" in infos[0]


def test_validate_structure_installed_mode_allows_multiple_extra_agents(tmp_path):
    names = list(vt.EXPECTED_SUBAGENT_NAMES) + ["extra-one", "extra-two"]
    root = _make_agent_tree(tmp_path, names)
    errors: list = []
    infos: list = []
    vt.validate_structure(root, errors, infos, installed=True)
    assert errors == []
    assert len(infos) == 1
    assert "extra-one" in infos[0] and "extra-two" in infos[0]


def test_validate_structure_installed_mode_still_errors_on_missing_template_agent(
    tmp_path,
):
    """--installed tolerates extras but must still require every template
    agent to be present — it is not a free pass on missing files."""
    short = sorted(vt.EXPECTED_SUBAGENT_NAMES)[:-1]  # omit one real agent
    root = _make_agent_tree(tmp_path, short)
    errors: list = []
    infos: list = []
    vt.validate_structure(root, errors, infos, installed=True)
    assert len(errors) == 1
    assert "missing" in errors[0]
    assert infos == []


def test_validate_structure_installed_mode_reports_both_missing_and_extra(tmp_path):
    short = sorted(vt.EXPECTED_SUBAGENT_NAMES)[:-1] + ["my-custom-agent"]
    root = _make_agent_tree(tmp_path, short)
    errors: list = []
    infos: list = []
    vt.validate_structure(root, errors, infos, installed=True)
    assert len(errors) == 1
    assert "missing" in errors[0]
    assert len(infos) == 1
    assert "my-custom-agent" in infos[0]


def test_real_repo_validate_structure_passes_both_modes():
    root = Path(__file__).resolve().parent.parent
    errors, infos = [], []
    vt.validate_structure(root, errors, infos, installed=False)
    assert errors == []
    assert infos == []
    errors, infos = [], []
    vt.validate_structure(root, errors, infos, installed=True)
    assert errors == []
    assert infos == []  # the repo itself ships no extra agent files


# ---------------------------------------------------------------------------
# Unit tests: validate() / main() threading the 'installed' flag through to
# check_model and validate_structure end to end.
# ---------------------------------------------------------------------------


def test_validate_end_to_end_repo_mode_on_real_template():
    root = Path(__file__).resolve().parent.parent
    config_path = root / "opencode.template.json"
    errors, skills_present, infos = vt.validate(root, config_path, installed=False)
    assert errors == []
    assert infos == []
    assert skills_present is True


def test_validate_end_to_end_installed_mode_on_real_template():
    root = Path(__file__).resolve().parent.parent
    config_path = root / "opencode.template.json"
    errors, skills_present, infos = vt.validate(root, config_path, installed=True)
    assert errors == []
    assert infos == []
