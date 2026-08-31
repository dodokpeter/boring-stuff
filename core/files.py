# Shared filesystem helpers used across multiple commands.


def unique_path(path):
    """Return `path` if it's free, otherwise the first "<stem> (N)<suffix>"
    variant that's free - same collision-avoidance scheme used by
    clipsave, email-extract, and move-to."""
    if not path.exists():
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1
