#! python3

import webbrowser
import sys


def main():
    all = False
    if len(sys.argv) == 1:
        all = True

    if all or 'init' in sys.argv:
        webbrowser.open('https://mail.google.com')
        webbrowser.open('https://calendar.google.com')
        webbrowser.open('https://translate.google.com')

    if all or 's' in sys.argv:
        webbrowser.open('https://facebook.com')
        webbrowser.open('https://twitter.com')
        webbrowser.open('https://linkedin.com')
        webbrowser.open('https://pinterest.com')
        webbrowser.open('https://azet.sk')

    if all or 'n' in sys.argv:
        webbrowser.open('https://hnonline.sk')
        webbrowser.open('https://aktuality.sk')
        webbrowser.open('https://sport.aktuality.sk')


if __name__ == "__main__":
    main()
