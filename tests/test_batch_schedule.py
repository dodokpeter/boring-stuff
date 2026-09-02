import pytest

pytest.importorskip("winreg")  # Windows-only feature (schtasks) - same gating idiom used elsewhere in this repo

from types import SimpleNamespace

from cases.devs import batch_schedule


def fake_result(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


SAMPLE_FIELDS_TEXT = """Folder: \\
HostName:                             testHost
TaskName:                             \\BoringStuffBatch
Next Run Time:                        9/3/2026 3:00:00 AM
Status:                               Ready
Start Time:                           3:00:00 AM
Start Date:                           9/2/2026
"""


# --- validate_schedule_time ---


@pytest.mark.parametrize("value", ["03:00:00", "00:00:00", "23:59:00", "06:30:00", "12:00:00", "21:00:00"])
def test_validate_schedule_time_accepts_valid_times(value):
    batch_schedule.validate_schedule_time(value)  # does not raise


@pytest.mark.parametrize(
    "value",
    [
        "3:00:00",  # missing leading zero on hour
        "24:00:00",
        "12:60:00",
        "not-a-time",
        "",
        "03:00",  # missing seconds
        "03:00:45",  # non-zero seconds - schtasks silently truncates these, so they're rejected outright
        "03:00:00:00",
        "3pm",
    ],
)
def test_validate_schedule_time_rejects_invalid_times(value):
    with pytest.raises(ValueError):
        batch_schedule.validate_schedule_time(value)


# --- task_action_command ---


def test_task_action_command_uses_pythonw_and_this_script_with_run_flag():
    command = batch_schedule.task_action_command()

    assert str(batch_schedule.PYTHONW_PATH) in command
    assert str(batch_schedule.SCRIPT_PATH) in command
    assert "--run" in command


# --- create_or_update_task / query_task / delete_task ---


def test_create_or_update_task_calls_schtasks_create_with_force(monkeypatch):
    calls = []
    monkeypatch.setattr(batch_schedule.subprocess, "run", lambda args, **kw: calls.append(args) or fake_result())

    batch_schedule.create_or_update_task("06:30:00")

    (args,) = calls
    assert args[0:2] == ["schtasks", "/Create"]
    assert "/F" in args
    assert "06:30:00" in args
    assert batch_schedule.TASK_NAME in args


def test_query_task_parses_list_output_into_a_dict(monkeypatch):
    monkeypatch.setattr(batch_schedule.subprocess, "run", lambda args, **kw: fake_result(stdout=SAMPLE_FIELDS_TEXT))

    fields = batch_schedule.query_task()

    assert fields["Start Time"] == "3:00:00 AM"
    assert fields["Next Run Time"] == "9/3/2026 3:00:00 AM"
    assert fields["Status"] == "Ready"


def test_query_task_returns_none_when_task_does_not_exist(monkeypatch):
    monkeypatch.setattr(
        batch_schedule.subprocess,
        "run",
        lambda args, **kw: fake_result(returncode=1, stderr="ERROR: The system cannot find the file specified."),
    )

    assert batch_schedule.query_task() is None


def test_delete_task_calls_schtasks_delete(monkeypatch):
    calls = []
    monkeypatch.setattr(batch_schedule.subprocess, "run", lambda args, **kw: calls.append(args) or fake_result())

    batch_schedule.delete_task()

    (args,) = calls
    assert args[0:2] == ["schtasks", "/Delete"]
    assert batch_schedule.TASK_NAME in args


# --- parse_task_start_time ---


def test_parse_task_start_time_normalizes_12_hour_am():
    assert batch_schedule.parse_task_start_time({"Start Time": "3:00:00 AM"}) == "03:00:00"


def test_parse_task_start_time_normalizes_12_hour_pm():
    assert batch_schedule.parse_task_start_time({"Start Time": "2:30:00 PM"}) == "14:30:00"


def test_parse_task_start_time_handles_midnight_and_noon():
    assert batch_schedule.parse_task_start_time({"Start Time": "12:00:00 AM"}) == "00:00:00"
    assert batch_schedule.parse_task_start_time({"Start Time": "12:00:00 PM"}) == "12:00:00"


def test_parse_task_start_time_returns_none_when_field_missing():
    assert batch_schedule.parse_task_start_time({}) is None


def test_parse_task_start_time_returns_none_for_unparseable_value():
    assert batch_schedule.parse_task_start_time({"Start Time": "garbage"}) is None


def test_parse_task_start_time_truncates_nonzero_seconds_like_schtasks_does():
    # schtasks itself never reports non-zero seconds back (it silently
    # truncates /ST to minute precision), but this confirms parsing
    # wouldn't choke if it ever did.
    assert batch_schedule.parse_task_start_time({"Start Time": "3:00:45 AM"}) == "03:00:45"


# --- register ---


def test_register_creates_task_with_configured_time(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(batch_schedule, "load_cloud_folder", lambda: tmp_path)
    monkeypatch.setattr(batch_schedule, "load_schedule_time", lambda: "06:30:00")
    calls = []
    monkeypatch.setattr(batch_schedule, "create_or_update_task", lambda t: calls.append(t))

    batch_schedule.register()

    assert calls == ["06:30:00"]
    assert "06:30:00" in capsys.readouterr().out


def test_register_exits_when_cloud_folder_config_missing(monkeypatch, capsys):
    def raise_missing():
        raise batch_schedule.MissingConfigError("Cloud folder root is not configured, and no terminal is attached.")

    monkeypatch.setattr(batch_schedule, "load_cloud_folder", raise_missing)

    with pytest.raises(SystemExit):
        batch_schedule.register()

    assert "not configured" in capsys.readouterr().out


def test_register_exits_when_cloud_folder_not_accessible(tmp_path, monkeypatch, capsys):
    missing = tmp_path / "not-mounted"
    monkeypatch.setattr(batch_schedule, "load_cloud_folder", lambda: missing)

    with pytest.raises(SystemExit):
        batch_schedule.register()

    assert "not accessible" in capsys.readouterr().out


def test_register_exits_when_schedule_time_config_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(batch_schedule, "load_cloud_folder", lambda: tmp_path)

    def raise_missing():
        raise batch_schedule.MissingConfigError("Daily batch time is not configured, and no terminal is attached.")

    monkeypatch.setattr(batch_schedule, "load_schedule_time", raise_missing)

    with pytest.raises(SystemExit):
        batch_schedule.register()

    assert "not configured" in capsys.readouterr().out


# --- status ---


def test_status_reports_unregistered_task(monkeypatch, capsys):
    monkeypatch.setattr(batch_schedule, "query_task", lambda: None)

    batch_schedule.status()

    assert "not registered" in capsys.readouterr().out


def test_status_reports_matching_configured_and_task_time(monkeypatch, capsys):
    monkeypatch.setattr(
        batch_schedule, "query_task", lambda: {"Start Time": "3:00:00 AM", "Next Run Time": "9/3/2026 3:00:00 AM"}
    )
    monkeypatch.setattr(batch_schedule, "load_schedule_time", lambda: "03:00:00")

    batch_schedule.status()

    out = capsys.readouterr().out
    assert "03:00:00" in out
    assert "differ" not in out


def test_status_flags_when_configured_and_task_time_differ(monkeypatch, capsys):
    monkeypatch.setattr(
        batch_schedule, "query_task", lambda: {"Start Time": "3:00:00 AM", "Next Run Time": "9/3/2026 3:00:00 AM"}
    )
    monkeypatch.setattr(batch_schedule, "load_schedule_time", lambda: "06:30:00")

    batch_schedule.status()

    out = capsys.readouterr().out
    assert "06:30:00" in out
    assert "differ" in out


# --- uninstall ---


def test_uninstall_reports_nothing_to_remove_when_not_registered(monkeypatch, capsys):
    monkeypatch.setattr(batch_schedule, "query_task", lambda: None)
    calls = []
    monkeypatch.setattr(batch_schedule, "delete_task", lambda: calls.append(True))

    batch_schedule.uninstall()

    assert calls == []
    assert "nothing to remove" in capsys.readouterr().out


def test_uninstall_removes_an_existing_task(monkeypatch, capsys):
    monkeypatch.setattr(batch_schedule, "query_task", lambda: {"Start Time": "3:00:00 AM"})
    calls = []
    monkeypatch.setattr(batch_schedule, "delete_task", lambda: calls.append(True))

    batch_schedule.uninstall()

    assert calls == [True]
    assert "Removed" in capsys.readouterr().out


# --- run_scheduled ---


def test_run_scheduled_syncs_trigger_when_time_has_drifted(tmp_path, monkeypatch):
    monkeypatch.setattr(batch_schedule, "load_schedule_time", lambda: "06:30:00")
    monkeypatch.setattr(batch_schedule, "query_task", lambda: {"Start Time": "3:00:00 AM"})
    sync_calls = []
    monkeypatch.setattr(batch_schedule, "create_or_update_task", lambda t: sync_calls.append(t))
    monkeypatch.setattr(batch_schedule, "load_cloud_folder", lambda: tmp_path)
    monkeypatch.setattr(batch_schedule, "process_queue_file", lambda folder: 0)

    result = batch_schedule.run_scheduled()

    assert sync_calls == ["06:30:00"]
    assert result == 0


def test_run_scheduled_does_not_resync_when_time_matches(tmp_path, monkeypatch):
    monkeypatch.setattr(batch_schedule, "load_schedule_time", lambda: "03:00:00")
    monkeypatch.setattr(batch_schedule, "query_task", lambda: {"Start Time": "3:00:00 AM"})
    sync_calls = []
    monkeypatch.setattr(batch_schedule, "create_or_update_task", lambda t: sync_calls.append(t))
    monkeypatch.setattr(batch_schedule, "load_cloud_folder", lambda: tmp_path)
    monkeypatch.setattr(batch_schedule, "process_queue_file", lambda folder: 0)

    batch_schedule.run_scheduled()

    assert sync_calls == []


def test_run_scheduled_runs_the_queue_and_returns_its_exit_code(tmp_path, monkeypatch):
    monkeypatch.setattr(batch_schedule, "load_schedule_time", lambda: "03:00:00")
    monkeypatch.setattr(batch_schedule, "query_task", lambda: {"Start Time": "3:00:00 AM"})
    monkeypatch.setattr(batch_schedule, "load_cloud_folder", lambda: tmp_path)
    seen_folders = []
    monkeypatch.setattr(batch_schedule, "process_queue_file", lambda folder: seen_folders.append(folder) or 0)

    result = batch_schedule.run_scheduled()

    assert seen_folders == [tmp_path]
    assert result == 0


def test_run_scheduled_returns_nonzero_when_schedule_time_config_missing(monkeypatch):
    def raise_missing():
        raise batch_schedule.MissingConfigError("not configured")

    monkeypatch.setattr(batch_schedule, "load_schedule_time", raise_missing)

    assert batch_schedule.run_scheduled() == 1


def test_run_scheduled_returns_nonzero_when_cloud_folder_config_missing(monkeypatch):
    monkeypatch.setattr(batch_schedule, "load_schedule_time", lambda: "03:00:00")
    monkeypatch.setattr(batch_schedule, "query_task", lambda: {"Start Time": "3:00:00 AM"})

    def raise_missing():
        raise batch_schedule.MissingConfigError("not configured")

    monkeypatch.setattr(batch_schedule, "load_cloud_folder", raise_missing)

    assert batch_schedule.run_scheduled() == 1


def test_run_scheduled_returns_nonzero_when_cloud_folder_not_accessible(tmp_path, monkeypatch):
    monkeypatch.setattr(batch_schedule, "load_schedule_time", lambda: "03:00:00")
    monkeypatch.setattr(batch_schedule, "query_task", lambda: {"Start Time": "3:00:00 AM"})
    monkeypatch.setattr(batch_schedule, "load_cloud_folder", lambda: tmp_path / "not-mounted")

    assert batch_schedule.run_scheduled() == 1


def test_run_scheduled_handles_task_not_yet_registered(tmp_path, monkeypatch):
    monkeypatch.setattr(batch_schedule, "load_schedule_time", lambda: "03:00:00")
    monkeypatch.setattr(batch_schedule, "query_task", lambda: None)
    sync_calls = []
    monkeypatch.setattr(batch_schedule, "create_or_update_task", lambda t: sync_calls.append(t))
    monkeypatch.setattr(batch_schedule, "load_cloud_folder", lambda: tmp_path)
    monkeypatch.setattr(batch_schedule, "process_queue_file", lambda folder: 0)

    result = batch_schedule.run_scheduled()

    assert sync_calls == []  # nothing to compare against - just proceed
    assert result == 0


# --- main ---


def test_main_default_calls_register(monkeypatch):
    calls = []
    monkeypatch.setattr(batch_schedule, "register", lambda: calls.append(True))

    batch_schedule.main([])

    assert calls == [True]


def test_main_status_flag_calls_status(monkeypatch):
    calls = []
    monkeypatch.setattr(batch_schedule, "status", lambda: calls.append(True))

    batch_schedule.main(["--status"])

    assert calls == [True]


def test_main_uninstall_flag_calls_uninstall(monkeypatch):
    calls = []
    monkeypatch.setattr(batch_schedule, "uninstall", lambda: calls.append(True))

    batch_schedule.main(["--uninstall"])

    assert calls == [True]


def test_main_run_flag_calls_run_scheduled_and_exits_with_its_code(monkeypatch):
    monkeypatch.setattr(batch_schedule, "run_scheduled", lambda: 7)

    with pytest.raises(SystemExit) as exc_info:
        batch_schedule.main(["--run"])

    assert exc_info.value.code == 7


def test_main_rejects_combining_status_and_uninstall():
    with pytest.raises(SystemExit) as exc_info:
        batch_schedule.main(["--status", "--uninstall"])

    assert exc_info.value.code == 2
