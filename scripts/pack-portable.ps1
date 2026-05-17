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
$Version = "0.0.1-alpha.0"
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
# package.json (nur die Felder die Electron braucht)
$pkg = @{
    name = "camwosa"
    version = $Version
    main = "dist/main.js"
    productName = $AppName
    description = "CAMWOSA - 2.5D CAM Tool"
}
$pkg | ConvertTo-Json | Out-File -FilePath "$AppDir\package.json" -Encoding UTF8 -NoNewline
# Electron-Code
New-Item -ItemType Directory -Path "$AppDir\dist" -Force | Out-Null
Copy-Item -Force "$Repo\electron\dist\*.js" "$AppDir\dist\"
# electron-updater + dependencies muessen mit (lazy-loaded zur Laufzeit)
New-Item -ItemType Directory -Path "$AppDir\node_modules" -Force | Out-Null
if (Test-Path "$Repo\electron\node_modules\electron-updater") {
    Copy-Item -Recurse -Force "$Repo\electron\node_modules\electron-updater" "$AppDir\node_modules\"
    # transitive deps von electron-updater (builder-util-runtime, lodash, etc.) auch mitnehmen
    @("builder-util-runtime", "fs-extra", "graceful-fs", "jsonfile", "universalify",
      "js-yaml", "argparse", "sprintf-js", "lazy-val", "semver", "lodash.escaperegexp",
      "lodash.isequal", "tiny-typed-emitter", "debug", "ms", "@types") | ForEach-Object {
        $src = "$Repo\electron\node_modules\$_"
        if (Test-Path $src) {
            Copy-Item -Recurse -Force $src "$AppDir\node_modules\" -ErrorAction SilentlyContinue
        }
    }
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

# Ergebnis
$bytes = (Get-Item $ZipPath).Length
$mb = [math]::Round($bytes / 1MB, 1)
Write-Host ""
Write-Host "==> Fertig" -ForegroundColor Green
Write-Host "  Verzeichnis : $OutDir" -ForegroundColor Gray
Write-Host "  ZIP         : $ZipPath ($mb MB)" -ForegroundColor Gray
