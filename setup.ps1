# lean-setup.ps1
Write-Host "🚀 Initializing BoringStuff with uv..." -ForegroundColor Cyan

$repoPath = Get-Location
$configDest = Join-Path $HOME "boring-stuff"

# 1. Sync Dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
uv sync

# `uv sync` alone doesn't install this project's own console scripts
# (hello/youtube/yt) since pyproject.toml isn't set up as a proper uv
# package - it can even uninstall them if already present. Reinstall in
# editable mode so those commands keep working after every setup run.
uv pip install -e .

# 2. Initialize Config Folder (The only manual part left)
Write-Host "Creating configuration in $configDest..." -ForegroundColor Yellow
if (-not (Test-Path $configDest)) {
    New-Item -ItemType Directory -Path $configDest -Force | Out-Null
}

$configFile = Join-Path $repoPath "BoringStuff.yml"
if (Test-Path $configFile) {
    Copy-Item $configFile (Join-Path $configDest "BoringStuff.yml") -Force
    Write-Host "✅ Configuration ready!"
}

# 3. Add 'boring' shortcut to activate this venv (PowerShell profile only -
# a .bat file can't do this, since activation has to happen in your current
# shell process rather than a child one)
Write-Host "Adding 'boring' activation shortcut to your PowerShell profile..." -ForegroundColor Yellow
$profileDir = Split-Path $PROFILE
if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}
if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
}

$marker = "# BoringStuff: activate shortcut"
$profileContent = [string](Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue)
if ($profileContent -notmatch [regex]::Escape($marker)) {
    $activateScript = Join-Path $repoPath ".venv\Scripts\Activate.ps1"
    $snippet = @"

$marker
function boring {
    param([Parameter(ValueFromRemainingArguments = `$true)] `$IgnoredArgs)
    & "$activateScript"
}
"@
    Add-Content -Path $PROFILE -Value $snippet -Encoding utf8
    Write-Host "✅ Added 'boring' command - run it (or 'boring 1', same thing) to activate this venv in any new terminal."
}
else {
    Write-Host "'boring' shortcut already present in profile, skipping."
}

Write-Host "`nSetup complete! Run your scripts using 'uv run <script_name>', or run 'boring' to activate the venv directly." -ForegroundColor Green