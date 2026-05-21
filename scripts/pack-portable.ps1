# pack-portable.ps1 — Baut ein portables Windows-Bundle als ZIP.
#
# Loest das winCodeSign-Symlink-Problem auf Windows ohne Admin/Dev-Mode,
# das electron-builder bei vielen Setups stoppt.
#
# Output:
#   dist-portable/CAMWOSA-win32-x64/            (entpackbar, doppelt-klickbar)
#   dist-portable/CAMWOSA-0.0.1-alpha.0-portable.zip
#
# Voraussetzungen (jeweils vorher bauen):
#   1. backend/dist/camwosa-backend/         (PyInstaller)
#   2. frontend/dist/index.html              (Vite build)
#   3. electron/dist/main.js                 (tsc)
#   4. electron/node_modules/electron/dist/electron.exe   (npm install)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
$Version = "0.0.1-alpha.7"
$AppName = "CAMWOSA"
$OutDir = "$Repo\electron\dist-portable\$AppName-win32-x64"
$ZipPath = "$Repo\electron\dist-portable\$AppName-$Version-portable.zip"

Write-Host ""
Write-Host "==> CAMWOSA Portable-Pack v$Version" -ForegroundColor Cyan

# Voraussetzungen pruefen
$checks = @(
    @{ Path = "$Repo\backend\dist\camwosa-backend\camwosa-backend.exe";    Name = "Backend-Bundle (PyInstaller)" }
    @{ Path = "$Repo\frontend\dist\index.html";                            Name = "Frontend-Build (Vite)" }
    @{ Path = "$Repo\electron\dist\main.js";                               Name = "Electron-tsc Output" }
    @{ Path = "$Repo\electron\node_modules\electron\dist\electron.exe";    Name = "Electron-Runtime" }
)
foreach ($c in $checks) {
    if (-not (Test-Path $c.Path)) {
        throw "Fehlt: $($c.Name) -> $($c.Path)"
    }
    Write-Host "  ok $($c.Name)" -ForegroundColor Gray
}

# Ausgabe-Verzeichnis sauber anlegen
if (Test-Path $OutDir) {
    Remove-Item -Recurse -Force $OutDir
}
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

# 1) Electron-Runtime kopieren (electron.exe + Lib)
Write-Host ""
Write-Host "==> 1/4 Electron-Runtime kopieren" -ForegroundColor Cyan
Copy-Item -Recurse -Force "$Repo\electron\node_modules\electron\dist\*" $OutDir
# electron.exe umbenennen zu CAMWOSA.exe (Desktop-Verknuepfung freundlich)
Rename-Item "$OutDir\electron.exe" "$AppName.exe"

# 2) App in resources\app\ ablegen (ohne asar, damit Markus dev-debuggen kann)
Write-Host "==> 2/4 App in resources\app\" -ForegroundColor Cyan
$AppDir = "$OutDir\resources\app"
New-Item -ItemType Directory -Path $AppDir -Force | Out-Null
# package.json (nur die Felder die Electron braucht — KEINE devDependencies)
$pkg = @{
    name = "camwosa"
    version = $Version
    main = "dist/main.js"
    productName = $AppName
    description = "CAMWOSA - 2.5D CAM Tool"
    dependencies = @{
        "electron-updater" = "^6.1.0"
    }
}
$pkg | ConvertTo-Json -Depth 10 | Out-File -FilePath "$AppDir\package.json" -Encoding UTF8 -NoNewline
# Electron-Code
New-Item -ItemType Directory -Path "$AppDir\dist" -Force | Out-Null
Copy-Item -Force "$Repo\electron\dist\*.js" "$AppDir\dist\"

# Production-only node_modules via npm install in der Bundle-App.
# Vorher npm-Cache deaktivieren damit es deterministisch ist.
Write-Host "  npm install --omit=dev in resources\app\ ..."
Push-Location $AppDir
$env:NPM_CONFIG_AUDIT = "false"
$env:NPM_CONFIG_FUND = "false"
npm install --omit=dev --omit=optional --no-package-lock --silent 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    throw "npm install --omit=dev in $AppDir failed"
}
Pop-Location
# Smoke-Check: sax muss da sein (transitiv von electron-updater)
if (-not (Test-Path "$AppDir\node_modules\sax")) {
    Write-Host "  WARNUNG: sax fehlt - electron-updater wird crashen" -ForegroundColor Yellow
} else {
    Write-Host "  ok node_modules komplett" -ForegroundColor Gray
}

# 3) Frontend in resources\app\frontend-dist\ (main.ts erwartet ../../frontend/dist)
Write-Host "==> 3/4 Frontend kopieren" -ForegroundColor Cyan
$FrontendDir = Join-Path (Split-Path -Parent $AppDir) "frontend-dist"
# Wait — main.js erwartet "../../frontend/dist/index.html" relativ zu __dirname (=resources\app\dist)
# Also: "../../frontend/dist" = "resources\frontend\dist". Wir legen es dorthin.
$FrontendTarget = "$OutDir\resources\frontend\dist"
New-Item -ItemType Directory -Path $FrontendTarget -Force | Out-Null
Copy-Item -Recurse -Force "$Repo\frontend\dist\*" $FrontendTarget

# 4) Backend-Bundle + data nach resources\
Write-Host "==> 4/4 Backend + data kopieren" -ForegroundColor Cyan
Copy-Item -Recurse -Force "$Repo\backend\dist\camwosa-backend" "$OutDir\resources\backend"
Copy-Item -Recurse -Force "$Repo\data" "$OutDir\resources\data"

# 5) app-update.yml fuer electron-updater (sonst gibt's ENOENT-Warning beim Start)
@"
provider: github
owner: MadGapun
repo: CAMWOSA
"@ | Out-File -FilePath "$OutDir\resources\app-update.yml" -Encoding ASCII

# README im Bundle
@"
CAMWOSA $Version (Alpha, portable)

Starten: Doppelklick auf $AppName.exe

Wenn Windows-Defender / SmartScreen warnt:
  - Klick "Weitere Informationen" -> "Trotzdem ausfuehren"
  - Build ist nicht signiert (Code-Signing ist Master-Plan F3)

Bekannte Einschraenkungen (Alpha):
  - Erste Inbetriebnahme dauert ~5-10 Sek (Backend-Subprozess startet)
  - Backend laeuft auf 127.0.0.1:8765 (oder naechster freier Port)
  - .cwp-Dateiverknuepfung muss manuell gesetzt werden

Wiki: https://github.com/MadGapun/CAMWOSA/blob/main/docs/wiki/Home.md
Bugs: https://github.com/MadGapun/CAMWOSA/issues
"@ | Out-File -FilePath "$OutDir\README.txt" -Encoding UTF8

# ZIP packen
Write-Host ""
Write-Host "==> ZIP packen" -ForegroundColor Cyan
if (Test-Path $ZipPath) {
    Remove-Item -Force $ZipPath
}
Compress-Archive -Path "$OutDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal

# Smoke-Test: Bundle in frischen Pfad entpacken + starten + DOM pruefen.
# Verhindert dass wir Bundles releasen wo der Renderer schwarz bleibt.
$skipSmoke = $env:CAMWOSA_PACK_SKIP_SMOKE -eq "1"
if (-not $skipSmoke) {
    Write-Host ""
    Write-Host "==> Smoke-Test (entpacken + starten + DOM pruefen)" -ForegroundColor Cyan
    Get-Process | Where-Object { $_.Name -in @('CAMWOSA','camwosa-backend','electron') } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    $smokeDir = "$env:TEMP\camwosa-pack-smoke"
    if (Test-Path $smokeDir) { Remove-Item -Recurse -Force $smokeDir -ErrorAction SilentlyContinue }
    Expand-Archive -Path $ZipPath -DestinationPath $smokeDir -Force
    $smokeOut = "$env:TEMP\camwosa-pack-smoke.log"
    "" | Out-File $smokeOut
    Start-Process -FilePath "$smokeDir\$AppName.exe" -RedirectStandardOutput $smokeOut -RedirectStandardError "$env:TEMP\camwosa-pack-smoke-err.log" | Out-Null
    Start-Sleep -Seconds 20  # 8s smoke + Buffer
    $out = Get-Content $smokeOut -Raw
    Get-Process | Where-Object { $_.Name -in @('CAMWOSA','camwosa-backend','electron') } | Stop-Process -Force -ErrorAction SilentlyContinue
    $smokeLine = ($out -split "`n") | Where-Object { $_ -match '\[smoke\] dom' } | Select-Object -First 1
    if (-not $smokeLine) {
        throw "Smoke-Test FAIL: kein '[smoke] dom'-Log nach 20s. stdout:`n$out"
    }
    $rootChildren = 0
    if ($smokeLine -match 'rootChildren=(\d+)') { $rootChildren = [int]$matches[1] }
    $bodyBytes = 0
    if ($smokeLine -match 'body=(\d+)B') { $bodyBytes = [int]$matches[1] }
    if ($rootChildren -lt 1 -or $bodyBytes -lt 500) {
        throw "Smoke-Test FAIL: Renderer leer (rootChildren=$rootChildren body=$bodyBytes). UI rendert nicht."
    }
    Write-Host "  ok Renderer aktiv (body=$bodyBytes B, root=$rootChildren child, smoke OK)" -ForegroundColor Green
}

# Ergebnis
$bytes = (Get-Item $ZipPath).Length
$mb = [math]::Round($bytes / 1MB, 1)
Write-Host ""
Write-Host "==> Fertig" -ForegroundColor Green
Write-Host "  Verzeichnis : $OutDir" -ForegroundColor Gray
Write-Host "  ZIP         : $ZipPath ($mb MB)" -ForegroundColor Gray
