from datetime import datetime

from cases.devs import stats as stats_cmd
from core import stats


def test_format_report_says_no_usage_when_empty():
    assert "No usage recorded yet." in stats_cmd.format_report([])


def test_format_report_lists_overall_and_weekly_breakdown():
    entries = [
        ("background", datetime(2026, 8, 31)),  # Monday, week of 2026-08-31
        ("background", datetime(2026, 9, 2)),  # same week
        ("clipsave", datetime(2026, 8, 24)),  # previous week
    ]

    report = stats_cmd.format_report(entries)

    assert "Overall usage (last 10 weeks):" in report
    assert "background  2" in report
    assert "clipsave  1" in report
    assert "Week of 2026-08-31:" in report
    assert "Week of 2026-08-24:" in report


def test_format_report_orders_weeks_most_recent_first():
    entries = [
        ("background", datetime(2026, 8, 17)),
        ("clipsave", datetime(2026, 8, 31)),
    ]

    report = stats_cmd.format_report(entries)

    assert report.index("Week of 2026-08-31") < report.index("Week of 2026-08-17")


def test_main_prints_report_and_records_its_own_usage(capsys):
    stats_cmd.main()

    out = capsys.readouterr().out
    assert "Overall usage (last 10 weeks):" in out
    assert "stats  1" in out  # main() recorded its own invocation before reading

    entries = stats.read_usage_entries()
    assert entries == [("stats", entries[0][1])]
