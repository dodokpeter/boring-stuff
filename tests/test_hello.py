import builtins

import pytest

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


def test_crashes_on_non_numeric_age_but_still_saves_config(tmp_path, monkeypatch):
    # Documents a known, separately-tracked bug (TODO.md): int(age) + 1 in the
    # final print is outside the try/except, so a non-numeric age is accepted
    # and saved, then crashes on the last line instead of the earlier
    # try/except catching it.
    monkeypatch.setattr(user_conf.Path, "home", lambda: tmp_path)
    answer_with(monkeypatch, "Ada", "Lovelace", "not-a-number")

    with pytest.raises(ValueError):
        hello.main()

    assert user_conf.load_config(None)["me"]["age"] == "not-a-number"
