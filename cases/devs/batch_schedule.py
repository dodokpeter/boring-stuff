#! python3
# batch-schedule - opt-in daily scheduler for `batch`, via a Windows
# Scheduled Task. Nothing is scheduled until this is run explicitly - no
# default task, and uv sync/setup.ps1 never register one.
#
# batch-schedule              register (or refresh) the daily task
# batch-schedule --status     show whether the task exists, its current
#                              trigger, the configured time, and its next
#                              run
# batch-schedule --uninstall  remove the task
#
# The registered task's action runs THIS SAME script with --run (via
# pythonw.exe, not the batch.exe console shim, so a 3 AM run never flashes
# a console window). --run mode re-reads batch.scheduleTime, re-registers
# the task if that time has drifted from the task's actual trigger, then
# runs the batch queue in-process (calling into batch.py directly, not as
# a subprocess).
#
# Trigger updates always go through a full /Create ... /F (recreate), not
# /Change - schtasks /Change /ST was found to prompt interactively for the
# run-as password (confirmed on this machine), which would hang forever in
# an unattended 3 AM run with no terminal attached. /Create /F does not
# prompt and updates the existing task in place.
#
# If the machine is off/asleep at the scheduled time, that day's run is
# simply skipped - no wake, no catch-up run. Runs "only when logged on"
# (schtasks' default when no password is supplied) - no Windows password
# is ever stored by this script.
#
# Configuration (in ~/.boring-stuff/BoringStuff.yml) - prompted for and
# saved automatically on first use:
#   batch:
#     scheduleTime: "03:00:00"
#
# Seconds must be "00": Windows Task Scheduler only has minute-level
# precision - schtasks /ST silently truncates any other seconds value
# (confirmed for real: /ST 06:15:45 registered as 6:15:00 AM), which would
# otherwise never match what query_task() reads back and cause the
# trigger-sync in run_scheduled() to "fix" the task on every single run.

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from cases.devs.batch import process_queue_file
from core.cloud import load_cloud_folder
from core.configuration.user_conf import MissingConfigError, load_config_value

TASK_NAME = "BoringStuffBatch"
DEFAULT_SCHEDULE_TIME = "03:00:00"
SCRIPT_PATH = Path(__file__).resolve()
PYTHONW_PATH = Path(sys.executable).resolve().with_name("pythonw.exe")

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d):00$")


def validate_schedule_time(value):
    """Raise ValueError unless `value` is a 24-hour HH:MM:00 string -
    seconds must be "00" (see module docstring) - used to reject a bad
    answer before it gets persisted to config or handed to schtasks."""
    if not TIME_PATTERN.match(value):
        raise ValueError(
            f"'{value}' must be 24-hour HH:MM:SS with seconds \"00\" "
            "(e.g. 03:00:00 or 21:00:00) - Windows Task Scheduler has no finer precision."
        )


def load_schedule_time():
    return load_config_value(
        None,
        "Daily batch time (HH:MM:SS)",
        DEFAULT_SCHEDULE_TIME,
        "batch",
        "scheduleTime",
        validate=validate_schedule_time,
    )


def task_action_command():
    return f'"{PYTHONW_PATH}" "{SCRIPT_PATH}" --run'


def create_or_update_task(schedule_time):
    """Register the task with today's schedule_time, overwriting any
    existing task of the same name - this is how both a fresh registration
    and a later time change are applied; schtasks /Create /F does not
    prompt for credentials, unlike schtasks /Change."""
    subprocess.run(
        [
            "schtasks",
            "/Create",
            "/TN",
            TASK_NAME,
            "/SC",
            "DAILY",
            "/ST",
            schedule_time,
            "/TR",
            task_action_command(),
            "/F",
        ],
        capture_output=True,
        text=True,
        check=True,
    )


def query_task():
    """Return a dict of the task's fields (from schtasks /Query /V /FO
    LIST), or None if the task doesn't exist."""
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    fields = {}
    for line in result.stdout.splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            continue
        fields[key.strip()] = value.strip()
    return fields


def delete_task():
    subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], capture_output=True, text=True)


def parse_task_start_time(fields):
    """Normalize the task's "Start Time" field (schtasks reports it as a
    12-hour "H:MM:SS AM/PM" string, e.g. "3:00:00 AM") into the same
    24-hour HH:MM:SS form batch.scheduleTime uses, so the two are directly
    comparable. Returns None if the field is missing or unparseable."""
    raw = fields.get("Start Time")
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%I:%M:%S %p").strftime("%H:%M:%S")
    except ValueError:
        return None


def register():
    try:
        cloud_folder = load_cloud_folder()
    except MissingConfigError as e:
        print(e)
        sys.exit(1)

    if not cloud_folder.is_dir():
        print(f"Configured cloud folder is not accessible: {cloud_folder}")
        sys.exit(1)

    try:
        schedule_time = load_schedule_time()
    except MissingConfigError as e:
        print(e)
        sys.exit(1)

    create_or_update_task(schedule_time)
    print(f"Registered '{TASK_NAME}' to run 'batch' daily at {schedule_time}.")


def status():
    fields = query_task()
    if fields is None:
        print(f"'{TASK_NAME}' is not registered.")
        return

    try:
        configured_time = load_schedule_time()
    except MissingConfigError as e:
        configured_time = None
        print(e)

    task_time = parse_task_start_time(fields)
    print(f"'{TASK_NAME}' is registered.")
    print(f"  Configured time (batch.scheduleTime): {configured_time or '?'}")
    print(f"  Task's current trigger time: {task_time or fields.get('Start Time', '?')}")
    if configured_time and task_time and configured_time != task_time:
        print("  These differ - the task will pick up the new time on its next run.")
    print(f"  Next run: {fields.get('Next Run Time', '?')}")


def uninstall():
    if query_task() is None:
        print(f"'{TASK_NAME}' is not registered - nothing to remove.")
        return
    delete_task()
    print(f"Removed '{TASK_NAME}'.")


def run_scheduled():
    """What the Scheduled Task's action actually runs: sync the task's
    trigger to the configured time if it's drifted, then run the batch
    queue in-process. No terminal is attached here, so any config prompt
    would just fail via MissingConfigError - caught below rather than
    propagating."""
    try:
        schedule_time = load_schedule_time()
    except MissingConfigError:
        return 1

    fields = query_task()
    if fields is not None and parse_task_start_time(fields) != schedule_time:
        create_or_update_task(schedule_time)

    try:
        cloud_folder = load_cloud_folder()
    except MissingConfigError:
        return 1

    if not cloud_folder.is_dir():
        return 1

    return process_queue_file(cloud_folder)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Opt-in daily scheduler for the batch command")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--status", action="store_true", help="show whether the task exists and when it next runs")
    group.add_argument("--uninstall", action="store_true", help="remove the scheduled task")
    group.add_argument("--run", action="store_true", help=argparse.SUPPRESS)  # internal - what the task itself runs
    args = parser.parse_args(argv)

    if args.run:
        sys.exit(run_scheduled())
    if args.status:
        status()
        return
    if args.uninstall:
        uninstall()
        return

    register()


if __name__ == "__main__":
    main()
