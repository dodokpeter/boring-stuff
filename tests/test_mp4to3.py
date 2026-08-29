from pathlib import Path

from cases.webs import mp4to3


def test_extracts_audio_for_each_mp4_in_folder(tmp_path, monkeypatch):
    (tmp_path / "song1.mp4").write_bytes(b"")
    (tmp_path / "song2.mp4").write_bytes(b"")

    calls = []
    monkeypatch.setattr(
        mp4to3, "extract_audio",
        lambda input_path, output_path: calls.append((str(input_path), output_path)),
    )
    monkeypatch.setattr(mp4to3.sys, "argv", ["mp4to3", str(tmp_path)])

    mp4to3.main()

    assert len(calls) == 2
    names = {Path(c[0]).name for c in calls}
    assert names == {"song1.mp4", "song2.mp4"}
