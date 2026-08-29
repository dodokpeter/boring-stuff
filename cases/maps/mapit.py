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
        address = root.clipboard_get()

    webbrowser.open('https://www.google.com/maps/place/' + quote(address))


if __name__ == "__main__":
    main()
