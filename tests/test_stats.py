from datetime import date, datetime

from core import stats


def test_usage_file_path_creates_boring_stuff_dir(tmp_path):
    path = stats.usage_file_path()

    assert path == tmp_path / ".boring-stuff" / "usage.jsonl"
    assert path.parent.is_dir()


def test_week_start_returns_monday_of_the_week():
    # 2026-08-31 is a Monday
    assert stats.week_start(datetime(2026, 9, 2)) == date(2026, 8, 31)


def test_week_start_accepts_a_date_directly():
    assert stats.week_start(date(2026, 9, 2)) == date(2026, 8, 31)


def test_week_start_on_a_monday_returns_itself():
    assert stats.week_start(datetime(2026, 8, 31)) == date(2026, 8, 31)


def test_record_usage_appends_an_entry():
    stats.record_usage("background")

    entries = stats.read_usage_entries()
    assert len(entries) == 1
    assert entries[0][0] == "background"


def test_record_usage_appends_multiple_calls():
    stats.record_usage("background")
    stats.record_usage("clipsave")
    stats.record_usage("background")

    entries = stats.read_usage_entries()
    assert [command for command, _ts in entries] == ["background", "clipsave", "background"]


def test_record_usage_never_raises_when_write_fails(monkeypatch):
    def raise_error():
        raise OSError("disk full")

    monkeypatch.setattr(stats, "write_usage_entries", raise_error)

    stats.record_usage("background")  # must not raise


def test_read_usage_entries_returns_empty_list_when_file_missing():
    assert stats.read_usage_entries() == []


def test_read_usage_entries_skips_malformed_lines():
    path = stats.usage_file_path()
    path.write_text(
        '{"command": "background", "timestamp": "2026-08-31T10:00:00"}\n'
        "not even json\n"
        '{"command": "clipsave"}\n'  # missing timestamp
        '{"timestamp": "2026-08-31T11:00:00"}\n'  # missing command
        "\n"
        '{"command": "clipsave", "timestamp": "not-a-date"}\n',
        encoding="utf-8",
    )

    entries = stats.read_usage_entries()
    assert [command for command, _ts in entries] == ["background"]


def test_write_usage_entries_round_trips_through_read(tmp_path):
    entries = [("background", datetime(2026, 8, 31, 10, 0, 0)), ("clipsave", datetime(2026, 8, 31, 11, 0, 0))]

    stats.write_usage_entries(entries)

    assert stats.read_usage_entries() == entries


def test_prune_old_entries_drops_entries_older_than_retention_window():
    now = datetime(2026, 9, 2)  # week of 2026-08-31
    too_old = datetime(2026, 8, 31) - stats.timedelta(weeks=stats.RETENTION_WEEKS)  # one week before the cutoff
    just_inside = stats.week_start(now) - stats.timedelta(weeks=stats.RETENTION_WEEKS - 1)

    entries = [
        ("old", too_old),
        ("kept", datetime.combine(just_inside, datetime.min.time())),
        ("current", now),
    ]

    pruned = stats.prune_old_entries(entries, now)

    assert [command for command, _ts in pruned] == ["kept", "current"]


def test_record_usage_prunes_old_entries_on_write(monkeypatch):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 2)  # week of 2026-08-31

    monkeypatch.setattr(stats, "datetime", FixedDateTime)

    old_entry_time = FixedDateTime(2026, 1, 1)
    stats.write_usage_entries([("ancient", old_entry_time)])

    stats.record_usage("background")

    entries = stats.read_usage_entries()
    assert [command for command, _ts in entries] == ["background"]


def test_count_by_command():
    entries = [
        ("background", datetime(2026, 8, 31)),
        ("clipsave", datetime(2026, 8, 31)),
        ("background", datetime(2026, 8, 31)),
    ]

    assert stats.count_by_command(entries) == {"background": 2, "clipsave": 1}


def test_top_commands_sorts_by_count_desc_then_name_asc():
    entries = [
        ("clipsave", datetime(2026, 8, 31)),
        ("background", datetime(2026, 8, 31)),
        ("background", datetime(2026, 8, 31)),
        ("email-extract", datetime(2026, 8, 31)),
        ("clipsave", datetime(2026, 8, 31)),
    ]

    assert stats.top_commands(entries) == [("background", 2), ("clipsave", 2), ("email-extract", 1)]


def test_top_commands_respects_limit():
    entries = [("background", datetime(2026, 8, 31)), ("clipsave", datetime(2026, 8, 31))]

    assert stats.top_commands(entries, limit=1) == [("background", 1)]


def test_group_by_week():
    entries = [
        ("background", datetime(2026, 8, 31)),  # Monday, week of 2026-08-31
        ("clipsave", datetime(2026, 9, 2)),  # Wednesday, same week
        ("background", datetime(2026, 8, 24)),  # previous week
    ]

    groups = stats.group_by_week(entries)

    assert set(groups.keys()) == {date(2026, 8, 31), date(2026, 8, 24)}
    assert len(groups[date(2026, 8, 31)]) == 2
    assert len(groups[date(2026, 8, 24)]) == 1
