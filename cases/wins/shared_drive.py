#! python3
# shared-drive - work inside a shared/synced drive folder (e.g. Google Drive
# for Desktop) as a plain local filesystem path - no API/OAuth needed since
# the desktop sync client already mounts it as a real directory.
#
# First version: makes sure a "boring-stuff" folder exists directly under
# the configured shared-drive root, creating it if it isn't there yet.
#
# Configuration (in ~/.boring-stuff/BoringStuff.yml):
#   drive:
#     directory:
#       boring-stuff: G:\.shortcut-targets-by-id\<id>

import sys
from pathlib import Path

from core.configuration.user_conf import MissingConfigError, load_config_value

BORING_STUFF_FOLDER_NAME = "boring-stuff"


def validate_shared_drive_directory(value):
    """Raise ValueError with a clear message if `value` isn't an accessible
    directory - used to reject a bad answer before it gets persisted to
    config."""
    if not Path(value).is_dir():
        raise ValueError(f"'{value}' is not an accessible directory.")


def ensure_boring_stuff_folder(root):
    """Make sure a 'boring-stuff' subfolder exists directly under `root`,
    creating it if needed. Returns (path, created)."""
    target = root / BORING_STUFF_FOLDER_NAME
    if target.is_dir():
        return target, False
    target.mkdir()
    return target, True


def main():
    try:
        directory = load_config_value(
            None,
            "Shared Drive root folder (e.g. your Google Drive mount path)",
            None,
            "drive",
            "directory",
            "boring-stuff",
            validate=validate_shared_drive_directory,
        )
    except MissingConfigError as e:
        print(e)
        sys.exit(1)

    root = Path(directory)
    if not root.is_dir():
        print(f"Configured shared Drive folder is not accessible: {root}")
        sys.exit(1)

    target, created = ensure_boring_stuff_folder(root)
    if created:
        print(f"Created folder: {target}")
    else:
        print(f"Folder already exists: {target}")


if __name__ == "__main__":
    main()
