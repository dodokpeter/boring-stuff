#! python3
# makezip - zip a folder and everything in it into a timestamped archive,
# saved next to the folder (in its parent directory).
#
# makezip <folder>   zip <folder> into <parent>\<name>_yyyy_mm_dd___HH_mm_ss.zip
# makezip            same, for the current working directory
#
# The folder itself is the zip's top-level entry (same layout clipsave
# makes for a copied folder), so extracting gives back a "<name>\..."
# folder instead of spilling loose files. The archive lands in the parent,
# so it can never try to include itself. The folder being zipped is never
# modified - the only effect is one new .zip beside it. An existing file
# of the same name is never overwritten (a "(1)", "(2)", ... suffix is
# added, same as clipsave/move-to). See issue #71.

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from core.files import unique_path
from core.stats import record_usage

TIMESTAMP_FORMAT = "%Y_%m_%d___%H_%M_%S"


def archive_path_for(folder, now):
    return unique_path(folder.parent / f"{folder.name}_{now.strftime(TIMESTAMP_FORMAT)}.zip")


def format_size(size_bytes):
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024


def make_zip(folder, now=None):
    """Zip `folder` into a timestamped archive in its parent directory and
    return the archive's path."""
    target = archive_path_for(folder, now or datetime.now())
    archive_base = target.with_suffix("")
    return Path(shutil.make_archive(str(archive_base), "zip", root_dir=folder.parent, base_dir=folder.name))


def main(argv=None):
    record_usage("makezip")
    parser = argparse.ArgumentParser(description="Zip a folder into a timestamped archive beside it")
    parser.add_argument("path", nargs="*", help="the folder to zip (default: the current directory)")
    args = parser.parse_args(argv)
    folder = Path(" ".join(args.path)).resolve() if args.path else Path.cwd()

    if not folder.exists():
        print(f"'{folder}' does not exist.")
        sys.exit(1)
    if not folder.is_dir():
        print(f"'{folder}' is not a folder.")
        sys.exit(1)
    if folder.parent == folder:
        print(f"'{folder}' is a drive root - there is no parent folder to write the zip into.")
        sys.exit(1)

    print(f"Zipping {folder} ...")
    archive = make_zip(folder)
    print(f"Created: {archive}")
    print(f"Size: {format_size(archive.stat().st_size)}")


if __name__ == "__main__":
    main()
