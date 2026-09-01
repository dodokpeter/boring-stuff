import pytest

from cases.wins import move_to


def test_move_path_moves_file_into_destination(tmp_path):
    source = tmp_path / "src" / "file.txt"
    source.parent.mkdir()
    source.write_text("content")
    destination_root = tmp_path / "dst"

    result = move_to.move_path(source, destination_root)

    assert result == destination_root / "file.txt"
    assert result.read_text() == "content"
    assert not source.exists()


def test_move_path_moves_folder_into_destination(tmp_path):
    source = tmp_path / "src" / "MyFolder"
    source.mkdir(parents=True)
    (source / "inside.txt").write_text("hi")
    destination_root = tmp_path / "dst"

    result = move_to.move_path(source, destination_root)

    assert result == destination_root / "MyFolder"
    assert (result / "inside.txt").read_text() == "hi"
    assert not source.exists()


def test_move_path_avoids_collision_at_destination(tmp_path):
    source = tmp_path / "src" / "file.txt"
    source.parent.mkdir()
    source.write_text("new")
    destination_root = tmp_path / "dst"
    destination_root.mkdir()
    (destination_root / "file.txt").write_text("existing")

    result = move_to.move_path(source, destination_root)

    assert result == destination_root / "file (1).txt"
    assert (destination_root / "file.txt").read_text() == "existing"
    assert result.read_text() == "new"


def test_move_path_creates_destination_root_if_missing(tmp_path):
    source = tmp_path / "file.txt"
    source.write_text("content")
    destination_root = tmp_path / "does" / "not" / "exist" / "yet"

    result = move_to.move_path(source, destination_root)

    assert result.read_text() == "content"


# --- main ---


def test_main_share_flag_moves_into_cloud_share_subfolder(tmp_path, monkeypatch, capsys):
    cloud_folder = tmp_path / "CloudDrive"
    cloud_folder.mkdir()
    source = tmp_path / "file.txt"
    source.write_text("content")

    monkeypatch.setattr(move_to, "load_cloud_folder", lambda: cloud_folder)
    monkeypatch.setattr(move_to, "load_cloud_subfolder_name", lambda key, default: default)

    move_to.main(["-s", str(source)])

    destination = cloud_folder / "share" / "file.txt"
    assert destination.read_text() == "content"
    assert not source.exists()
    assert f"Moved to: {destination}" in capsys.readouterr().out


def test_main_output_flag_moves_into_cloud_output_subfolder(tmp_path, monkeypatch):
    cloud_folder = tmp_path / "CloudDrive"
    cloud_folder.mkdir()
    source = tmp_path / "file.txt"
    source.write_text("content")

    monkeypatch.setattr(move_to, "load_cloud_folder", lambda: cloud_folder)
    monkeypatch.setattr(move_to, "load_cloud_subfolder_name", lambda key, default: default)

    move_to.main(["-o", str(source)])

    assert (cloud_folder / "output" / "file.txt").read_text() == "content"


def test_main_requests_correct_config_key_per_flag(tmp_path, monkeypatch):
    cloud_folder = tmp_path / "CloudDrive"
    cloud_folder.mkdir()
    source = tmp_path / "file.txt"
    source.write_text("content")

    requested_keys = []
    monkeypatch.setattr(move_to, "load_cloud_folder", lambda: cloud_folder)
    monkeypatch.setattr(
        move_to, "load_cloud_subfolder_name", lambda key, default: requested_keys.append((key, default)) or default
    )

    move_to.main(["-o", str(source)])

    assert requested_keys == [("output", "output")]


def test_main_requires_exactly_one_destination_flag(tmp_path):
    with pytest.raises(SystemExit):
        move_to.main([str(tmp_path)])  # neither -s nor -o


def test_main_rejects_both_destination_flags(tmp_path):
    with pytest.raises(SystemExit):
        move_to.main(["-s", "-o", str(tmp_path)])


def test_main_exits_cleanly_when_source_does_not_exist(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(move_to, "load_cloud_folder", lambda: tmp_path)
    monkeypatch.setattr(move_to, "load_cloud_subfolder_name", lambda key, default: default)

    with pytest.raises(SystemExit):
        move_to.main(["-s", str(tmp_path / "nope.txt")])

    assert "does not exist" in capsys.readouterr().out


def test_main_exits_cleanly_when_config_cannot_be_obtained(tmp_path, monkeypatch, capsys):
    source = tmp_path / "file.txt"
    source.write_text("content")

    def raise_missing():
        raise move_to.MissingConfigError("Cloud folder root is not configured, and no terminal is attached.")

    monkeypatch.setattr(move_to, "load_cloud_folder", raise_missing)

    with pytest.raises(SystemExit):
        move_to.main(["-s", str(source)])

    assert "not configured" in capsys.readouterr().out


def test_main_exits_cleanly_when_cloud_folder_not_accessible(tmp_path, monkeypatch, capsys):
    source = tmp_path / "file.txt"
    source.write_text("content")
    missing_cloud_folder = tmp_path / "not-mounted"

    monkeypatch.setattr(move_to, "load_cloud_folder", lambda: missing_cloud_folder)
    monkeypatch.setattr(move_to, "load_cloud_subfolder_name", lambda key, default: default)

    with pytest.raises(SystemExit):
        move_to.main(["-s", str(source)])

    assert "not accessible" in capsys.readouterr().out
