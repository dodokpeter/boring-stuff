#! python3
# Choose one random picture from Pinterest board

import requests
import random
import xmltodict
import webbrowser
import configparser
from pathlib import Path


def main():
    home = str(Path.home())
    Config = configparser.ConfigParser()
    Config.read(str(Path(home) / 'BoringStuff.ini'))

    #obtain url of pinterest board
    url = Config.get('Pinterest','RandomBoard')
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

