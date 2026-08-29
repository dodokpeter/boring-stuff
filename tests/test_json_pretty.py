import pytest

from cases.devs import json_pretty


@pytest.fixture
def clipboard(monkeypatch):
    state = {"value": ""}
    monkeypatch.setattr(json_pretty.pyperclip, "paste", lambda: state["value"])
    monkeypatch.setattr(json_pretty.pyperclip, "copy", lambda text: state.__setitem__("value", text))
    return state


def test_pretty_prints_by_default(clipboard):
    clipboard["value"] = '{"b":2,"a":1}'

    json_pretty.main([])

    assert clipboard["value"] == '{\n  "b": 2,\n  "a": 1\n}'


def test_minify_flag_strips_whitespace(clipboard):
    clipboard["value"] = '{\n  "b": 2,\n  "a": 1\n}'

    json_pretty.main(["--minify"])

    assert clipboard["value"] == '{"b":2,"a":1}'


def test_rejects_invalid_json(clipboard):
    clipboard["value"] = "this is not json"

    with pytest.raises(SystemExit):
        json_pretty.main([])

    # clipboard is left untouched on failure
    assert clipboard["value"] == "this is not json"


def test_exits_on_empty_clipboard(clipboard):
    clipboard["value"] = ""

    with pytest.raises(SystemExit):
        json_pretty.main([])


def test_round_trips_pretty_then_minify(clipboard):
    clipboard["value"] = "[1, 2, 3]"

    json_pretty.main([])
    assert clipboard["value"] == "[\n  1,\n  2,\n  3\n]"

    json_pretty.main(["-m"])
    assert clipboard["value"] == "[1,2,3]"
