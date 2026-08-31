#! python3
# shared-drive - make sure the configured cloud "share" folder exists,
# creating it if it isn't there yet. Works as a plain filesystem path - no
# API/OAuth needed since the desktop sync client already mounts it as a
# real directory.
#
# Configuration (in ~/.boring-stuff/BoringStuff.yml) - prompted for and
# saved automatically on first run if missing:
#   cloud:
#     folder: G:\.shortcut-targets-by-id\<id>\Dodo\boring-stuff
#     share: share

import sys

from core.cloud import DEFAULT_SHARE_SUBFOLDER_NAME, load_cloud_folder, load_cloud_subfolder_name
from core.configuration.user_conf import MissingConfigError
from core.stats import record_usage


def ensure_share_folder(cloud_folder, share_subfolder_name):
    """Make sure `share_subfolder_name` exists directly under `cloud_folder`,
    creating it if needed. Returns (path, created)."""
    target = cloud_folder / share_subfolder_name
    if target.is_dir():
        return target, False
    target.mkdir(parents=True)
    return target, True


def main():
    record_usage("shared-drive")
    try:
        cloud_folder = load_cloud_folder()
        share_subfolder_name = load_cloud_subfolder_name("share", DEFAULT_SHARE_SUBFOLDER_NAME)
    except MissingConfigError as e:
        print(e)
        sys.exit(1)

    if not cloud_folder.is_dir():
        print(f"Configured cloud folder is not accessible: {cloud_folder}")
        sys.exit(1)

    target, created = ensure_share_folder(cloud_folder, share_subfolder_name)
    if created:
        print(f"Created folder: {target}")
    else:
        print(f"Folder already exists: {target}")


if __name__ == "__main__":
    main()
