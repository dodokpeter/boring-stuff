# Records and aggregates per-command usage, one JSON line per invocation,
# in ~/.boring-stuff/usage.jsonl. Every registered boring-stuff command
# calls record_usage() near the top of its main() - see issue #52.
#
# Retention: record_usage() prunes anything older than RETENTION_WEEKS
# calendar weeks on every call, so the file stays self-bounded without a
# separate scheduled/background process (this repo has none of its own).

import json
from datetime import datetime, timedelta
from pathlib import Path

USAGE_FILE_NAME = "usage.jsonl"
RETENTION_WEEKS = 10


def usage_file_path():
    directory = Path.home() / ".boring-stuff"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / USAGE_FILE_NAME


def week_start(dt):
    """The Monday (a date, not a datetime) of dt's calendar week."""
    day = dt.date() if isinstance(dt, datetime) else dt
    return day - timedelta(days=day.weekday())


def read_usage_entries():
    """Return [(command, datetime), ...] from usage.jsonl, oldest first.
    Malformed lines are skipped rather than raising - a corrupted usage
    log must never take down the `stats` command."""
    path = usage_file_path()
    if not path.is_file():
        return []

    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            entries.append((record["command"], datetime.fromisoformat(record["timestamp"])))
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    return entries


def write_usage_entries(entries):
    path = usage_file_path()
    lines = [json.dumps({"command": command, "timestamp": timestamp.isoformat()}) for command, timestamp in entries]
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")


def prune_old_entries(entries, now=None):
    """Keep only entries from the last RETENTION_WEEKS calendar weeks,
    counting the week `now` falls in as one of them."""
    now = now or datetime.now()
    cutoff = week_start(now) - timedelta(weeks=RETENTION_WEEKS - 1)
    return [entry for entry in entries if entry[1].date() >= cutoff]


def record_usage(command_name):
    """Record one invocation of `command_name`. Best-effort: any failure
    (disk full, permissions, a corrupted existing file, ...) is swallowed
    so usage tracking can never break the command actually being run."""
    try:
        now = datetime.now()
        entries = read_usage_entries()
        entries.append((command_name, now))
        entries = prune_old_entries(entries, now)
        write_usage_entries(entries)
    except Exception:  # noqa: BLE001 - tracking must never break the real command
        pass


def count_by_command(entries):
    counts = {}
    for command, _timestamp in entries:
        counts[command] = counts.get(command, 0) + 1
    return counts


def top_commands(entries, limit=None):
    """[(command, count), ...] sorted by count desc, then name asc."""
    ranked = sorted(count_by_command(entries).items(), key=lambda item: (-item[1], item[0]))
    return ranked[:limit] if limit else ranked


def group_by_week(entries):
    """{week_start_date: [(command, datetime), ...]}."""
    groups = {}
    for command, timestamp in entries:
        groups.setdefault(week_start(timestamp), []).append((command, timestamp))
    return groups
