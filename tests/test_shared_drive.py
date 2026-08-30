import pytest

from cases.wins import shared_drive


def test_prompts_and_persists_directory_when_not_configured(tmp_path, monkeypatch, capsys):
    root = tmp_path / "SharedDrive"
    root.mkdir()

    calls = []

    def fake_load_config_value(config_name, message, default, *keys, validate=None):
        calls.append((config_name, message, default, keys))
        if validate is not None:
            validate(str(root))
        return str(root)

    monkeypatch.setattr(shared_drive, "load_config_value", fake_load_config_value)

    shared_drive.main()

    expected_message = "Shared Drive root folder (e.g. your Google Drive mount path)"
    assert calls == [(None, expected_message, None, ("drive", "directory", "boring-stuff"))]

    target = root / "boring-stuff"
    assert target.is_dir()

    out = capsys.readouterr().out
    assert f"Created folder: {target}" in out


def test_creates_boring_stuff_folder_when_missing(tmp_path, monkeypatch, capsys):
    root = tmp_path / "SharedDrive"
    root.mkdir()
    monkeypatch.setattr(shared_drive, "load_config_value", lambda *args, **kwargs: str(root))

    shared_drive.main()

    target = root / "boring-stuff"
    assert target.is_dir()
    assert f"Created folder: {target}" in capsys.readouterr().out


def test_leaves_existing_boring_stuff_folder_alone(tmp_path, monkeypatch, capsys):
    root = tmp_path / "SharedDrive"
    root.mkdir()
    target = root / "boring-stuff"
    target.mkdir()
    (target / "keep.txt").write_text("do not touch", encoding="utf-8")
    monkeypatch.setattr(shared_drive, "load_config_value", lambda *args, **kwargs: str(root))

    shared_drive.main()

    assert (target / "keep.txt").read_text(encoding="utf-8") == "do not touch"
    assert f"Folder already exists: {target}" in capsys.readouterr().out


def test_exits_cleanly_when_configured_directory_is_not_accessible(tmp_path, monkeypatch, capsys):
    missing = tmp_path / "not-mounted"
    monkeypatch.setattr(shared_drive, "load_config_value", lambda *args, **kwargs: str(missing))

    with pytest.raises(SystemExit):
        shared_drive.main()

    assert "not accessible" in capsys.readouterr().out


def test_exits_cleanly_when_config_cannot_be_obtained(monkeypatch, capsys):
    def raise_missing(*args, **kwargs):
        raise shared_drive.MissingConfigError(
            "Shared Drive root folder is not configured, and no terminal is attached."
        )

    monkeypatch.setattr(shared_drive, "load_config_value", raise_missing)

    with pytest.raises(SystemExit):
        shared_drive.main()

    assert "not configured" in capsys.readouterr().out


def test_validate_shared_drive_directory_rejects_missing_path(tmp_path):
    with pytest.raises(ValueError):
        shared_drive.validate_shared_drive_directory(str(tmp_path / "nope"))


def test_validate_shared_drive_directory_accepts_existing_directory(tmp_path):
    shared_drive.validate_shared_drive_directory(str(tmp_path))  # does not raise


def test_ensure_boring_stuff_folder_creates_when_missing(tmp_path):
    target, created = shared_drive.ensure_boring_stuff_folder(tmp_path)

    assert created is True
    assert target == tmp_path / "boring-stuff"
    assert target.is_dir()


def test_ensure_boring_stuff_folder_reports_existing(tmp_path):
    existing = tmp_path / "boring-stuff"
    existing.mkdir()

    target, created = shared_drive.ensure_boring_stuff_folder(tmp_path)

    assert created is False
    assert target == existing
