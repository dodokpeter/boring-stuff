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

- `clean-logs` console script in `pyproject.toml` points to `scripts.cleanup:run`, which doesn't exist - crashes if run
- `scripts/hello.py` throws `UnicodeEncodeError` on this console's codepage (emoji in a `print`)
- `mapit.py`/`negative.py` lack basic error handling (empty clipboard, non-image files in a directory)

## Environment/admin

- Optional: branch protection on `master` requiring the CI "test" check to pass before merge
