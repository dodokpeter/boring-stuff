import builtins

from core.console.inputs import ask_string_value


def answer_with(monkeypatch, *answers):
    values = iter(answers)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(values))


def test_returns_typed_answer(monkeypatch):
    answer_with(monkeypatch, "typed")

    assert ask_string_value("Name", "default") == "typed"


def test_returns_default_on_empty_answer(monkeypatch):
    answer_with(monkeypatch, "")

    assert ask_string_value("Name", "default") == "default"


def test_prompt_includes_default_suffix_when_default_given(monkeypatch):
    prompts = []
    monkeypatch.setattr(builtins, "input", lambda prompt="": prompts.append(prompt) or "")

    ask_string_value("Name", "Bob")

    assert prompts == ["Name (default = Bob): "]


def test_prompt_omits_default_suffix_when_required(monkeypatch):
    prompts = []
    monkeypatch.setattr(builtins, "input", lambda prompt="": prompts.append(prompt) or "typed")

    ask_string_value("Directory", None)

    assert prompts == ["Directory: "]


def test_reasks_until_non_empty_when_required(monkeypatch):
    answer_with(monkeypatch, "", "", "final")

    assert ask_string_value("Directory", None) == "final"
