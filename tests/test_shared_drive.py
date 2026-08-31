import pytest

from cases.wins import shared_drive
from core import cloud


def test_prompts_and_persists_config_when_not_configured(tmp_path, monkeypatch, capsys):
    root = tmp_path / "SharedDrive"
    root.mkdir()

    calls = []

    def fake_load_config_value(config_name, message, default, *keys, validate=None):
        calls.append((config_name, message, default, keys))
        if validate is not None:
            validate(str(root))
        if keys == ("cloud", "folder"):
            return str(root)
        return "share"

    monkeypatch.setattr(cloud, "load_config_value", fake_load_config_value)

    shared_drive.main()

    assert calls[0] == (
        None,
        "Cloud folder root (e.g. your Google Drive mount path)",
        None,
        ("cloud", "folder"),
    )
    assert calls[1] == (None, "Cloud 'share' subfolder name", "share", ("cloud", "share"))

    target = root / "share"
    assert target.is_dir()

    out = capsys.readouterr().out
    assert f"Created folder: {target}" in out


def test_creates_share_folder_when_missing(tmp_path, monkeypatch, capsys):
    root = tmp_path / "SharedDrive"
    root.mkdir()
    monkeypatch.setattr(shared_drive, "load_cloud_folder", lambda: root)
    monkeypatch.setattr(shared_drive, "load_cloud_subfolder_name", lambda key, default: "share")

    shared_drive.main()

    target = root / "share"
    assert target.is_dir()
    assert f"Created folder: {target}" in capsys.readouterr().out


def test_leaves_existing_share_folder_alone(tmp_path, monkeypatch, capsys):
    root = tmp_path / "SharedDrive"
    root.mkdir()
    target = root / "share"
    target.mkdir()
    (target / "keep.txt").write_text("do not touch", encoding="utf-8")
    monkeypatch.setattr(shared_drive, "load_cloud_folder", lambda: root)
    monkeypatch.setattr(shared_drive, "load_cloud_subfolder_name", lambda key, default: "share")

    shared_drive.main()

    assert (target / "keep.txt").read_text(encoding="utf-8") == "do not touch"
    assert f"Folder already exists: {target}" in capsys.readouterr().out


def test_respects_a_custom_share_subfolder_name(tmp_path, monkeypatch, capsys):
    root = tmp_path / "SharedDrive"
    root.mkdir()
    monkeypatch.setattr(shared_drive, "load_cloud_folder", lambda: root)
    monkeypatch.setattr(shared_drive, "load_cloud_subfolder_name", lambda key, default: "custom-share-name")

    shared_drive.main()

    target = root / "custom-share-name"
    assert target.is_dir()
    assert f"Created folder: {target}" in capsys.readouterr().out


def test_exits_cleanly_when_configured_cloud_folder_is_not_accessible(tmp_path, monkeypatch, capsys):
    missing = tmp_path / "not-mounted"
    monkeypatch.setattr(shared_drive, "load_cloud_folder", lambda: missing)
    monkeypatch.setattr(shared_drive, "load_cloud_subfolder_name", lambda key, default: "share")

    with pytest.raises(SystemExit):
        shared_drive.main()

    assert "not accessible" in capsys.readouterr().out


def test_exits_cleanly_when_config_cannot_be_obtained(monkeypatch, capsys):
    def raise_missing():
        raise shared_drive.MissingConfigError("Cloud folder root is not configured, and no terminal is attached.")

    monkeypatch.setattr(shared_drive, "load_cloud_folder", raise_missing)

    with pytest.raises(SystemExit):
        shared_drive.main()

    assert "not configured" in capsys.readouterr().out


def test_ensure_share_folder_creates_when_missing(tmp_path):
    target, created = shared_drive.ensure_share_folder(tmp_path, "share")

    assert created is True
    assert target == tmp_path / "share"
    assert target.is_dir()


def test_ensure_share_folder_reports_existing(tmp_path):
    existing = tmp_path / "share"
    existing.mkdir()

    target, created = shared_drive.ensure_share_folder(tmp_path, "share")

    assert created is False
    assert target == existing
