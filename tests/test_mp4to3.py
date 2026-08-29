from pathlib import Path

import pytest

from cases.webs import mp4to3


def test_no_folder_exits_with_usage_error():
    with pytest.raises(SystemExit) as exc_info:
        mp4to3.main([])
    assert exc_info.value.code == 2


def test_extracts_audio_for_each_mp4_in_folder(tmp_path, monkeypatch):
    (tmp_path / "song1.mp4").write_bytes(b"")
    (tmp_path / "song2.mp4").write_bytes(b"")

    calls = []
    monkeypatch.setattr(
        mp4to3, "extract_audio",
        lambda input_path, output_path: calls.append((str(input_path), output_path)),
    )
    mp4to3.main([str(tmp_path)])

    assert len(calls) == 2
    names = {Path(c[0]).name for c in calls}
    assert names == {"song1.mp4", "song2.mp4"}

    expected_audio_dir = Path(f"{tmp_path} - audio")
    for _input_path, output_path in calls:
        assert Path(output_path).parent == expected_audio_dir
        assert output_path.endswith(".mp3")
