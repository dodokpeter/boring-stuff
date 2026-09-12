#! python3
# joinfiles - join every .m4a file in a folder into one, in filename order.
#
# joinfiles <folder>
#
# Dispatches on file type - only .m4a is supported for now, joined via
# ffmpeg's concat demuxer with stream copy (no re-encoding). That's fast
# and lossless but requires all inputs to share a compatible
# codec/sample rate/channel layout; if they don't, ffmpeg's own error is
# what you see - there's no automatic re-encoding fallback. See issue #64
# for other choices considered and explicitly deferred.

import argparse
import subprocess
import tempfile
from pathlib import Path

from core.stats import record_usage

# ffmpeg on system path - see mp4to3.py for setup notes.

OUTPUT_NAME = "joined.m4a"


def find_input_files(folder):
    """Every .m4a file directly in `folder`, alphabetical by filename,
    excluding a previous run's own output - so re-running joinfiles on the
    same folder doesn't fold last run's joined.m4a back into the next
    one."""
    return sorted((f for f in folder.glob("*.m4a") if f.name != OUTPUT_NAME), key=lambda f: f.name)


def escape_concat_path(path):
    """Escape a path for ffmpeg's concat-list single-quoted format."""
    return str(path.resolve()).replace("'", "'\\''")


def write_concat_list(files, list_path):
    lines = [f"file '{escape_concat_path(f)}'" for f in files]
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def join_files(files, output_path):
    """Concatenate `files` into `output_path` via ffmpeg's concat demuxer
    with stream copy (-c copy)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        list_path = Path(tmp.name)
    try:
        write_concat_list(files, list_path)
        subprocess.run(
            ["ffmpeg", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "copy", "-y", str(output_path)],
            check=True,
        )
    finally:
        list_path.unlink(missing_ok=True)


def main(argv=None):
    record_usage("joinfiles")
    parser = argparse.ArgumentParser(description="Join every .m4a file in a folder into one")
    parser.add_argument("path", nargs="+", help="a folder containing .m4a files")
    args = parser.parse_args(argv)
    folder = Path(" ".join(args.path))

    if not folder.is_dir():
        print(f"'{folder}' is not a folder.")
        return

    files = find_input_files(folder)
    if len(files) < 2:
        print(f"Found {len(files)} .m4a file(s) in '{folder}' - need at least 2 to join.")
        return

    output_path = folder / OUTPUT_NAME
    for f in files:
        print(f.name)
    join_files(files, output_path)
    print(f"Joined {len(files)} files into {output_path}")


if __name__ == "__main__":
    main()
