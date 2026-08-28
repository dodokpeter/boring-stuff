# Available scripts

## Hello
Run command:

    hello

to ensure that scrips can be run from CMD. 
## Lucky

Open several (default is 4) page in default browser from googling

Run command:

    lucky tips for developers
    lucky -n3 tips for developers

Parameters:

**-n3** - number of pages opened in browser

## Mapit
Open google map with specific address:
- default is taken from clipboard
- from argument of the command

Run command:

    mapit  (takes address from clipboard)
    mapit Bratislava

## Pinterest
Open random picture from pinteres board

Run command:

    pinterest
    
Configuration (in userHome/BoringStuff.ini):

    [Pinterest]
    RandomBoard: https://pinterest.com/username/board.rss
    
## Youtube
Download youtube video.
Run command:

    youtube -a [youtube url] - it creates also mp3 file
    youtube [youtube url]
    youtube [youtube playlist url]


## Negative
Invert picture in negative colors.
Run command:

    negative [directory_with_picture]

## Clipsave
Save clipboard content to your Downloads folder. Auto-detects whether the
clipboard holds an image or text - no prompt, no flags needed.

Run command:

    clipsave

Saves as `YYYY-MM-dd HH-mm-ss.png` for images or `.txt` for text (e.g.
`2026-08-28 09-45-50.png`). Prints a message and exits non-zero if the
clipboard is empty or holds something else (like copied files).
