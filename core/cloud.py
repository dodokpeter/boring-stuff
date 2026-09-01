# Shared helpers for resolving a cloud-synced destination, used by
# shared-drive, move-to, and yt's -c flag. No Google Drive API/OAuth -
# cloud.folder is just a plain local path (typically a Google Drive for
# Desktop mount); whatever sync client is watching it picks up changes on
# its own.

from pathlib import Path

from core.configuration.user_conf import load_config_value

DEFAULT_SHARE_SUBFOLDER_NAME = "share"
DEFAULT_OUTPUT_SUBFOLDER_NAME = "output"


def validate_cloud_folder(value):
    """Raise ValueError with a clear message if `value` isn't an accessible
    directory - used to reject a bad answer before it gets persisted to
    config."""
    if not Path(value).is_dir():
        raise ValueError(f"'{value}' is not an accessible directory.")


def load_cloud_folder():
    """Prompt for (and persist) cloud.folder - required, no default."""
    return Path(
        load_config_value(
            None,
            "Cloud folder root (e.g. your Google Drive mount path)",
            None,
            "cloud",
            "folder",
            validate=validate_cloud_folder,
        )
    )


def load_cloud_subfolder_name(key, default):
    """Prompt for (and persist) cloud.<key> - e.g. "share"/"output" - with a
    working default, so hitting Enter just accepts it."""
    return load_config_value(None, f"Cloud '{key}' subfolder name", default, "cloud", key)
