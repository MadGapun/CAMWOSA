# build.ps1 — Full Production Build CAMWOSA fuer Windows.
#
# Schritte:
#   1. Backend: PyInstaller-Bundle (camwosa-backend.exe + Lib + data)
#   2. Frontend: Vite-Production-Build
#   3. Electron: build:installer (electron-builder, NSIS)
#
# Output: electron/release/CAMWOSA Setup vX.Y.Z.exe

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

Write-Host ""
Write-Host "==> CAMWOSA Build" -ForegroundColor Cyan
Write-Host "Repo: $Repo" -ForegroundColor Gray
Write-Host ""

# ---------- 1/3 Backend ----------
Write-Host "==> 1/3 Backend: PyInstaller-Bundle" -ForegroundColor Cyan
Set-Location "$Repo\backend"
python -m pip install -q pyinstaller
if ($LASTEXITCODE -ne 0) { throw "pip install pyinstaller failed" }

python -m PyInstaller camwosa-backend.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

if (-not (Test-Path "$Repo\backend\dist\camwosa-backend\camwosa-backend.exe")) {
    throw "Backend-Bundle nicht gefunden — dist/camwosa-backend/camwosa-backend.exe fehlt"
}
Write-Host "  Backend OK -> backend\dist\camwosa-backend\" -ForegroundColor Green

# ---------- 2/3 Frontend ----------
Write-Host ""
Write-Host "==> 2/3 Frontend: Vite-Build" -ForegroundColor Cyan
Set-Location "$Repo\frontend"
if (-not (Test-Path "node_modules")) {
    npm install --legacy-peer-deps --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw "npm install (frontend) failed" }
}
npm run build
if ($LASTEXITCODE -ne 0) { throw "vite build failed" }
if (-not (Test-Path "$Repo\frontend\dist\index.html")) {
    throw "Frontend-Build nicht gefunden — frontend\dist\index.html fehlt"
}
Write-Host "  Frontend OK -> frontend\dist\" -ForegroundColor Green

# ---------- 3/3 Electron ----------
Write-Host ""
Write-Host "==> 3/3 Electron: Installer-Build" -ForegroundColor Cyan
Set-Location "$Repo\electron"
if (-not (Test-Path "node_modules")) {
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install (electron) failed" }
}
npm run build
if ($LASTEXITCODE -ne 0) { throw "tsc (electron) failed" }
npm run build:installer
if ($LASTEXITCODE -ne 0) { throw "electron-builder failed" }

# ---------- Done ----------
Write-Host ""
Write-Host "==> Fertig" -ForegroundColor Green
Get-ChildItem "$Repo\electron\release\*.exe" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host ("  -> {0}  ({1:N1} MB)" -f $_.FullName, ($_.Length / 1MB)) -ForegroundColor Green
}
Set-Location $Repo
