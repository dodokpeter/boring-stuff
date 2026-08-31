#! python3
# Choose one random picture from Pinterest board

import random
import sys
import webbrowser
from xml.parsers.expat import ExpatError

import requests
import xmltodict

from core.configuration.user_conf import MissingConfigError, load_config_value
from core.stats import record_usage


def main():
    record_usage("pinterest")
    try:
        url = load_config_value(None, "Pinterest board RSS URL", None, "pinterest", "randomBoard")
    except MissingConfigError as e:
        print(e)
        sys.exit(1)

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch the Pinterest board RSS feed: {e}")
        sys.exit(1)

    try:
        doc = xmltodict.parse(response.content)
    except ExpatError as e:
        print(f"Pinterest board RSS feed is not valid XML: {e}")
        sys.exit(1)

    items = doc["rss"]["channel"]["item"]
    if isinstance(items, dict):
        # xmltodict parses a single <item> as a dict rather than a list
        items = [items]
    picture = random.choice(items)
    print(picture)
    webbrowser.open(picture["link"])


if __name__ == "__main__":
    main()
