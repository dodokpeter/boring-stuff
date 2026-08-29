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

---

# Repository analysis (2026-08-29)

Findings from a full read of the repo. Tests currently pass (40/40).
Grouped roughly by payoff; each item names the file it applies to.

## Tooling and CI

- No linter or formatter configured. Adding `ruff` (lint + format) would catch
  unused locals and bare `except Exception` cases elsewhere in the repo.
- [.github/workflows/tests.yml](.github/workflows/tests.yml) runs only on
  `ubuntu-latest` and a single Python version, yet a large part of the codebase is
  Windows-only (`pywin32`, the taskbar setup, `background`). Add a
  `windows-latest` matrix leg so that code is exercised at all.
- No lint job and no coverage reporting in CI.
- No `pytest` configuration in `pyproject.toml` (`testpaths`, `pythonpath`) - the
  `sys.path` insertion in `conftest.py` could be replaced by `pythonpath = ["."]`.

## Test gaps

Untested modules: [cases/webs/youtube.py](cases/webs/youtube.py),
[cases/git/gitConfig.py](cases/git/gitConfig.py).

## Documentation

- [README.md](README.md) says dependencies are tracked in `requirements.txt` - that
  file does not exist; everything lives in `pyproject.toml`/`uv.lock`.
- README's "Core Libraries" table lists `pypdf2`, `python-docx` and `moviepy`, none of
  which are declared or used anywhere in the repo.
- README has a whole Selenium/geckodriver section, but there are no Selenium scripts
  and `webdriver-manager` is not a dependency.
- README clone URL is still the placeholder `https://github.com/youruser/BoringStuff.git`.
- [cases/README.md](cases/README.md) does not document the `gitConfig` stub.
