#! python3
# stats - print how often each boring-stuff command has been used, overall
# and broken down by calendar week (Monday-Sunday), from the usage data
# recorded in ~/.boring-stuff/usage.jsonl (last 10 weeks, see core/stats.py).
#
# Run command:
#   stats

from core.stats import group_by_week, read_usage_entries, record_usage, top_commands


def format_ranked(ranked):
    width = max(len(command) for command, _count in ranked)
    return [f"  {command.ljust(width)}  {count}" for command, count in ranked]


def format_report(entries):
    lines = ["Overall usage (last 10 weeks):"]
    overall = top_commands(entries)
    if not overall:
        lines.append("  No usage recorded yet.")
    else:
        lines.extend(format_ranked(overall))

    weeks = group_by_week(entries)
    for week in sorted(weeks, reverse=True):
        lines.append("")
        lines.append(f"Week of {week.isoformat()}:")
        lines.extend(format_ranked(top_commands(weeks[week])))

    return "\n".join(lines)


def main():
    record_usage("stats")
    print(format_report(read_usage_entries()))


if __name__ == "__main__":
    main()
