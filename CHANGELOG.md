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
- `youtube` renamed to `yt` (module file `cases/webs/youtube.py` renamed to
  `cases/webs/yt.py` to match). `youtube` no longer runs.

### Added
- `makezip [folder]` zips a folder (default: the current directory) and
  everything in it into `<parent>\<name>_yyyy_mm_dd___HH_mm_ss.zip`, beside
  the folder, with the folder as the archive's top-level entry. The folder
  is never modified and an existing zip is never overwritten. Also
  available as "Make a zip version" in the File Explorer right-click menu,
  on folders only - re-run `setup_explorer_menu.py` to pick it up. See
  issue #71.
- `splitfiles <file.mp4>` splits a large file into ~30-minute parts (`-m N`
  for a different length, otherwise prompted, default configurable via
  `splitfiles.minutes`), via ffmpeg's segment muxer with stream copy (no
  re-encoding). A remainder under 5 minutes is folded into the previous
  part instead of becoming its own tiny file; a file that would end up as
  a single part is reported as "nothing to split". Parts go into a
  sibling `<name> - parts\` folder - the original file is never modified.
  Only `.mp4` is supported for now. Counterpart of `joinfiles` - also
  available from the File Explorer right-click menu on `.mp4` files. See
  issue #67.
- `joinfiles <folder>` joins every `.m4a` file already sitting in a folder
  into one (`<folder>/joined.m4a`), in alphabetical filename order, via
  ffmpeg's concat demuxer with stream copy (no re-encoding). Needs at
  least 2 files; a `joined.m4a` from a previous run is excluded from the
  input set before joining. Only `.m4a` is supported for now. Prints each
  file's name in the order it was joined. See issue #64.
- `batch` runs a queued list of commands from `<cloud.folder>/toProcess.txt`
  sequentially, removing each line from the queue as it completes
  (atomically, so an interrupted run leaves the remaining work intact) and
  logging successes/failures/failure-diagnostics per day under
  `<cloud.folder>/logs/`. `batch --dry-run` lists what would run without
  touching anything. New `noop` command (`noop`/`noop --fail`) exists to
  exercise `batch` against a real subprocess in tests. See issue #60.
- `batch-schedule` registers an opt-in daily Windows Scheduled Task that
  runs `batch` at a configured time (`batch.scheduleTime`, 24-hour
  `HH:MM:SS` with seconds always `00` - Windows Task Scheduler has no
  finer precision - default `03:00:00`) - nothing is scheduled until it's
  run explicitly; `uv sync`/
  `setup.ps1` never register a task on their own. `--status` shows the
  task's current trigger vs. the configured time; `--uninstall` removes
  it. Runs quietly via `pythonw.exe` (no console window), "only when
  logged on" (no Windows password stored), and skips (not catches up) a
  day the machine is off/asleep for. See issue #62.
- Every command now records its own usage (command name + timestamp) to
  `~/.boring-stuff/usage.jsonl` - purely local, last 10 calendar weeks
  kept, older entries pruned automatically. New `stats` command prints a
  report: overall usage and a per-calendar-week (Monday-Sunday) breakdown.
  See issue #52; the taskbar Jump List auto-refreshing itself from this
  data is tracked separately in #53, not part of this change.
- `email-extract` processes `.msg` email files dropped into a configured
  folder: saves PDF attachments, saves image attachments and combines them
  into a PDF, and downloads any `.pdf` link found in the body - all into
  an output folder, named `<yyyy-mm-dd> <sender name>`, with a content-hash
  check so a repeated email/link doesn't produce duplicate output. See
  issue #50 for the ruled-out trigger mechanisms (Jump List item, taskbar
  icon, shortcut icon all refuse the drop - a real Explorer folder window
  is the only one that works). Also available from the taskbar Jump List.
- `shared-drive` ensures a "share" folder exists inside the configured
  cloud folder (e.g. a Google Drive for Desktop mount), creating it if
  missing - no API or OAuth needed since the sync client already mounts it
  as a real directory. Uses the shared `cloud.folder`/`cloud.share` config
  (see `move-to`, below) - no separate config of its own.
- `move-to -s`/`move-to -o` moves a file or folder to the configured cloud
  share/output folder (`<cloud.folder>/<cloud.share>` or
  `<cloud.folder>/<cloud.output>`) - plain `shutil.move`, no Drive
  API/OAuth. Also available from the new File Explorer right-click menu
  (files and folders) - see below. See issue #58.
- A "Boring" File Explorer right-click submenu
  (`cases/devs/explorer_menu/setup_explorer_menu.py`, registered under
  `HKCU` so no admin elevation is needed): `move-to` (share/output) on
  every file and folder, plus `negative`/`mp4to3`/`email-extract` on
  their relevant file types only. Hidden under "Show more options" on
  Windows 11 by default (a platform limitation, not a bug). See issue #58.
- `negative` and `mp4to3` now also accept a single file (not just a
  folder) - `negative <picture>` inverts just that one picture,
  `mp4to3 <file.mp4>` extracts just that one file's audio - so the new
  Explorer right-click menu can act on a single clicked file.
- `email-extract <file.msg>` (a new optional argument) moves that file
  into the drop folder before processing it - what the Explorer
  right-click menu uses; still defaults to processing whatever's already
  in the drop folder when no argument is given.
- `background <color>` sets a solid desktop color (a standard 12-color
  palette, falling back to CSS3/X11 color names) instead of a random
  picture.
- `yt` (see Breaking, above) now gives every download its own subfolder
  under `~/.boring-stuff/output` (the same folder `email-extract` writes
  into, replacing the old hardcoded `~/Videos/YoutubeDownload`), named
  after the video/playlist title - a well-defined `<content-folder>` so
  the new `-c` flag has something self-contained to move. `-a`'s mp3 now
  lands in `<content-folder>/audio/` instead of alongside the video.
  `-t<langcode>` downloads a transcript into `<content-folder>` and is
  repeatable (e.g. `-ten -tsk` for English + Slovak); a language that
  isn't available is reported without aborting the rest of the download.
  `-c` moves the content folder to `<cloud.folder>/<cloud.output>` after
  a successful download - the same shared cloud config `move-to` uses
  (plain local path, e.g. a Google Drive for Desktop mount - no
  API/OAuth). See issue #55.
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
- `stats` no longer lists `noop`. The test-only command recorded its own
  usage, and the `batch` end-to-end test runs it as a real subprocess -
  which doesn't inherit the test suite's temp-home isolation - so every
  test run wrote two `noop` entries into the real `usage.jsonl`, pushing it
  to the top of the report. `noop` no longer records usage, and `stats`
  filters out entries it already wrote.
- `requires-python` is now `>=3.12,<3.13` (was unbounded `>=3.12`), and a
  new `.python-version` file pins `uv sync`/`uv run` to 3.12 by default,
  downloading it automatically if the machine doesn't have it. Without
  this, a fresh machine whose only installed Python was newer (e.g. 3.14)
  would have `uv` resolve against it, then fail installing `quickjs` -
  its prebuilt Windows wheels only go up to 3.12, so anything newer falls
  back to compiling from source and needs MSVC Build Tools. Hit for real
  setting up a second machine.
- `background` no longer stretches wallpaper pictures outside the screen.
- `background <color>` no longer turns the desktop black regardless of the
  requested color.
- `pinterest` no longer sends a mangled request URL (`requests.get(url,
  "xml")` was passing `"xml"` as `params`, not a format hint).
- `mapit`, `negative`, and `openwebs` handle their expected failure modes
  (empty clipboard, non-image files, unconfigured groups) with a clear
  message instead of crashing.
