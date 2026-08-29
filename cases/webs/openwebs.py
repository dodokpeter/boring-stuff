#! python3
# openwebs - open a batch of your usual sites in the browser, grouped by tag.
#   openwebs          open every group
#   openwebs <tag>    open only that group (multiple tags may be given)
#
# Configuration (in ~/.boring-stuff/BoringStuff.yml) - optional, replaces the
# built-in default groups below entirely when present:
#   openwebs:
#     init:
#       - https://mail.google.com
#       - https://calendar.google.com
#     s:
#       - https://facebook.com

import argparse
import webbrowser

from core.configuration.user_conf import load_config

DEFAULT_GROUPS = {
    "init": [
        "https://mail.google.com",
        "https://calendar.google.com",
        "https://translate.google.com",
    ],
    "s": [
        "https://facebook.com",
        "https://twitter.com",
        "https://linkedin.com",
        "https://pinterest.com",
        "https://azet.sk",
    ],
    "n": [
        "https://hnonline.sk",
        "https://aktuality.sk",
        "https://sport.aktuality.sk",
    ],
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Open a batch of your usual sites in the browser")
    parser.add_argument("tags", nargs="*", help="only open these groups (default: every group)")
    args = parser.parse_args(argv)

    config = load_config(None)
    groups = config.get("openwebs") or DEFAULT_GROUPS

    tags = args.tags or list(groups)
    for tag in tags:
        for url in groups.get(tag, []):
            webbrowser.open(url)


if __name__ == "__main__":
    main()
