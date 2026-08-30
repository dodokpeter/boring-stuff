Automating the mundane to focus on what matters.

A collection of Python utility scripts for daily productivity.

**Windows only.** Several commands (`background`, the taskbar setup, `clipsave`)
depend on `pywin32` for Shell/registry integration and won't work on macOS or
Linux.

## ⚡ Quick Start (New PC)

1.  **Install uv** (The modern way to manage Python):
    ```powershell
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
2.  **Clone & Setup**:
    ```bash
    git clone https://github.com/dodokpeter/boring-stuff.git
    cd boring-stuff
    # This creates a venv and installs all dependencies in seconds
    uv sync
    ```
3.  **Initialize**:
    ```bash
    ./setup.ps1
    ```
4. Run this command in PowerShell:
   ```uv pip install -e .```
   Result: uv will create a shim. Now, as long as your venv is active, you can just type hello.

## Upgrading

```bash
git pull
uv sync
```

Then check [CHANGELOG.md](CHANGELOG.md) for anything under **Breaking** -
if a command you use (or have pinned to the taskbar) was renamed or
removed, that's where you'll find out. If a taskbar-registered command
changed, re-run the taskbar setup to pick it up:

```bash
uv run python cases/devs/taskbar/setup_taskbar_icon.py
```

## Uninstalling

```bash
uv run python cases/devs/taskbar/setup_taskbar_icon.py --uninstall
```

removes the registered Jump List, the pinned shortcut, and the generated
icon. Windows has no supported API to un-pin a taskbar icon
programmatically, so if it's still pinned, right-click it and choose
"Unpin from taskbar" to finish.

This does **not** touch `~/.boring-stuff/BoringStuff.yml` - that's your
actual config (Pinterest board, wallpaper folder, etc.), and removing it is
a separate decision. To remove everything:

```powershell
Remove-Item -Recurse -Force $HOME\.boring-stuff   # or delete the folder in Explorer
```

Then delete the cloned repo folder (and its `.venv`) however you'd remove
any other folder.

---

## 🔧 Environment & Dependencies

### Python Management
This project uses **Python 3.12+**. We no longer recommend manual Path edits or Anaconda for this repo.
* **Virtual Environments:** Managed automatically via `uv` or `venv`.
* **Dependencies:** All core libraries are tracked in `pyproject.toml`, locked in `uv.lock`.

### Core Libraries Used:
| Library | Usage |
| :--- | :--- |
| `pyyaml` | Reads/writes `~/.boring-stuff/BoringStuff.yml` |
| `openpyxl` | Excel automation |
| `requests` | HTTP requests (e.g. `pinterest`) |
| `yt-dlp` | YouTube video/audio downloads |
| `quickjs` | JS runtime for yt-dlp's challenge-solving |
| `googlesearch-python` | Scrapes Google results for `lucky` |
| `pillow` | Image processing (`negative`, `clipsave`, `background`, taskbar icon) |
| `pyperclip` | Clipboard read/write (`b64d`/`b64e`, `mapit`, `clipsave`) |
| `pywin32` | Windows-only Shell/taskbar Jump List integration |
| `xmltodict` | Parses the Pinterest RSS feed |

---

## Additional installations

### youtube command

For the MP3 extraction to work, ffmpeg must be on your system path.
The Modern Way: The easiest way to install it is via winget (Windows Package Manager):

```winget install ffmpeg```
After installing, restart your terminal. yt-dlp will automatically find it.

Path environment variable modified; restart your shell to use the new value.
Command line alias added: "ffmpeg"
Command line alias added: "ffplay"
Command line alias added: "ffprobe"

YouTube recently started requiring a JavaScript (JS) runtime to extract video information properly. 
Without it, you get that "Video not available" error even if the video is perfectly fine.
```winget install denoland.deno```

If you still get "Challenge solving failed"
If the logs say challenge solving failed even after the steps above, it's time to force the download directly into your script's environment. Use this command:
```uv run yt-dlp --remote-components ejs:github --update-base```


## 📖 Available Commands
Run `hello` in your terminal to verify the installation.

* [Command Reference](./cases/README.md) - Full list of available automation scripts.
* [CHANGELOG.md](CHANGELOG.md) - what changed, and what's Breaking.

## Versioning

There's no built release artifact yet (see [CHANGELOG.md](CHANGELOG.md) -
distribution is git-clone based for now), so a version tag is just a
label: it only ever gets created from a `master` commit whose CI (`lint`
and both `test` matrix legs) is green.



## 🛠️ Internal Maintenance Notes
<details>
<summary>Troubleshooting Pillow/DLL issues</summary>

If you encounter `ImportError: DLL load failed` for Pillow on Windows, ensure you are not mixing Conda and Pip environments. Using the `uv` setup above bypasses the old Anaconda 1.6.12 versioning conflicts.
</details>