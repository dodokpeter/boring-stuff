#! python3
# Choose one random picture from Pinterest board

import random
import webbrowser

import requests
import xmltodict

from core.configuration.user_conf import load_config


def main():
    config = load_config(None)

    # obtain url of pinterest board
    url = config["pinterest"]["randomBoard"]
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
