# Changelog

All notable changes to this project are documented here, in the spirit of
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

**Convention:** a command being renamed or removed is always a **Breaking**
change and gets its own line under that heading - not folded into
"Changed". `background` replacing `set-wallpaper` (below) is the case this
convention exists for: it silently broke the live taskbar Jump List for
anyone who'd already run `setup_taskbar_icon.py`, and nothing said so
anywhere until it broke. When you see a Breaking entry, re-run
`cases/devs/taskbar/setup_taskbar_icon.py` if the changed command was one
of the ones registered there.

This file starts tracking from here - earlier history lives in `git log`,
not backfilled here.

## [Unreleased]

### Breaking
- `set-wallpaper` renamed to `background`.

### Added
- `outlook-action` processes `.msg` email files dropped into a configured
  folder: saves PDF attachments, saves image attachments and combines them
  into a PDF, and downloads any `.pdf` link found in the body - all into
  an output folder, named `<yyyy-mm-dd> <sender name>`. See issue #50 for
  the ruled-out trigger mechanisms (Jump List item, taskbar icon,
  shortcut icon all refuse the drop - a real Explorer folder window is
  the only one that works).
- `shared-drive` ensures a `boring-stuff` folder exists inside a configured
  shared/synced drive folder (e.g. a Google Drive for Desktop mount),
  creating it if missing. First step toward using such a folder as a plain
  filesystem path for uploads/edits - no API or OAuth needed since the sync
  client already mounts it as a real directory.
- `background <color>` sets a solid desktop color (a standard 12-color
  palette, falling back to CSS3/X11 color names) instead of a random
  picture.
- `json-pretty` (and `json-pretty --minify`) pretty-prints or minifies the
  clipboard's JSON text in place.
- Scripts with a required config value (`background`'s wallpaper directory,
  `pinterest`'s board URL) now prompt for it and save the answer instead of
  crashing with `KeyError` when it's missing.
- Taskbar Jump List items show the command they run as a hover tooltip.
- `cases/devs/taskbar/setup_taskbar_icon.py --uninstall` removes the
  registered Jump List, shortcut, and icon (see the "Uninstalling" section
  in `README.md`).
- CI now runs a `lint` job (`ruff`) and tests on both `ubuntu-latest` and
  `windows-latest`, so the Windows-only code actually gets exercised.

### Fixed
- `background` no longer stretches wallpaper pictures outside the screen.
- `background <color>` no longer turns the desktop black regardless of the
  requested color.
- `pinterest` no longer sends a mangled request URL (`requests.get(url,
  "xml")` was passing `"xml"` as `params`, not a format hint).
- `mapit`, `negative`, and `openwebs` handle their expected failure modes
  (empty clipboard, non-image files, unconfigured groups) with a clear
  message instead of crashing.
