Automating the mundane to focus on what matters.

A collection of Python utility scripts for daily productivity.

## ⚡ Quick Start (New PC)

1.  **Install uv** (The modern way to manage Python):
    ```powershell
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
2.  **Clone & Setup**:
    ```bash
    git clone https://github.com/youruser/BoringStuff.git
    cd BoringStuff
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


---

## 🔧 Environment & Dependencies

### Python Management
This project uses **Python 3.12+**. We no longer recommend manual Path edits or Anaconda for this repo.
* **Virtual Environments:** Managed automatically via `uv` or `venv`.
* **Dependencies:** All core libraries are tracked in `requirements.txt`.

### Core Libraries Used:
| Library | Usage |
| :--- | :--- |
| `pyyaml` | Configuration and data parsing |
| `openpyxl` | Excel automation |
| `pypdf2` | PDF manipulation |
| `python-docx` | Word document generation |
| `pillow` | Image processing |
| `moviepy` | Video editing |

---

## 🌐 Selenium Setup (Geckodriver)
If you use the web automation scripts, you need the Firefox `geckodriver`.
1.  **Automatic (Recommended):** The scripts now use `webdriver-manager` (added to requirements), so you likely **don't** need to download drivers manually anymore.
2.  **Manual:** If needed, download from [geckodriver releases](https://github.com/mozilla/geckodriver/releases) and place it in the `bin/` folder of this repo.

---

## 📖 Available Commands
Run `hello` in your terminal to verify the installation.

* [Command Reference](./scripts/README.md) - Full list of available automation scripts.

---

## 🛠️ Internal Maintenance Notes
<details>
<summary>Troubleshooting Pillow/DLL issues</summary>

If you encounter `ImportError: DLL load failed` for Pillow on Windows, ensure you are not mixing Conda and Pip environments. Using the `uv` setup above bypasses the old Anaconda 1.6.12 versioning conflicts.
</details>