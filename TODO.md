# Open items

Running list of things discussed but not yet done. Remove an item once it's built/fixed.

## Feature ideas, not yet built

- `killport <port>` - find and kill whatever process is holding a TCP port
- `todos` - scan local repos for TODO/FIXME comments, list grouped by file
- `standup` - summarize your own git commits (yesterday/today) across one or more local repos
- `newproj <name>` - scaffold a new project (git init, uv init, README, .gitignore) matching personal conventions
- `findcode <term>` - grep across every repo under a root folder (e.g. `C:\Projects`) at once
- `jwtd` - decode a JWT from the clipboard, print/copy header+payload as JSON
- `pr` command - branch + push + open a PR in one go, now that `gh` CLI is installed and authenticated
- finish [cases/git/gitConfig.py](cases/git/gitConfig.py) - currently just a `# todo` stub for per-repo git config management

---

# Repository analysis (2026-08-29)

Findings from a full read of the repo.
Grouped roughly by payoff; each item names the file it applies to.

## Tooling and CI

- [.github/workflows/tests.yml](.github/workflows/tests.yml) only tests a
  single Python version (3.12) - consider a matrix leg for newer versions too.

## Test gaps

Untested modules: [cases/git/gitConfig.py](cases/git/gitConfig.py).
