#!/usr/bin/env bash
#
# build.sh — Full Production Build CAMWOSA.
#
# Schritte:
#   1. Backend: PyInstaller-Bundle erzeugen
#   2. Frontend: Vite-Production-Build
#   3. Electron: build:installer (electron-builder)
#
# Output: electron/release/CAMWOSA Setup vX.Y.Z.exe (Win) / .dmg (Mac) / .AppImage (Linux)

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

echo "==> 1/3 Backend: PyInstaller-Bundle"
cd backend
pip install -q pyinstaller
pyinstaller camwosa-backend.spec --clean --noconfirm
cd ..

echo "==> 2/3 Frontend: Vite-Build"
cd frontend
npm ci
npm run build
cd ..

echo "==> 3/3 Electron: Installer-Build"
cd electron
npm ci
npm run build
npm run build:installer
cd ..

echo "Fertig — Output in electron/release/"
