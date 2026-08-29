import builtins

from core.configuration import user_conf
from scripts import hello


def answer_with(monkeypatch, *answers):
    values = iter(answers)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(values))


def test_creates_config_and_saves_answers(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(user_conf.Path, "home", lambda: tmp_path)
    answer_with(monkeypatch, "Ada", "Lovelace", "36")

    hello.main()

    config_path = tmp_path / ".boring-stuff" / "BoringStuff.yml"
    assert config_path.exists()
    assert user_conf.load_config(None)["me"] == {"name": "Ada", "surname": "Lovelace", "age": 36}

    out = capsys.readouterr().out
    assert "Nice to meet you, Ada" in out
    assert "Next year you will be 37" in out


def test_non_numeric_age_saves_as_string_without_crashing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(user_conf.Path, "home", lambda: tmp_path)
    answer_with(monkeypatch, "Ada", "Lovelace", "not-a-number")

    hello.main()

    assert user_conf.load_config(None)["me"]["age"] == "not-a-number"
    out = capsys.readouterr().out
    assert "Nice to meet you, Ada" in out
    assert "Next year" not in out


def test_output_is_safe_for_legacy_windows_console_codepage(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(user_conf.Path, "home", lambda: tmp_path)
    answer_with(monkeypatch, "Ada", "Lovelace", "36")

    hello.main()

    out = capsys.readouterr().out
    out.encode("cp1252")  # raises UnicodeEncodeError if an emoji sneaks back in
