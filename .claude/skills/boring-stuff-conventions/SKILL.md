---
name: boring-stuff-conventions
description: House rules and workflow for the boring-stuff repository (C:\Projects\boring-stuff), a personal collection of Windows automation scripts. Use this any time you are adding, moving, fixing, testing, or documenting anything in this repo - new commands, bug fixes, dependency changes, taskbar/Jump List work, git branch cleanup, or config handling. Load it before writing code here, not just when the user explicitly asks about "conventions" - if the working directory is this repo, this skill almost certainly applies.
---

# Boring Stuff repo conventions

This repo is a personal collection of small Windows automation commands
(`lucky`, `clipsave`, `b64d`/`b64e`, `prune-branches`, `background`, and
more). The conventions below came out of real bugs hit and fixed while
building it out - following them saves you from repeating that work.

## Where things live

`cases/` is the single top-level container for every script category:

- `cases/devs` - dev-workflow tooling (base64 clipboard, prune-branches, the
  taskbar setup script)
- `cases/maps`, `cases/pictures`, `cases/webs`, `cases/wins` - personal-use
  scripts, grouped by what they do
- `cases/git` - git-related utilities

`scripts/` only holds `hello.py` - nothing else belongs there. `core/` holds
shared infrastructure, most importantly `core/configuration/user_conf.py`:
the single config loader/saver, backed by one YAML file at
`~/.boring-stuff/BoringStuff.yml`. If a script needs a user-specific
setting (an API URL, a folder path, credentials-free preferences), route it
through `load_config`/`save_config` from that module rather than inventing
a new config file or format - this repo used to have three different config
mechanisms before they got consolidated into this one, and it was a real
mess to unwind.

If a script *requires* a config value to run (not just an optional
preference with a working default, like `openwebs`'s groups), use
`load_config_value(config_name, message, default, *config_keys, validate=...)`
instead of indexing the config dict directly - it supports a nested key
path (`"wallpaper", "directory"`), prompts for and persists a missing value
instead of raising a raw `KeyError`, and raises `MissingConfigError` if the
prompt itself can't be completed (no terminal attached, or cancelled),
which the script should catch and turn into a message + non-zero exit. See
`background.py`/`pinterest.py` for the pattern, including the optional
`validate` callback (`background`'s wallpaper directory is checked to
actually exist and be non-empty before it's saved).

## Adding or fixing a command

Every command is a real console-script entry point in `pyproject.toml`,
e.g. `lucky = "cases.webs.lucky:main"`. There used to be an older mechanism
(`scripts/*.bat` shims relying on a `%BORING_STUFF_PATH%` environment
variable) - that variable is unset on this machine and the whole approach
is dead. Never resurrect it; always register new commands as proper entry
points instead.

Give each script's entry point a `main(argv=None)` function built on
`argparse` when it takes arguments (see `cases/webs/lucky.py` or
`cases/webs/mp4to3.py` for the pattern). This isn't just style - it's what
lets tests call `module.main([...])` directly instead of monkeypatching
`sys.argv`, which is both cleaner and more reliable.

After registering a new entry point, `uv sync` (not just editing
`pyproject.toml`) to actually install the shim, and sanity-check it runs
before considering the work done.

## Git and PR workflow

Never push straight to `master` here - always branch, commit, push, and
open a PR, even for a small fix. This was stated explicitly and firmly by
the repo owner after an early slip-up, so treat it as non-negotiable rather
than a judgment call.

The standard sequence:

```bash
git checkout master && git pull   # always sync first - see note below
git checkout -b <descriptive-name>
# make changes, run tests
git add <files>
git commit -m "..."
git push -u origin <descriptive-name>
gh pr create --title "..." --body "..."
gh pr checks <N> --repo dodokpeter/boring-stuff --watch
```

For a non-trivial or ambiguous feature (open design questions, multiple
reasonable approaches), file a GitHub issue on
`https://github.com/dodokpeter/boring-stuff/issues` first, capturing the
proposal, the decisions made, and explicit out-of-scope items - then open
a PR that closes it. This has been worth it twice already: a reviewer
(human or otherwise) can comment on the issue and get it updated before
any code is written, and "explicitly out of scope" prevents the same
question from being silently re-decided differently in a later PR.

A few things that will trip you up if you don't know them:

- **Sync before branching, every time.** PRs in this repo often get merged
  by the owner between turns without any explicit notification. Don't
  assume `master` is where you left it - `git checkout master && git pull`
  first, and read the fast-forward output rather than assuming nothing
  changed.
- **If new work depends on something that only exists on an unmerged
  branch** (e.g. you need a command that was added in a PR still awaiting
  review), branch from that branch instead of stale `master`. Check with
  `git log --oneline origin/master` if you're unsure whether a dependency
  has landed yet.
- **`gh` may not be on `PATH` inside an already-running shell**, even
  though it's installed and authenticated (as `dodokpeter`). Environment
  variable changes don't propagate to processes that were already running
  when the change happened. If the bare `gh` command isn't found, fall
  back to the full path: `"C:\Program Files\GitHub CLI\gh.exe"`.
- **Wait for CI to go green before calling something done.** `gh pr checks
  <N> --repo dodokpeter/boring-stuff --watch` blocks until the checks
  resolve. `master` has branch protection requiring `lint`,
  `test (ubuntu-latest)`, and `test (windows-latest)` to pass, so an
  unmerged PR with failing CI can't land anyway.
- **A stacked PR (branched off another unmerged branch) doesn't get CI
  until it targets `master`.** `tests.yml` only triggers on PRs into
  `master`, so retarget with `gh pr edit <N> --base master` once the
  dependency merges - but a base-branch edit alone doesn't fire a new
  `pull_request` event, so CI still won't run until you also
  `gh pr close <N>` + `gh pr reopen <N>` (or push a new commit) to trigger
  it.
- **If you ever change job names or add a matrix to `tests.yml`,
  update branch protection's required status checks to match.** GitHub
  Actions renames matrix jobs in the checks list (e.g. `test` ->
  `test (ubuntu-latest)` / `test (windows-latest)`), but branch protection
  keeps whatever check name string it already had configured. A mismatch
  means every future PR shows unmergeable/stuck-pending forever, waiting
  on a check name that will never post again - this happened for real
  after adding the OS matrix, and needed
  `gh api -X PATCH repos/.../branches/master/protection/required_status_checks`
  to fix.

## Line endings

`.gitattributes` at the repo root (`* text=auto eol=lf`) normalizes every
text file to LF on `git add`. This fixed a real recurring problem: editing
files on this Windows machine used to silently flip them to CRLF, which
made every diff in that file look like a full delete-and-rewrite instead of
the actual one-line change. You shouldn't need to think about this anymore,
but if a diff ever looks suspiciously huge for a small edit, that's the
first thing to check.

## Testing

Every new or fixed script gets real pytest coverage in `tests/`. Fake the
external interactions - clipboard (`pyperclip`), network (`requests`),
browser (`webbrowser.open`), filesystem - with `monkeypatch` rather than
hitting real systems in CI: CI runs on both `ubuntu-latest` and
`windows-latest`, and neither can touch a real clipboard or open a real
browser.

For anything that only makes sense on Windows (`pywin32`, `tkinter`), guard
the test module with `pytest.importorskip(...)` so it skips cleanly on
Linux CI instead of erroring at collection time.

`IObjectArray.GetAt(index, IID)` (reading an item back out of a Jump
List/COM object array) reliably segfaults the whole interpreter in this
pywin32 setup - reproduced standalone outside pytest too, not a test-only
quirk. Don't try to introspect a built `IObjectArray`'s contents that way;
`GetCount()` is safe, and per-item content is better covered by testing
the smaller functions (`make_link`, `set_title`) that built it, the way
`tests/test_setup_taskbar_icon.py` does.

Mocked unit tests are necessary but not sufficient - wherever it's
feasible and safe, also verify the real thing works: run the actual
command against a real (throwaway) clipboard value, a real small `ffmpeg`
conversion, a real temporary git repo (bare "remote" + clone, matching the
pattern in `tests/test_prune_branches.py`). This has caught real bugs that
mocks alone would have missed - the Windows-vs-Linux path-separator bugs in
`mp4to3.py`/`pinterest.py`, for instance, only showed up once tests ran on
real CI rather than just against mocks on this Windows machine.

Run `uv run pytest tests/ -q` before every commit. If you touch anything
real during manual verification (the actual clipboard, `~/Downloads`, the
real `BoringStuff.yml`, real local/remote git branches), clean it up
immediately afterward - don't leave test data sitting in the user's real
files or repo state.

## Linting and formatting

`ruff` (lint + format) is configured in `pyproject.toml` and gated in CI as
its own `lint` job, separate from `test`. Before committing, run
`uv run ruff check .` and `uv run ruff format .` (the latter rewrites files
in place - use `--check` instead if you just want to know whether it would).
`rasbpi/` is excluded (a standalone legacy Python 2 script, not part of the
packaged `boring-stuff` tool suite).

## Packaging

Two non-obvious settings in `pyproject.toml` exist because of real,
previously-hit bugs:

- `[tool.uv] package = true` - without it, `uv sync` silently uninstalls
  this project's own console scripts every time a dependency is added or
  removed. If commands you know you registered suddenly can't be found,
  check this hasn't regressed, then re-run `uv sync`.
- `[tool.setuptools.packages.find]` with `include = ["cases*", "core*",
  "scripts*"]` and `namespaces = true` - every package here is an implicit
  namespace package (no `__init__.py` anywhere), so setuptools needs to be
  told explicitly to discover them this way. Without it, a non-editable
  install produces a wheel containing zero source files and every entry
  point breaks - this was verified directly by building the wheel and
  inspecting its contents before the fix existed.

Platform-specific dependencies (`pywin32`) need a `sys_platform ==
'win32'` marker in `pyproject.toml`, or `uv sync` breaks on the Linux CI
runner, which can't install a Windows-only package.

## Documentation

`cases/README.md` documents every command, organized into sections that
mirror the real folder structure (`### cases/devs`, `### cases/webs`,
etc.), commands alphabetical within each section. Keep a new command's doc
entry in the right section rather than tacking it on wherever's
convenient.

`TODO.md` is a live backlog, not a changelog - remove an item's bullet as
soon as it's actually fixed, rather than letting resolved items or
references to since-deleted files pile up.

## Distribution and releases

Distribution is git-clone based for now (`git clone` -> `uv sync` ->
`setup.ps1`; upgrade is `git pull` -> `uv sync`) - no PyPI package, no
built release artifact. That's an explicit, revisit-later decision, not an
oversight; don't add PyPI publishing or artifact-building tooling without
that decision being reopened first.

`CHANGELOG.md` (Keep a Changelog style) tracks changes from when it was
added onward - it was never backfilled against older history, so don't
try to reconstruct entries for anything before it existed. **Any command
rename or removal is a Breaking change and must get its own line under
that heading.** This isn't optional politeness: renaming `set-wallpaper`
to `background` without flagging it anywhere silently broke the live
taskbar Jump List (it kept pointing at a `.bat` file that no longer
existed) until `setup_taskbar_icon.py` was re-run - exactly the kind of
damage the Breaking convention exists to prevent for the next rename.

A version tag only ever gets created from a `master` commit whose CI
(`lint` + both `test` legs) is green - there's no automated release
workflow enforcing this since there's no artifact to gate yet, so it's on
whoever's tagging to check.

`setup_taskbar_icon.py --uninstall` removes the registered Jump List, the
pinned shortcut, and the generated icon, but deliberately never touches
`BoringStuff.yml` - removing someone's actual config is a separate
decision from removing a taskbar shortcut, not a side effect of it.

## Judgment calls worth knowing about

- **Stay scoped to what's asked.** If you're fixing bugs from one named
  section of `TODO.md`, don't also fix bugs from a different section in
  the same file just because you noticed them while you were there - note
  them and move on. Scope creep here has been explicitly corrected before.
- **Preserve existing behavior when just relocating code**, even buggy
  behavior, unless the bug itself is what you were asked to fix. Wrapping
  bare module-level code in a `main()` function, for example, shouldn't
  change what the code actually does.
- **Confirm a file is genuinely dead before deleting it** - grep the whole
  repo for imports/references first, then delete outright rather than
  commenting it out or leaving a TODO.
- **Building a capability isn't the same as authorization to run it for
  real.** Deleting remote git branches, changing the real desktop
  wallpaper, opening a dozen real browser tabs, or writing test data into
  the user's actual config file are all things worth a quick check-in
  before doing for real, even if the feature itself was explicitly
  requested. If you do touch real state while verifying something, clean
  up immediately after.
- **When verifying against the real `~/.boring-stuff/BoringStuff.yml`**
  (as opposed to a `tmp_path`-isolated test), copy it aside first and
  restore the exact original content afterward, even across multiple
  verification steps - don't leave it half-modified or trust that the
  next step will happen to put back what the first step removed.
- **Repo-level settings changes - branch protection, git tags - also
  warrant a check-in first**, same as the real-state category above, even
  though they're not code. They're immediately live and visible (unlike a
  PR, which is reviewable before it lands), and a tag in particular is
  meant to be a stable, semi-permanent marker.
