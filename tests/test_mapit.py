import pytest

pytest.importorskip("tkinter")

from cases.maps import mapit


def test_uses_argv_address_when_given(monkeypatch):
    opened = []
    monkeypatch.setattr(mapit.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(mapit.sys, "argv", ["mapit", "Bratislava"])

    mapit.main()

    assert opened == ["https://www.google.com/maps/place/Bratislava"]


def test_falls_back_to_clipboard_when_no_args(monkeypatch):
    opened = []
    monkeypatch.setattr(mapit.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(mapit.sys, "argv", ["mapit"])

    class FakeRoot:
        def clipboard_get(self):
            return "Vienna"

    monkeypatch.setattr(mapit.tk, "Tk", lambda: FakeRoot())

    mapit.main()

    assert opened == ["https://www.google.com/maps/place/Vienna"]


def test_prints_message_and_does_not_open_browser_when_clipboard_is_empty(monkeypatch, capsys):
    opened = []
    monkeypatch.setattr(mapit.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(mapit.sys, "argv", ["mapit"])

    class FakeRoot:
        def clipboard_get(self):
            raise mapit.tk.TclError("CLIPBOARD selection doesn't exist")

    monkeypatch.setattr(mapit.tk, "Tk", lambda: FakeRoot())

    mapit.main()

    assert opened == []
    out = capsys.readouterr().out
    assert "clipboard is empty" in out.lower()


def test_url_encodes_special_characters_in_address(monkeypatch):
    opened = []
    monkeypatch.setattr(mapit.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(mapit.sys, "argv", ["mapit", "AT&T", "Building,", "5th", "&", "Main"])

    mapit.main()

    assert opened == ["https://www.google.com/maps/place/AT%26T%20Building%2C%205th%20%26%20Main"]
