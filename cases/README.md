# Boring stuff - manual

Boring Stuff is a personal collection of small command-line utilities that
take care of repetitive, everyday tasks - clipboard conversions, quick web
lookups, image tweaks, downloads, and more - so you don't have to do them by
hand every time.

**Windows only.** `background`, this taskbar setup, and `clipsave` depend on
`pywin32` and won't work on macOS or Linux.

## Add Boring Stuff to Taskbar in windows
A pinned taskbar shortcut ("B" icon): left-click runs `clipsave`, right-click
shows a Jump List menu with `b64d`/`b64e`/`background`/`json-pretty`
(pretty-print and minify) - hover any item to see the command it runs. Each
opens a terminal window that shows the result and closes itself after 60
seconds.

One-time setup:

    uv run python cases/devs/taskbar/setup_taskbar_icon.py

Then, in the folder it prints (`%USERPROFILE%\.boring-stuff`), right-click
`Boring.lnk` and choose "Pin to taskbar". Safe to re-run the setup script any
time - it refreshes the icon and the Jump List tasks in place (e.g. after
pulling an update that renames or adds a taskbar-registered command).

To remove it:

    uv run python cases/devs/taskbar/setup_taskbar_icon.py --uninstall

Removes the Jump List registration, the shortcut, and the icon (leaves your
`BoringStuff.yml` config untouched). Right-click the taskbar icon and choose
"Unpin from taskbar" afterward - Windows doesn't expose an API to do that
part programmatically.

## Available scripts

### cases/devs

#### B64d / B64e
Base64 decode/encode the clipboard's text, in place - result goes straight
back onto the clipboard, no files, no arguments.

Run command:

    b64d   (decode)
    b64e   (encode)

If the clipboard isn't valid base64 (for `b64d`), or is empty, prints a
message and exits non-zero without touching the clipboard.

#### Json-pretty
Pretty-print (or minify) the clipboard's JSON text, in place - result goes
straight back onto the clipboard, no files.

Run command:

    json-pretty            (pretty-print, 2-space indent)
    json-pretty --minify   (minify)

If the clipboard isn't valid JSON, or is empty, prints a message and exits
non-zero without touching the clipboard.

#### Prune-branches
Delete branches already merged into origin's default branch (master/main).
Run from inside whichever repo you want to clean up - not specific to
boring-stuff.

Run command:

    prune-branches                    (local, dry run - lists what would be deleted)
    prune-branches --yes              (local, actually deletes them)
    prune-branches --remote           (origin, dry run)
    prune-branches --remote --yes     (origin, actually deletes them)

Fetches from origin first (with `--prune`, so stale remote-tracking refs
don't linger) so the merged-status check reflects branches merged remotely
(e.g. via a squash-merged PR), even if your local default branch hasn't
been updated yet. Local deletion only removes branches git itself considers
safe to delete (`git branch -d`, not `-D`); `--remote` deletes branches on
origin via `git push origin --delete` - only ever branches already
confirmed merged, but a real, visible-to-everyone deletion, so double-check
the dry-run list first.

### cases/git

#### Gitconfig
Not available as a command yet - [git/gitConfig.py](git/gitConfig.py) is
currently just a stub for per-repo git config management. See
[TODO.md](../TODO.md) for the planned scope.

### cases/maps

#### Mapit
Open google map with specific address:
- default is taken from clipboard
- from argument of the command

Run command:

    mapit  (takes address from clipboard)
    mapit Bratislava

### cases/pictures

#### Negative
Invert every picture in a folder to its negative, saved into a `negative`
subfolder alongside the originals (so re-running doesn't invert its own
output). Non-image files in the folder are skipped with a message.

Run command:

    negative [directory_with_picture]

### cases/webs

#### Lucky
Open several (default is 4) page in default browser from googling

Run command:

    lucky tips for developers
    lucky -n3 tips for developers

Parameters:

**-n3** - number of pages opened in browser

#### Mp4to3
Extract mp3 audio from every .mp4 file already sitting in a folder (doesn't
download anything itself - see `youtube -a` for downloading + extracting in
one step).

Run command:

    mp4to3 [folder]

#### Openwebs
Open a batch of your usual sites in the browser, grouped by tag.

Run command:

    openwebs           (opens all groups)
    openwebs init      (mail/calendar/translate)
    openwebs s         (social sites)
    openwebs n         (news sites)
    openwebs s n       (multiple groups at once)

Groups default to `init`/`s`/`n` above, but can be fully replaced via
config (in `~/.boring-stuff/BoringStuff.yml`) - each key becomes a tag:

    openwebs:
      work:
        - https://mail.example.com
        - https://tickets.example.com

#### Pinterest
Open random picture from pinteres board

Run command:

    pinterest

Configuration (in `~/.boring-stuff/BoringStuff.yml`):

    pinterest:
      randomBoard: https://pinterest.com/username/board.rss

#### Youtube
Download youtube video.
Run command:

    youtube -a [youtube url] - it creates also mp3 file
    youtube [youtube url]
    youtube [youtube playlist url]

### cases/wins

#### Clipsave
Save clipboard content to your Downloads folder. Auto-detects the content
type - no prompt, no flags needed:

- image -> `<timestamp>.png`
- text -> `<timestamp>.txt`
- a copied file -> `<timestamp> <original name>` (copied, original left in place)
- a copied folder -> `<timestamp> <folder name>.zip`
- multiple copied files/folders -> each one handled per the rules above

Run command:

    clipsave

Timestamp format is `YYYY-MM-dd HH-mm-ss` (e.g. `2026-08-28 09-45-50`).
Prints a message and exits non-zero if the clipboard is empty or nothing
could be saved.

#### Background
Set your desktop background to a random picture from a configured folder, or
to a solid color. A color name is first tried against a standard 12-color
palette (red, orange, yellow, green, cyan, blue, purple, pink, brown, black,
white, gray); if that doesn't match, it falls back to CSS3/X11 color names
(e.g. `light blue`, `steelblue`), so most everyday color names work.

Run command:

    background
    background green
    background light blue

Configuration (in `~/.boring-stuff/BoringStuff.yml`), only needed for the
random-picture form:

    wallpaper:
      directory: C:\Pictures\Wallpapers

### scripts

#### Hello
Run command:

    hello

to ensure that scrips can be run from CMD. Also saves your name/surname/age
into `~/.boring-stuff/BoringStuff.yml` - the same config file every other
script reads from.
