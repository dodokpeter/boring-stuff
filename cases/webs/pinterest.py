#! python3
# Choose one random picture from Pinterest board

import random
import sys
import webbrowser

import requests
import xmltodict

from core.configuration.user_conf import MissingConfigError, load_config_value


def main():
    try:
        url = load_config_value(None, "Pinterest board RSS URL", None, "pinterest", "randomBoard")
    except MissingConfigError as e:
        print(e)
        sys.exit(1)

    response = requests.get(url, "xml")
    response.raise_for_status()

    # xml response parse it
    doc = xmltodict.parse(response.content)
    items = doc["rss"]["channel"]["item"]
    if isinstance(items, dict):
        # xmltodict parses a single <item> as a dict rather than a list
        items = [items]
    picture = random.choice(items)
    print(picture)
    webbrowser.open(picture["link"])


if __name__ == "__main__":
    main()
