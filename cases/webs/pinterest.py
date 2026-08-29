#! python3
# Choose one random picture from Pinterest board

import requests
import random
import xmltodict
import webbrowser

from core.configuration.user_conf import load_config


def main():
    config = load_config(None)

    #obtain url of pinterest board
    url = config['pinterest']['randomBoard']
    response = requests.get(url, "xml")
    response.raise_for_status()

    #xml response parse it
    doc = xmltodict.parse(response.content)
    size = len(doc['rss']['channel']['item'])
    picture = doc['rss']['channel']['item'][random.randint(0, size)]
    print(picture)
    webbrowser.open(picture['link'])


if __name__ == "__main__":
    main()
