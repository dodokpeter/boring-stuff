#! python3

# ideas - check the defined route


import webbrowser
import sys
import tkinter as tk
from urllib.parse import quote


def main():
    if len(sys.argv) > 1:
        # Get address from command line.
        address = ' '.join(sys.argv[1:])
    else:
        root = tk.Tk()
        try:
            address = root.clipboard_get()
        except tk.TclError:
            address = ''

    address = address.strip()
    if not address:
        print("No address given and the clipboard is empty. Pass an address as an argument instead, e.g. `mapit Bratislava`.")
        return

    webbrowser.open('https://www.google.com/maps/place/' + quote(address))


if __name__ == "__main__":
    main()
