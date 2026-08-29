#! python3
# lucky - "Feeling lucky" Google search. Opens the top N result pages.
# Falls back to opening the plain Google search results page if scraping
# gets blocked (Google/DuckDuckGo increasingly reject non-browser clients).
#
# lucky tips for developers
# lucky -n3 tips for developers

import argparse
import webbrowser
from urllib.parse import quote_plus

from googlesearch import search


def main(argv=None):
    parser = argparse.ArgumentParser(description="Open the top Google results for a search")
    parser.add_argument("-n", type=int, default=4, dest="count", help="number of result pages to open (default: 4)")
    parser.add_argument("query", nargs="+", help="search terms")
    args = parser.parse_args(argv)

    query = " ".join(args.query)
    print(f"Googling '{query}'...")

    urls = []
    try:
        urls = list(search(query, num_results=args.count))
    except Exception as e:  # noqa: BLE001 - scraping can fail in many ways; any of them should fall back, not crash
        print(f"Scraping failed ({e}), falling back to search results page.")

    if not urls:
        print("No results scraped, opening search results page instead.")
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
        return

    for url in urls:
        webbrowser.open(url)


if __name__ == "__main__":
    main()
