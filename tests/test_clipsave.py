from datetime import datetime

import pytest
from PIL import Image

from wins import clipsave


@pytest.fixture(autouse=True)
def isolated_downloads(tmp_path, monkeypatch):
    monkeypatch.setattr(clipsave.Path, "home", lambda: tmp_path)
    return tmp_path / "Downloads"


@pytest.fixture(autouse=True)
def fixed_timestamp(monkeypatch):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 8, 28, 9, 45, 50)

    monkeypatch.setattr(clipsave, "datetime", FixedDateTime)


def test_saves_image_when_clipboard_has_a_picture(monkeypatch, isolated_downloads):
    image = Image.new("RGB", (10, 10), color="blue")
    monkeypatch.setattr(clipsave.ImageGrab, "grabclipboard", lambda: image)

    clipsave.main()

    saved = isolated_downloads / "2026-08-28 09-45-50.png"
    assert saved.exists()
    assert Image.open(saved).size == (10, 10)


def test_saves_text_when_clipboard_has_no_image(monkeypatch, isolated_downloads):
    monkeypatch.setattr(clipsave.ImageGrab, "grabclipboard", lambda: None)
    monkeypatch.setattr(clipsave, "get_clipboard_text", lambda: "hello from clipboard")

    clipsave.main()

    saved = isolated_downloads / "2026-08-28 09-45-50.txt"
    assert saved.read_text(encoding="utf-8") == "hello from clipboard"


def test_exits_nonzero_when_clipboard_is_empty(monkeypatch, isolated_downloads):
    monkeypatch.setattr(clipsave.ImageGrab, "grabclipboard", lambda: None)
    monkeypatch.setattr(clipsave, "get_clipboard_text", lambda: None)

    with pytest.raises(SystemExit) as exc_info:
        clipsave.main()

    assert exc_info.value.code != 0
    assert list(isolated_downloads.iterdir()) == []


def test_ignores_file_list_from_clipboard(monkeypatch, isolated_downloads):
    # grabclipboard() returns a list of paths when files (not pixel data)
    # are copied - that shouldn't be mistaken for an image.
    monkeypatch.setattr(clipsave.ImageGrab, "grabclipboard", lambda: ["C:\\some\\file.txt"])
    monkeypatch.setattr(clipsave, "get_clipboard_text", lambda: None)

    with pytest.raises(SystemExit):
        clipsave.main()
