import builtins
import shutil
import subprocess

import pytest

from cases.webs import joinfiles, splitfiles
from core.configuration import user_conf


def answer_with(monkeypatch, *answers):
    values = iter(answers)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(values))


# --- plan_parts -------------------------------------------------------


def test_plan_parts_exact_multiple():
    assert splitfiles.plan_parts(60 * 60, 30) == [1800, 1800]


def test_plan_parts_remainder_just_under_five_minutes_is_absorbed():
    duration = 2 * 1800 + 299  # 2 full 30-min parts + a 4:59 remainder
    assert splitfiles.plan_parts(duration, 30) == [1800, 1800 + 299]


def test_plan_parts_remainder_just_at_five_minutes_becomes_its_own_part():
    duration = 2 * 1800 + 300  # 2 full 30-min parts + exactly a 5:00 remainder
    assert splitfiles.plan_parts(duration, 30) == [1800, 1800, 300]


def test_plan_parts_shorter_than_one_part_is_nothing_to_split():
    assert splitfiles.plan_parts(1000, 30) == []


def test_plan_parts_one_part_plus_sub_five_minute_tail_is_nothing_to_split():
    duration = 1800 + 120  # one 30-min part plus a 2-min tail
    assert splitfiles.plan_parts(duration, 30) == []


def test_plan_parts_matches_issue_examples():
    assert splitfiles.plan_parts(61 * 60, 30) == [1800, 31 * 60]
    assert splitfiles.plan_parts(66 * 60, 30) == [1800, 1800, 6 * 60]
    assert splitfiles.plan_parts(34 * 60, 30) == []


# --- format_duration ----------------------------------------------------


def test_format_duration_under_an_hour():
    assert splitfiles.format_duration(37 * 60) == "37m"


def test_format_duration_with_hours():
    assert splitfiles.format_duration(2 * 3600 + 7 * 60) == "2h 07m"


def test_format_duration_rounds_half_a_minute_up_not_to_even():
    # plain round() (banker's rounding) would give "2m" here, not "3m" -
    # found for real while manually verifying against an actual video.
    assert splitfiles.format_duration(150) == "3m"


# --- prompt_for_minutes ---------------------------------------------------


def test_prompt_for_minutes_blank_answer_accepts_default(monkeypatch):
    answer_with(monkeypatch, "")
    assert splitfiles.prompt_for_minutes(30) == 30


def test_prompt_for_minutes_accepts_a_valid_number(monkeypatch):
    answer_with(monkeypatch, "45")
    assert splitfiles.prompt_for_minutes(30) == 45


def test_prompt_for_minutes_reprompts_on_non_numeric_answer(monkeypatch):
    answer_with(monkeypatch, "banana", "20")
    assert splitfiles.prompt_for_minutes(30) == 20


def test_prompt_for_minutes_reprompts_on_zero_or_negative(monkeypatch):
    answer_with(monkeypatch, "0", "-5", "15")
    assert splitfiles.prompt_for_minutes(30) == 15


# --- load_default_minutes -------------------------------------------------


def test_load_default_minutes_falls_back_when_unset(tmp_path, monkeypatch):
    monkeypatch.setattr(user_conf.Path, "home", lambda: tmp_path)
    assert splitfiles.load_default_minutes() == splitfiles.DEFAULT_MINUTES


def test_load_default_minutes_reads_configured_value(tmp_path, monkeypatch):
    monkeypatch.setattr(user_conf.Path, "home", lambda: tmp_path)
    user_conf.save_config(None, {"splitfiles": {"minutes": 45}})
    assert splitfiles.load_default_minutes() == 45


# --- main: argument/file/type handling -------------------------------------


def test_no_path_exits_with_usage_error():
    with pytest.raises(SystemExit) as exc_info:
        splitfiles.main([])
    assert exc_info.value.code == 2


def test_missing_file_prints_message_and_exits_non_zero(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc_info:
        splitfiles.main([str(tmp_path / "nope.mp4")])
    assert exc_info.value.code != 0
    assert "is not a file" in capsys.readouterr().out


def test_unsupported_extension_prints_message_and_exits_non_zero(tmp_path, capsys):
    file_path = tmp_path / "audio.wav"
    file_path.write_bytes(b"")

    with pytest.raises(SystemExit) as exc_info:
        splitfiles.main([str(file_path)])

    assert exc_info.value.code != 0
    out = capsys.readouterr().out
    assert "Unsupported file type" in out
    assert ".mp4" in out


def test_extension_check_is_case_insensitive(tmp_path, monkeypatch):
    file_path = tmp_path / "movie.MP4"
    file_path.write_bytes(b"")

    calls = []
    monkeypatch.setattr(splitfiles, "SPLITTERS", {".mp4": lambda path, minutes: calls.append((path, minutes))})

    splitfiles.main([str(file_path), "-m", "10"])

    assert calls == [(file_path, 10)]


def test_minutes_flag_skips_the_prompt(tmp_path, monkeypatch):
    file_path = tmp_path / "movie.mp4"
    file_path.write_bytes(b"")

    calls = []
    monkeypatch.setattr(splitfiles, "SPLITTERS", {".mp4": lambda path, minutes: calls.append((path, minutes))})
    monkeypatch.setattr(builtins, "input", lambda prompt="": (_ for _ in ()).throw(AssertionError("must not prompt")))

    splitfiles.main([str(file_path), "-m", "45"])

    assert calls == [(file_path, 45)]


def test_minutes_flag_rejects_non_positive_value(tmp_path, capsys):
    file_path = tmp_path / "movie.mp4"
    file_path.write_bytes(b"")

    with pytest.raises(SystemExit) as exc_info:
        splitfiles.main([str(file_path), "-m", "0"])

    assert exc_info.value.code != 0
    assert "positive whole number" in capsys.readouterr().out


def test_no_minutes_flag_falls_back_to_prompt(tmp_path, monkeypatch):
    file_path = tmp_path / "movie.mp4"
    file_path.write_bytes(b"")

    calls = []
    monkeypatch.setattr(splitfiles, "SPLITTERS", {".mp4": lambda path, minutes: calls.append((path, minutes))})
    monkeypatch.setattr(splitfiles, "load_default_minutes", lambda: 30)
    answer_with(monkeypatch, "")

    splitfiles.main([str(file_path)])

    assert calls == [(file_path, 30)]


# --- split_mp4 -----------------------------------------------------------


def test_split_mp4_reports_nothing_to_split_and_does_not_call_ffmpeg(tmp_path, monkeypatch, capsys):
    file_path = tmp_path / "short.mp4"
    file_path.write_bytes(b"")

    monkeypatch.setattr(splitfiles, "get_duration_seconds", lambda path: 34 * 60)
    calls = []
    monkeypatch.setattr(splitfiles, "run_ffmpeg_segment", lambda *a: calls.append(a))

    splitfiles.split_mp4(file_path, 30)

    assert calls == []
    assert "nothing to split" in capsys.readouterr().out


def test_split_mp4_writes_parts_into_sibling_folder(tmp_path, monkeypatch, capsys):
    file_path = tmp_path / "Lecture.mp4"
    file_path.write_bytes(b"")

    monkeypatch.setattr(splitfiles, "get_duration_seconds", lambda path: 61 * 60)
    calls = []
    monkeypatch.setattr(
        splitfiles, "run_ffmpeg_segment", lambda path, cut_points, pattern: calls.append((path, cut_points, pattern))
    )

    splitfiles.split_mp4(file_path, 30)

    assert len(calls) == 1
    called_path, cut_points, pattern = calls[0]
    assert called_path == file_path
    assert cut_points == [1800]
    expected_dir = tmp_path / "Lecture - parts"
    assert pattern == expected_dir / "Lecture - part %02d.mp4"
    assert expected_dir.is_dir()

    out = capsys.readouterr().out
    assert "2 parts of 30 min" in out
    assert "last part 31m" in out


def test_run_ffmpeg_segment_invokes_ffmpeg_with_expected_arguments(tmp_path, monkeypatch):
    file_path = tmp_path / "movie.mp4"
    output_pattern = tmp_path / "movie - parts" / "movie - part %02d.mp4"

    calls = []
    monkeypatch.setattr(splitfiles.subprocess, "run", lambda cmd, **kwargs: calls.append((cmd, kwargs)))

    splitfiles.run_ffmpeg_segment(file_path, [1800, 3600], output_pattern)

    assert len(calls) == 1
    cmd, kwargs = calls[0]
    assert cmd[0] == "ffmpeg"
    assert "-map" in cmd and cmd[cmd.index("-map") + 1] == "0"
    assert "-c" in cmd and cmd[cmd.index("-c") + 1] == "copy"
    assert "-f" in cmd and cmd[cmd.index("-f") + 1] == "segment"
    assert "-segment_times" in cmd and cmd[cmd.index("-segment_times") + 1] == "1800,3600"
    assert "-segment_start_number" in cmd and cmd[cmd.index("-segment_start_number") + 1] == "1"
    assert str(output_pattern) in cmd
    assert kwargs.get("check") is True


# --- end-to-end with a real ffmpeg-generated file --------------------------

requires_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")


@requires_ffmpeg
def test_split_and_rejoin_a_real_video_round_trips(tmp_path):
    source = tmp_path / "source.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=64x64:rate=5:duration=150",  # 2.5 min, synthetic - generates instantly
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-force_key_frames",
            "expr:gte(t,n_forced)",
            str(source),
        ],
        check=True,
        capture_output=True,
    )

    splitfiles.split_mp4(source, 1)  # 1-minute parts -> 60s + a 30s remainder, absorbed into part 1

    parts_dir = tmp_path / "source - parts"
    parts = sorted(parts_dir.glob("*.mp4"))
    assert len(parts) == 2
    assert [p.name for p in parts] == ["source - part 01.mp4", "source - part 02.mp4"]

    rejoined = tmp_path / "rejoined.mp4"
    joinfiles.join_files(parts, rejoined)

    original_duration = splitfiles.get_duration_seconds(source)
    rejoined_duration = splitfiles.get_duration_seconds(rejoined)
    assert rejoined_duration == pytest.approx(original_duration, abs=2)
