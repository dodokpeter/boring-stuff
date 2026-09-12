from pathlib import Path

import pytest

from cases.webs import joinfiles


def test_no_folder_exits_with_usage_error():
    with pytest.raises(SystemExit) as exc_info:
        joinfiles.main([])
    assert exc_info.value.code == 2


def test_prints_message_and_returns_when_folder_does_not_exist(tmp_path, capsys):
    joinfiles.main([str(tmp_path / "nope")])  # must not raise

    assert "not a folder" in capsys.readouterr().out


def test_prints_message_and_returns_when_path_is_a_file(tmp_path, capsys):
    file_path = tmp_path / "notafolder.txt"
    file_path.write_bytes(b"")

    joinfiles.main([str(file_path)])

    assert "not a folder" in capsys.readouterr().out


def test_find_input_files_sorts_alphabetically_and_excludes_own_output(tmp_path):
    (tmp_path / "b.m4a").write_bytes(b"")
    (tmp_path / "a.m4a").write_bytes(b"")
    (tmp_path / "c.m4a").write_bytes(b"")
    (tmp_path / "joined.m4a").write_bytes(b"")
    (tmp_path / "other.mp3").write_bytes(b"")

    files = joinfiles.find_input_files(tmp_path)

    assert [f.name for f in files] == ["a.m4a", "b.m4a", "c.m4a"]


def test_prints_message_and_does_not_join_with_fewer_than_two_files(tmp_path, monkeypatch, capsys):
    (tmp_path / "only.m4a").write_bytes(b"")

    calls = []
    monkeypatch.setattr(joinfiles, "join_files", lambda files, output_path: calls.append((files, output_path)))

    joinfiles.main([str(tmp_path)])

    assert calls == []
    assert "need at least 2" in capsys.readouterr().out


def test_joins_every_m4a_file_in_folder_order(tmp_path, monkeypatch, capsys):
    (tmp_path / "b.m4a").write_bytes(b"")
    (tmp_path / "a.m4a").write_bytes(b"")

    calls = []
    monkeypatch.setattr(joinfiles, "join_files", lambda files, output_path: calls.append((files, output_path)))

    joinfiles.main([str(tmp_path)])

    assert len(calls) == 1
    files, output_path = calls[0]
    assert [f.name for f in files] == ["a.m4a", "b.m4a"]
    assert output_path == tmp_path / "joined.m4a"

    out_lines = capsys.readouterr().out.splitlines()
    assert out_lines[:2] == ["a.m4a", "b.m4a"]


def test_excludes_previous_output_from_a_rerun(tmp_path, monkeypatch):
    (tmp_path / "a.m4a").write_bytes(b"")
    (tmp_path / "b.m4a").write_bytes(b"")
    (tmp_path / "joined.m4a").write_bytes(b"")  # a previous run's output

    calls = []
    monkeypatch.setattr(joinfiles, "join_files", lambda files, output_path: calls.append((files, output_path)))

    joinfiles.main([str(tmp_path)])

    assert len(calls) == 1
    files, _output_path = calls[0]
    assert [f.name for f in files] == ["a.m4a", "b.m4a"]


def test_escape_concat_path_escapes_single_quotes(tmp_path):
    path = tmp_path / "it's a song.m4a"

    escaped = joinfiles.escape_concat_path(path)

    assert "'\\''" in escaped
    assert escaped.count("'") == 3  # the 2 escape quotes + the literal one from the filename


def test_write_concat_list_writes_one_quoted_file_line_per_input(tmp_path):
    file_a = tmp_path / "a.m4a"
    file_b = tmp_path / "b.m4a"
    file_a.write_bytes(b"")
    file_b.write_bytes(b"")
    list_path = tmp_path / "list.txt"

    joinfiles.write_concat_list([file_a, file_b], list_path)

    content = list_path.read_text(encoding="utf-8")
    assert content == f"file '{file_a.resolve()}'\nfile '{file_b.resolve()}'\n"


def test_join_files_invokes_ffmpeg_with_concat_demuxer_and_stream_copy(tmp_path, monkeypatch):
    file_a = tmp_path / "a.m4a"
    file_b = tmp_path / "b.m4a"
    file_a.write_bytes(b"")
    file_b.write_bytes(b"")
    output_path = tmp_path / "joined.m4a"

    calls = []
    monkeypatch.setattr(joinfiles.subprocess, "run", lambda cmd, **kwargs: calls.append((cmd, kwargs)))

    joinfiles.join_files([file_a, file_b], output_path)

    assert len(calls) == 1
    cmd, kwargs = calls[0]
    assert cmd[0] == "ffmpeg"
    assert "-c" in cmd and cmd[cmd.index("-c") + 1] == "copy"
    assert str(output_path) in cmd
    assert kwargs.get("check") is True

    # the temporary concat-list file is cleaned up afterward
    list_path = Path(cmd[cmd.index("-i") + 1])
    assert not list_path.exists()
