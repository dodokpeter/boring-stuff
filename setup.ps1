# lean-setup.ps1
Write-Host "🚀 Initializing BoringStuff with uv..." -ForegroundColor Cyan

$repoPath = Get-Location
$configDest = Join-Path $HOME "boring-stuff"

# 1. Sync Dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
uv sync

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

Write-Host "`nSetup complete! Run your scripts using 'uv run <script_name>'" -ForegroundColor Green