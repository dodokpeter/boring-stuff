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


def test_copies_a_single_file_from_clipboard(tmp_path, monkeypatch, isolated_downloads):
    source = tmp_path / "notes.txt"
    source.write_text("original content", encoding="utf-8")
    monkeypatch.setattr(clipsave.ImageGrab, "grabclipboard", lambda: [str(source)])

    clipsave.main()

    copied = isolated_downloads / "2026-08-28 09-45-50 notes.txt"
    assert copied.read_text(encoding="utf-8") == "original content"
    assert source.exists()  # original is untouched, this is a copy


def test_zips_a_folder_from_clipboard(tmp_path, monkeypatch, isolated_downloads):
    folder = tmp_path / "project"
    folder.mkdir()
    (folder / "a.txt").write_text("a", encoding="utf-8")
    (folder / "b.txt").write_text("b", encoding="utf-8")
    monkeypatch.setattr(clipsave.ImageGrab, "grabclipboard", lambda: [str(folder)])

    clipsave.main()

    archive = isolated_downloads / "2026-08-28 09-45-50 project.zip"
    assert archive.exists()
    import zipfile
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
    assert "project/a.txt" in names
    assert "project/b.txt" in names


def test_copies_multiple_files_and_folders_from_clipboard(tmp_path, monkeypatch, isolated_downloads):
    file_source = tmp_path / "report.pdf"
    file_source.write_text("pdf-ish content", encoding="utf-8")
    folder_source = tmp_path / "photos"
    folder_source.mkdir()
    (folder_source / "pic.jpg").write_text("jpg-ish content", encoding="utf-8")
    monkeypatch.setattr(clipsave.ImageGrab, "grabclipboard", lambda: [str(file_source), str(folder_source)])

    clipsave.main()

    assert (isolated_downloads / "2026-08-28 09-45-50 report.pdf").exists()
    assert (isolated_downloads / "2026-08-28 09-45-50 photos.zip").exists()


def test_skips_missing_paths_and_falls_back_when_nothing_saved(monkeypatch, isolated_downloads):
    monkeypatch.setattr(clipsave.ImageGrab, "grabclipboard", lambda: ["C:\\does\\not\\exist.txt"])
    monkeypatch.setattr(clipsave, "get_clipboard_text", lambda: None)

    with pytest.raises(SystemExit):
        clipsave.main()

    assert list(isolated_downloads.iterdir()) == []
