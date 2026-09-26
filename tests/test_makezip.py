import zipfile
from datetime import datetime

import pytest

from cases.wins import makezip
from core import stats

FIXED_NOW = datetime(2026, 9, 26, 14, 5, 33)
FIXED_NAME = "Report_2026_09_26___14_05_33.zip"


@pytest.fixture
def report_folder(tmp_path):
    folder = tmp_path / "work" / "Report"
    (folder / "sub" / "deeper").mkdir(parents=True)
    (folder / "empty").mkdir()
    (folder / "a.txt").write_text("alpha", encoding="utf-8")
    (folder / "sub" / "b.txt").write_text("bravo", encoding="utf-8")
    (folder / "sub" / "deeper" / "c.txt").write_text("charlie", encoding="utf-8")
    return folder


def snapshot(folder):
    return {p.relative_to(folder): (p.read_bytes() if p.is_file() else None) for p in folder.rglob("*")}


def test_archive_name_uses_fixed_timestamp_format(report_folder):
    assert makezip.archive_path_for(report_folder, FIXED_NOW) == report_folder.parent / FIXED_NAME


def test_make_zip_writes_archive_into_the_parent_folder(report_folder):
    archive = makezip.make_zip(report_folder, FIXED_NOW)

    assert archive == report_folder.parent / FIXED_NAME
    assert archive.is_file()
    assert not (report_folder / FIXED_NAME).exists()


def test_make_zip_puts_the_folder_at_the_top_level_with_all_contents(report_folder):
    archive = makezip.make_zip(report_folder, FIXED_NOW)

    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
        assert zf.read("Report/a.txt") == b"alpha"
        assert zf.read("Report/sub/b.txt") == b"bravo"
        assert zf.read("Report/sub/deeper/c.txt") == b"charlie"

    assert {"Report/a.txt", "Report/sub/b.txt", "Report/sub/deeper/c.txt"} <= names
    assert "Report/empty/" in names  # empty subfolders are kept
    assert all(name.startswith("Report/") for name in names)


def test_make_zip_leaves_the_source_folder_untouched(report_folder):
    before = snapshot(report_folder)

    makezip.make_zip(report_folder, FIXED_NOW)

    assert snapshot(report_folder) == before


def test_same_second_collision_gets_a_numeric_suffix_and_never_overwrites(report_folder):
    first = makezip.make_zip(report_folder, FIXED_NOW)
    first_bytes = first.read_bytes()

    second = makezip.make_zip(report_folder, FIXED_NOW)
    third = makezip.make_zip(report_folder, FIXED_NOW)

    assert second == report_folder.parent / "Report_2026_09_26___14_05_33 (1).zip"
    assert third == report_folder.parent / "Report_2026_09_26___14_05_33 (2).zip"
    assert first.read_bytes() == first_bytes


def test_format_size():
    assert makezip.format_size(500) == "500 B"
    assert makezip.format_size(1536) == "1.5 KB"
    assert makezip.format_size(int(12.4 * 1024 * 1024)) == "12.4 MB"


def test_main_zips_the_given_folder_and_prints_source_archive_and_size(report_folder, capsys):
    makezip.main([str(report_folder)])

    archives = list(report_folder.parent.glob("Report_*.zip"))
    assert len(archives) == 1
    out = capsys.readouterr().out
    assert f"Zipping {report_folder}" in out
    assert f"Created: {archives[0]}" in out
    assert "Size: " in out


def test_main_without_argument_zips_the_current_directory(report_folder, monkeypatch):
    monkeypatch.chdir(report_folder)

    makezip.main([])

    archives = list(report_folder.parent.glob("Report_*.zip"))
    assert len(archives) == 1
    with zipfile.ZipFile(archives[0]) as zf:
        assert "Report/a.txt" in zf.namelist()


def test_main_accepts_a_path_with_spaces_split_across_arguments(tmp_path):
    folder = tmp_path / "My Report"
    folder.mkdir()
    (folder / "a.txt").write_text("x", encoding="utf-8")

    makezip.main(str(folder).split(" "))

    assert len(list(tmp_path.glob("My Report_*.zip"))) == 1


def test_main_records_usage():
    with pytest.raises(SystemExit):
        makezip.main(["definitely-not-a-real-folder-xyz"])

    assert [command for command, _ts in stats.read_usage_entries()] == ["makezip"]


def test_nonexistent_path_prints_message_exits_non_zero_and_creates_nothing(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc_info:
        makezip.main([str(tmp_path / "nope")])

    assert exc_info.value.code != 0
    assert "does not exist" in capsys.readouterr().out
    assert list(tmp_path.glob("*.zip")) == []


def test_file_path_prints_message_exits_non_zero_and_creates_nothing(tmp_path, capsys):
    file_path = tmp_path / "notafolder.txt"
    file_path.write_text("x", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        makezip.main([str(file_path)])

    assert exc_info.value.code != 0
    assert "is not a folder" in capsys.readouterr().out
    assert list(tmp_path.glob("*.zip")) == []


def test_drive_root_prints_message_exits_non_zero_and_creates_nothing(tmp_path, monkeypatch, capsys):
    made = []
    monkeypatch.setattr(makezip, "make_zip", lambda *a, **kw: made.append(a))
    root = tmp_path.anchor  # "C:\\" on Windows, "/" elsewhere

    with pytest.raises(SystemExit) as exc_info:
        makezip.main([root])

    assert exc_info.value.code != 0
    assert "drive root" in capsys.readouterr().out
    assert made == []
