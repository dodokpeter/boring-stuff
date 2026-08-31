#! python3
# move-to - move a file or folder to a cloud-synced destination:
#   move-to -s <path>   move to <cloud.folder>/<cloud.share>
#   move-to -o <path>   move to <cloud.folder>/<cloud.output>
#
# No Google Drive API/OAuth - cloud.folder is a plain local path (typically
# a Google Drive for Desktop mount); whatever sync client is watching it
# picks up the move on its own. A name collision at the destination gets a
# "(1)", "(2)", ... suffix, same as clipsave/email-extract.
#
# Configuration (in ~/.boring-stuff/BoringStuff.yml) - prompted for and
# saved automatically on first run if missing:
#   cloud:
#     folder: G:\.shortcut-targets-by-id\<id>\Dodo\boring-stuff
#     share: share
#     output: output

import argparse
import shutil
import sys
from pathlib import Path

from core.cloud import (
    DEFAULT_OUTPUT_SUBFOLDER_NAME,
    DEFAULT_SHARE_SUBFOLDER_NAME,
    load_cloud_folder,
    load_cloud_subfolder_name,
)
from core.configuration.user_conf import MissingConfigError
from core.files import unique_path
from core.stats import record_usage


def move_path(source, destination_root):
    """Move `source` (file or folder) into destination_root, avoiding a
    name collision at the destination. Returns the final destination
    path."""
    destination_root.mkdir(parents=True, exist_ok=True)
    target = unique_path(destination_root / source.name)
    shutil.move(str(source), str(target))
    return target


def main(argv=None):
    record_usage("move-to")
    parser = argparse.ArgumentParser(description="Move a file or folder to a cloud-synced destination")
    parser.add_argument("path", nargs="+", help="file or folder to move")
    destination_group = parser.add_mutually_exclusive_group(required=True)
    destination_group.add_argument("-s", "--share", action="store_true", help="move to <cloud.folder>/<cloud.share>")
    destination_group.add_argument("-o", "--output", action="store_true", help="move to <cloud.folder>/<cloud.output>")
    args = parser.parse_args(argv)

    source = Path(" ".join(args.path))
    if not source.exists():
        print(f"'{source}' does not exist.")
        sys.exit(1)

    if args.share:
        key, default = "share", DEFAULT_SHARE_SUBFOLDER_NAME
    else:
        key, default = "output", DEFAULT_OUTPUT_SUBFOLDER_NAME

    try:
        cloud_folder = load_cloud_folder()
        subfolder_name = load_cloud_subfolder_name(key, default)
    except MissingConfigError as e:
        print(e)
        sys.exit(1)

    if not cloud_folder.is_dir():
        print(f"Configured cloud folder is not accessible: {cloud_folder}")
        sys.exit(1)

    destination = move_path(source, cloud_folder / subfolder_name)
    print(f"Moved to: {destination}")


if __name__ == "__main__":
    main()
