import pytest

from cases.maps import mapit


@pytest.fixture
def clipboard(monkeypatch):
    state = {"value": ""}
    monkeypatch.setattr(mapit.pyperclip, "paste", lambda: state["value"])
    return state


def test_uses_argv_address_when_given(monkeypatch, clipboard):
    opened = []
    monkeypatch.setattr(mapit.webbrowser, "open", lambda url: opened.append(url))

    mapit.main(["Bratislava"])

    assert opened == ["https://www.google.com/maps/place/Bratislava"]


def test_falls_back_to_clipboard_when_no_args(monkeypatch, clipboard):
    opened = []
    monkeypatch.setattr(mapit.webbrowser, "open", lambda url: opened.append(url))
    clipboard["value"] = "Vienna"

    mapit.main([])

    assert opened == ["https://www.google.com/maps/place/Vienna"]


def test_prints_message_and_does_not_open_browser_when_clipboard_is_empty(monkeypatch, clipboard, capsys):
    opened = []
    monkeypatch.setattr(mapit.webbrowser, "open", lambda url: opened.append(url))
    clipboard["value"] = ""

    mapit.main([])

    assert opened == []
    out = capsys.readouterr().out
    assert "clipboard is empty" in out.lower()


def test_url_encodes_special_characters_in_address(monkeypatch, clipboard):
    opened = []
    monkeypatch.setattr(mapit.webbrowser, "open", lambda url: opened.append(url))

    mapit.main(["AT&T", "Building,", "5th", "&", "Main"])

    assert opened == ["https://www.google.com/maps/place/AT%26T%20Building%2C%205th%20%26%20Main"]
