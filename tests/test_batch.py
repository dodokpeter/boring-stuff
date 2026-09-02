from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from cases.devs import batch


def fake_result(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 1, 10, 15, 32)

    monkeypatch.setattr(batch, "datetime", FixedDateTime)


# --- read_queue / write_queue ---


def test_read_queue_returns_none_when_file_missing(tmp_path):
    assert batch.read_queue(tmp_path / "toProcess.txt") is None


def test_read_queue_skips_blank_and_comment_lines(tmp_path):
    queue_path = tmp_path / "toProcess.txt"
    queue_path.write_text("cmd-a\n\n# a comment\n  \ncmd-b\n#cmd-c\n", encoding="utf-8")

    assert batch.read_queue(queue_path) == ["cmd-a", "cmd-b"]


def test_read_queue_returns_empty_list_for_all_comment_file(tmp_path):
    queue_path = tmp_path / "toProcess.txt"
    queue_path.write_text("# nothing here\n\n", encoding="utf-8")

    assert batch.read_queue(queue_path) == []


def test_write_queue_round_trips_through_read(tmp_path):
    queue_path = tmp_path / "toProcess.txt"

    batch.write_queue(queue_path, ["cmd-a", "cmd-b"])

    assert batch.read_queue(queue_path) == ["cmd-a", "cmd-b"]


def test_write_queue_replaces_existing_content(tmp_path):
    queue_path = tmp_path / "toProcess.txt"
    queue_path.write_text("old-cmd\n", encoding="utf-8")

    batch.write_queue(queue_path, ["new-cmd"])

    assert queue_path.read_text(encoding="utf-8") == "new-cmd\n"
    assert not queue_path.with_suffix(".txt.tmp").exists()


def test_write_queue_empty_list_produces_empty_file(tmp_path):
    queue_path = tmp_path / "toProcess.txt"

    batch.write_queue(queue_path, [])

    assert queue_path.read_text(encoding="utf-8") == ""


def test_write_queue_retries_past_a_transient_permission_error(tmp_path, monkeypatch):
    # A real, observed Windows quirk: os.replace() can transiently raise
    # PermissionError (antivirus/indexer briefly holding the temp file)
    # even though nothing is actually wrong - write_queue must retry
    # rather than propagate the first failure.
    queue_path = tmp_path / "toProcess.txt"
    real_replace = Path.replace
    calls = []

    def flaky_replace(self, target):
        calls.append(self)
        if len(calls) < 3:
            raise PermissionError("simulated transient lock")
        return real_replace(self, target)

    monkeypatch.setattr(batch, "time", SimpleNamespace(sleep=lambda seconds: None))
    monkeypatch.setattr(Path, "replace", flaky_replace)

    batch.write_queue(queue_path, ["cmd-a"])

    assert len(calls) == 3
    assert batch.read_queue(queue_path) == ["cmd-a"]


def test_write_queue_gives_up_after_repeated_permission_errors(tmp_path, monkeypatch):
    def always_fails(self, target):
        raise PermissionError("simulated persistent lock")

    monkeypatch.setattr(batch, "time", SimpleNamespace(sleep=lambda seconds: None))
    monkeypatch.setattr(Path, "replace", always_fails)

    with pytest.raises(PermissionError):
        batch.write_queue(tmp_path / "toProcess.txt", ["cmd-a"])


# --- process_queue_file: ordering / logging ---


def test_runs_commands_in_order(tmp_path, monkeypatch):
    (tmp_path / "toProcess.txt").write_text("cmd-a\ncmd-b\ncmd-c\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr(batch.subprocess, "run", lambda line, **kw: calls.append(line) or fake_result())

    exit_code = batch.process_queue_file(tmp_path)

    assert exit_code == 0
    assert calls == ["cmd-a", "cmd-b", "cmd-c"]


def test_successful_command_appends_to_processed_log(tmp_path, monkeypatch):
    (tmp_path / "toProcess.txt").write_text("cmd-a\n", encoding="utf-8")
    monkeypatch.setattr(batch.subprocess, "run", lambda line, **kw: fake_result(returncode=0))

    batch.process_queue_file(tmp_path)

    processed = tmp_path / "logs" / "2026-09-01_processed.txt"
    assert processed.read_text(encoding="utf-8") == "cmd-a\n"
    assert not (tmp_path / "logs" / "2026-09-01_errors.txt").exists()


def test_failed_command_appends_to_errors_log_verbatim(tmp_path, monkeypatch):
    (tmp_path / "toProcess.txt").write_text("cmd-a --flag\n", encoding="utf-8")
    monkeypatch.setattr(batch.subprocess, "run", lambda line, **kw: fake_result(returncode=1))

    batch.process_queue_file(tmp_path)

    errors = tmp_path / "logs" / "2026-09-01_errors.txt"
    assert errors.read_text(encoding="utf-8") == "cmd-a --flag\n"
    assert not (tmp_path / "logs" / "2026-09-01_processed.txt").exists()


def test_failed_command_writes_diagnostics_block(tmp_path, monkeypatch):
    (tmp_path / "toProcess.txt").write_text("cmd-a\n", encoding="utf-8")
    monkeypatch.setattr(
        batch.subprocess, "run", lambda line, **kw: fake_result(returncode=3, stdout="some output", stderr="boom")
    )

    batch.process_queue_file(tmp_path)

    content = (tmp_path / "logs" / "2026-09-01_errors_logs.txt").read_text(encoding="utf-8")
    assert "[2026-09-01 10:15:32] cmd-a" in content
    assert "exit code: 3" in content
    assert "stderr:" in content
    assert "boom" in content
    assert "stdout:" in content
    assert "some output" in content


def test_successful_command_adds_nothing_to_errors_logs(tmp_path, monkeypatch):
    (tmp_path / "toProcess.txt").write_text("cmd-a\n", encoding="utf-8")
    monkeypatch.setattr(batch.subprocess, "run", lambda line, **kw: fake_result(returncode=0))

    batch.process_queue_file(tmp_path)

    assert not (tmp_path / "logs" / "2026-09-01_errors_logs.txt").exists()


def test_diagnostics_block_omits_stdout_section_when_empty(tmp_path, monkeypatch):
    (tmp_path / "toProcess.txt").write_text("cmd-a\n", encoding="utf-8")
    monkeypatch.setattr(batch.subprocess, "run", lambda line, **kw: fake_result(returncode=1, stdout="", stderr="boom"))

    batch.process_queue_file(tmp_path)

    content = (tmp_path / "logs" / "2026-09-01_errors_logs.txt").read_text(encoding="utf-8")
    assert "stdout:" not in content


def test_logs_are_appended_across_multiple_runs_same_day(tmp_path, monkeypatch):
    (tmp_path / "toProcess.txt").write_text("cmd-a\n", encoding="utf-8")
    monkeypatch.setattr(batch.subprocess, "run", lambda line, **kw: fake_result(returncode=0))
    batch.process_queue_file(tmp_path)

    (tmp_path / "toProcess.txt").write_text("cmd-b\n", encoding="utf-8")
    batch.process_queue_file(tmp_path)

    processed = tmp_path / "logs" / "2026-09-01_processed.txt"
    assert processed.read_text(encoding="utf-8") == "cmd-a\ncmd-b\n"


def test_continues_running_after_a_failure(tmp_path, monkeypatch):
    (tmp_path / "toProcess.txt").write_text("bad-cmd\ngood-cmd\n", encoding="utf-8")
    monkeypatch.setattr(
        batch.subprocess, "run", lambda line, **kw: fake_result(returncode=1 if line == "bad-cmd" else 0)
    )

    batch.process_queue_file(tmp_path)

    assert "good-cmd" in (tmp_path / "logs" / "2026-09-01_processed.txt").read_text(encoding="utf-8")
    assert "bad-cmd" in (tmp_path / "logs" / "2026-09-01_errors.txt").read_text(encoding="utf-8")


# --- process_queue_file: queue rewrite behavior ---


def test_queue_is_empty_after_a_full_successful_run(tmp_path, monkeypatch):
    (tmp_path / "toProcess.txt").write_text("cmd-a\ncmd-b\n", encoding="utf-8")
    monkeypatch.setattr(batch.subprocess, "run", lambda line, **kw: fake_result(returncode=0))

    batch.process_queue_file(tmp_path)

    assert batch.read_queue(tmp_path / "toProcess.txt") == []


def test_queue_is_rewritten_before_the_next_command_starts(tmp_path, monkeypatch):
    queue_path = tmp_path / "toProcess.txt"
    queue_path.write_text("cmd-a\ncmd-b\ncmd-c\n", encoding="utf-8")
    seen_before_second_call = []

    def fake_run(line, **kw):
        if line == "cmd-b":
            seen_before_second_call.append(batch.read_queue(queue_path))
        return fake_result()

    monkeypatch.setattr(batch.subprocess, "run", fake_run)

    batch.process_queue_file(tmp_path)

    assert seen_before_second_call == [["cmd-b", "cmd-c"]]


def test_completed_command_line_is_removed_even_on_failure(tmp_path, monkeypatch):
    (tmp_path / "toProcess.txt").write_text("bad-cmd\n", encoding="utf-8")
    monkeypatch.setattr(batch.subprocess, "run", lambda line, **kw: fake_result(returncode=1))

    batch.process_queue_file(tmp_path)

    assert batch.read_queue(tmp_path / "toProcess.txt") == []


# --- process_queue_file: edge cases ---


def test_missing_queue_file_prints_message_and_returns_nonzero(tmp_path, capsys):
    exit_code = batch.process_queue_file(tmp_path)

    assert exit_code != 0
    assert "toProcess.txt" in capsys.readouterr().out


def test_empty_queue_reports_nothing_to_do_and_returns_zero(tmp_path, capsys):
    (tmp_path / "toProcess.txt").write_text("# just a comment\n", encoding="utf-8")

    exit_code = batch.process_queue_file(tmp_path)

    assert exit_code == 0
    assert "Nothing to do" in capsys.readouterr().out
    assert not (tmp_path / "logs").exists()


def test_dry_run_lists_commands_without_executing_or_writing_anything(tmp_path, monkeypatch, capsys):
    (tmp_path / "toProcess.txt").write_text("cmd-a\ncmd-b\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr(batch.subprocess, "run", lambda line, **kw: calls.append(line) or fake_result())

    exit_code = batch.process_queue_file(tmp_path, dry_run=True)

    assert exit_code == 0
    assert calls == []
    assert batch.read_queue(tmp_path / "toProcess.txt") == ["cmd-a", "cmd-b"]
    assert not (tmp_path / "logs").exists()
    out = capsys.readouterr().out
    assert "cmd-a" in out
    assert "cmd-b" in out


# --- main ---


def test_main_exits_cleanly_when_config_cannot_be_obtained(monkeypatch, capsys):
    def raise_missing():
        raise batch.MissingConfigError("Cloud folder root is not configured, and no terminal is attached.")

    monkeypatch.setattr(batch, "load_cloud_folder", raise_missing)

    with pytest.raises(SystemExit) as exc_info:
        batch.main([])

    assert exc_info.value.code == 1
    assert "not configured" in capsys.readouterr().out


def test_main_exits_cleanly_when_cloud_folder_not_accessible(tmp_path, monkeypatch, capsys):
    missing = tmp_path / "not-mounted"
    monkeypatch.setattr(batch, "load_cloud_folder", lambda: missing)

    with pytest.raises(SystemExit) as exc_info:
        batch.main([])

    assert exc_info.value.code == 1
    assert "not accessible" in capsys.readouterr().out


def test_main_runs_the_queue_and_exits_zero(tmp_path, monkeypatch):
    (tmp_path / "toProcess.txt").write_text("cmd-a\n", encoding="utf-8")
    monkeypatch.setattr(batch, "load_cloud_folder", lambda: tmp_path)
    monkeypatch.setattr(batch.subprocess, "run", lambda line, **kw: fake_result(returncode=0))

    with pytest.raises(SystemExit) as exc_info:
        batch.main([])

    assert exc_info.value.code == 0


def test_main_dry_run_flag_is_wired_up(tmp_path, monkeypatch):
    (tmp_path / "toProcess.txt").write_text("cmd-a\n", encoding="utf-8")
    monkeypatch.setattr(batch, "load_cloud_folder", lambda: tmp_path)
    calls = []
    monkeypatch.setattr(batch.subprocess, "run", lambda line, **kw: calls.append(line) or fake_result())

    with pytest.raises(SystemExit):
        batch.main(["--dry-run"])

    assert calls == []


# --- end-to-end against real noop subprocesses ---


def test_end_to_end_with_real_noop_and_noop_fail_subprocesses(tmp_path):
    (tmp_path / "toProcess.txt").write_text("noop\nnoop --fail\n", encoding="utf-8")

    exit_code = batch.process_queue_file(tmp_path)

    assert exit_code == 0
    assert batch.read_queue(tmp_path / "toProcess.txt") == []

    processed = (tmp_path / "logs" / "2026-09-01_processed.txt").read_text(encoding="utf-8")
    assert processed == "noop\n"

    errors = (tmp_path / "logs" / "2026-09-01_errors.txt").read_text(encoding="utf-8")
    assert errors == "noop --fail\n"

    errors_logs = (tmp_path / "logs" / "2026-09-01_errors_logs.txt").read_text(encoding="utf-8")
    assert "noop --fail" in errors_logs
    assert "exit code: 1" in errors_logs
    assert "failing as requested" in errors_logs
