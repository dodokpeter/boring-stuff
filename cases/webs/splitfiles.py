#! python3
# splitfiles - split a large file into ~N-minute parts, dispatching on file
# type. The counterpart of joinfiles: it produces the pieces joinfiles can
# put back together.
#
# splitfiles <file>          prompt for the part length, then split
# splitfiles <file> -m 45    split into 45-minute parts, no prompt
#
# Only .mp4 is registered for now (SPLITTERS below) - any other extension
# prints a clear "unsupported file type" message and exits non-zero.
# Adding a new type later means adding one handler to SPLITTERS, not
# reworking main().
#
# mp4 is split via ffmpeg's segment muxer with stream copy (-c copy) - no
# re-encoding, so even a very large file splits in seconds with zero
# quality loss. The trade-off, accepted: stream copy can only cut on
# keyframes, so each part is the requested length +/- a few seconds, not
# frame-exact.
#
# Cut points are computed up front from the real duration (read via
# ffprobe) and handed to the segment muxer via -segment_times, rather than
# using a fixed -segment_time and fixing up a short trailing part
# afterwards - see plan_parts() for the "no tiny trailing part" rule: a
# remainder under MIN_PART_MINUTES is folded into the previous part
# instead of becoming its own file.

import argparse
import subprocess
import sys
from pathlib import Path

from core.configuration.user_conf import load_config
from core.stats import record_usage

DEFAULT_MINUTES = 30
MIN_PART_MINUTES = 5


def load_default_minutes():
    """splitfiles.minutes is an optional preference (like openwebs's
    groups) - a missing key just falls back to DEFAULT_MINUTES instead of
    being prompted for and persisted."""
    config = load_config(None)
    return config.get("splitfiles", {}).get("minutes", DEFAULT_MINUTES)


def prompt_for_minutes(default_minutes):
    while True:
        answer = input(f"Part length in minutes [{default_minutes}]: ").strip()
        if not answer:
            return default_minutes
        try:
            minutes = int(answer)
        except ValueError:
            minutes = 0
        if minutes > 0:
            return minutes
        print("Enter a positive whole number of minutes.")


def format_duration(seconds):
    """Round to the nearest whole minute, half up - plain round() uses
    banker's rounding, which would display a real 2:30 file as "2m"
    instead of "3m" (found for real while manually verifying against an
    actual video)."""
    whole_minutes, leftover_seconds = divmod(seconds, 60)
    total_minutes = int(whole_minutes) + (1 if leftover_seconds >= 30 else 0)
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def get_duration_seconds(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def plan_parts(duration_seconds, minutes):
    """The length (in seconds) of every part, in order - or [] if the file
    is already short enough that nothing needs splitting. Every part but
    the last is exactly `minutes` long; a remainder under MIN_PART_MINUTES
    is folded into the last part instead of becoming its own tiny file
    (see the module docstring)."""
    length = minutes * 60
    min_part = MIN_PART_MINUTES * 60
    full_parts = int(duration_seconds // length)
    if full_parts == 0:
        return []

    remainder = duration_seconds - full_parts * length
    if remainder >= min_part:
        parts = [length] * full_parts + [remainder]
    else:
        parts = [length] * (full_parts - 1) + [length + remainder]

    return parts if len(parts) > 1 else []


def run_ffmpeg_segment(path, cut_points, output_pattern):
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(path),
            "-map",
            "0",
            "-c",
            "copy",
            "-f",
            "segment",
            "-segment_times",
            ",".join(str(round(cut_point)) for cut_point in cut_points),
            "-reset_timestamps",
            "1",
            "-segment_start_number",
            "1",
            str(output_pattern),
        ],
        check=True,
    )


def split_mp4(path, minutes):
    duration = get_duration_seconds(path)
    parts = plan_parts(duration, minutes)

    if not parts:
        print(f"{path.name} - {format_duration(duration)} - nothing to split.")
        return

    cut_points = [sum(parts[:i]) for i in range(1, len(parts))]
    print(
        f"{path.name} - {format_duration(duration)} -> {len(parts)} parts of {minutes} min "
        f"(last part {format_duration(parts[-1])})"
    )

    output_dir = path.parent / f"{path.stem} - parts"
    output_dir.mkdir(exist_ok=True)
    output_pattern = output_dir / f"{path.stem} - part %02d{path.suffix}"
    run_ffmpeg_segment(path, cut_points, output_pattern)
    print(f"Wrote {len(parts)} parts into {output_dir}")


SPLITTERS = {".mp4": split_mp4}


def main(argv=None):
    record_usage("splitfiles")
    parser = argparse.ArgumentParser(description="Split a large file into shorter parts, dispatching on file type")
    parser.add_argument("path", nargs="+", help="the file to split")
    parser.add_argument("-m", "--minutes", type=int, help="part length in minutes - skips the prompt")
    args = parser.parse_args(argv)
    path = Path(" ".join(args.path))

    if not path.is_file():
        print(f"'{path}' is not a file.")
        sys.exit(1)

    splitter = SPLITTERS.get(path.suffix.lower())
    if splitter is None:
        supported = ", ".join(sorted(SPLITTERS))
        print(f"Unsupported file type '{path.suffix}' - splitfiles supports: {supported}")
        sys.exit(1)

    if args.minutes is not None and args.minutes <= 0:
        print("Minutes must be a positive whole number.")
        sys.exit(1)

    minutes = args.minutes if args.minutes is not None else prompt_for_minutes(load_default_minutes())
    splitter(path, minutes)


if __name__ == "__main__":
    main()
