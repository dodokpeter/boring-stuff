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
