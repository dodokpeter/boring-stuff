#! python3
# mapit - open a Google Maps place page.
#   mapit               use the address currently on the clipboard
#   mapit <address>     use the given address

import argparse
import webbrowser
from urllib.parse import quote

import pyperclip


def main(argv=None):
    parser = argparse.ArgumentParser(description="Open a Google Maps place page")
    parser.add_argument("address", nargs="*", help="address to look up (default: the clipboard's text)")
    args = parser.parse_args(argv)

    address = " ".join(args.address) if args.address else (pyperclip.paste() or "")
    address = address.strip()
    if not address:
        print("No address given and the clipboard is empty. Pass an address as an argument instead, e.g. `mapit Bratislava`.")
        return

    webbrowser.open('https://www.google.com/maps/place/' + quote(address))


if __name__ == "__main__":
    main()
