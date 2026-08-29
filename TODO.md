# Open items

Running list of things discussed but not yet done. Remove an item once it's built/fixed.

## Feature ideas, not yet built

- `killport <port>` - find and kill whatever process is holding a TCP port
- `todos` - scan local repos for TODO/FIXME comments, list grouped by file
- `standup` - summarize your own git commits (yesterday/today) across one or more local repos
- `newproj <name>` - scaffold a new project (git init, uv init, README, .gitignore) matching personal conventions
- `findcode <term>` - grep across every repo under a root folder (e.g. `C:\Projects`) at once
- `jsonfmt` - pretty-print/minify JSON from the clipboard, back to the clipboard
- `jwtd` - decode a JWT from the clipboard, print/copy header+payload as JSON
- `pr` command - branch + push + open a PR in one go, now that `gh` CLI is installed and authenticated
- finish [cases/git/gitConfig.py](cases/git/gitConfig.py) - currently just a `# todo` stub for per-repo git config management

## Known bugs/gaps

- `scripts/hello.py` throws `UnicodeEncodeError` on this console's codepage (emoji in a `print`)
- `mapit.py`/`negative.py` lack basic error handling (empty clipboard, non-image files in a directory)

## Environment/admin

- Optional: branch protection on `master` requiring the CI "test" check to pass before merge

---

# Repository analysis (2026-08-29)

Findings from a full read of the repo. Tests currently pass (40/40).
Grouped roughly by payoff; each item names the file it applies to.

## Correctness bugs

- [cases/webs/pinterest.py](cases/webs/pinterest.py) - `random.randint(0, size)` is
  inclusive on both ends, so it can index one past the end of the item list and
  raise `IndexError`. Should be `randint(0, size - 1)` (or `random.choice`).
- [cases/webs/pinterest.py](cases/webs/pinterest.py) - a feed with a single `<item>`
  parses as a dict, not a list, so `len(...)` and indexing silently do the wrong
  thing. The test only covers the two-item case (and says so in a comment).
- [scripts/hello.py](scripts/hello.py) - `int(age) + 1` in the final print is outside
  the `try`, so a non-numeric age is accepted earlier and then crashes at the end.
- [cases/wins/setBackgroundPicture.py](cases/wins/setBackgroundPicture.py) - all logic
  runs at import time, the `sys.argv` check demands an argument that is then never
  used, and `DIR_PATH` is hardcoded to `c:\repositories\_backgroundPics\`.
- [cases/maps/mapit.py](cases/maps/mapit.py) - address is not URL-encoded, so
  addresses with `&`, `#` or `+` build a broken Maps URL.

## Robustness / UX

- [cases/pictures/negative.py](cases/pictures/negative.py) - no filtering of
  non-image files (any stray file raises), string path concatenation instead of
  `pathlib`, output written next to the input so a second run inverts its own
  `negative*.png` output, and `ImageOps.invert` fails on RGBA/palette PNGs.
- [cases/maps/mapit.py](cases/maps/mapit.py) - uses a bare Tkinter root for the
  clipboard (never withdrawn or destroyed, flashes a window) while `pyperclip` is
  already a dependency; empty clipboard is unhandled.
- Emoji in `print` statements ([scripts/hello.py](scripts/hello.py),
  [cases/webs/youtube.py](cases/webs/youtube.py), `setup.ps1`) raise
  `UnicodeEncodeError` on a legacy Windows console codepage.
- [cases/webs/openwebs.py](cases/webs/openwebs.py) - the site list is hardcoded and
  shadows the builtin `all`; the groups belong in user config.
- No script prints a `--version` or supports `-h` consistently (the argparse-based
  ones do; the `sys.argv`-based ones do not).

## Tooling and CI

- No linter or formatter configured. Adding `ruff` (lint + format) would catch the
  builtin shadowing, unused locals, and the bare `except Exception` cases above.
- [.github/workflows/tests.yml](.github/workflows/tests.yml) runs only on
  `ubuntu-latest` and a single Python version, yet a large part of the codebase is
  Windows-only (`pywin32`, the taskbar setup, `setBackgroundPicture`). Add a
  `windows-latest` matrix leg so that code is exercised at all.
- No lint job and no coverage reporting in CI.
- No `pytest` configuration in `pyproject.toml` (`testpaths`, `pythonpath`) - the
  `sys.path` insertion in `conftest.py` could be replaced by `pythonpath = ["."]`.

## Test gaps

Untested modules: [cases/webs/youtube.py](cases/webs/youtube.py),
[cases/wins/setBackgroundPicture.py](cases/wins/setBackgroundPicture.py),
[cases/git/gitConfig.py](cases/git/gitConfig.py). The pinterest test does not cover
the single-item feed or an out-of-range index (both real bugs listed above).

## Documentation

- [README.md](README.md) says dependencies are tracked in `requirements.txt` - that
  file does not exist; everything lives in `pyproject.toml`/`uv.lock`.
- README's "Core Libraries" table lists `pypdf2`, `python-docx` and `moviepy`, none of
  which are declared or used anywhere in the repo.
- README has a whole Selenium/geckodriver section, but there are no Selenium scripts
  and `webdriver-manager` is not a dependency.
- README clone URL is still the placeholder `https://github.com/youruser/BoringStuff.git`.
- [cases/README.md](cases/README.md) does not document `openwebs` config or the
  `clean-logs`/`gitConfig` stubs.
