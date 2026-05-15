"""Speichern und Laden von .cwp-Projektdateien.

Format:
- ZIP-Container mit:
  - manifest.json   (CWPProjekt als JSON)
  - geometry/       (eingebettete DXF/STL-Dateien)
  - gcode/          (generierte G-Code-Dateien, optional)
  - photos/         (Setup-Fotos, optional)

Versionierung:
- schema_version-Feld im Manifest
- Migration via project.migrate.migrate_cwp(...)
"""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import IO

from camwosa.project.schema import CWP_SCHEMA_VERSION, CWPProjekt


class CWPFehler(Exception):
    pass


_MANIFEST_NAME = "manifest.json"


def speichere_cwp(projekt: CWPProjekt, pfad: str | Path) -> Path:
    """Schreibt ein Projekt als .cwp-Datei."""
    pfad_obj = Path(pfad)
    pfad_obj.parent.mkdir(parents=True, exist_ok=True)
    projekt.metadaten.geaendert = datetime.now(timezone.utc)

    with zipfile.ZipFile(pfad_obj, "w", zipfile.ZIP_DEFLATED) as zf:
        manifest_json = projekt.model_dump_json(indent=2)
        zf.writestr(_MANIFEST_NAME, manifest_json)

        # Embedded DXF/STL-Dateien (wenn `eingebettete_datei` ein lokaler Pfad ist)
        for geo in projekt.geometrien:
            if geo.eingebettete_datei is None:
                continue
            quelle = Path(geo.eingebettete_datei)
            if quelle.exists():
                ziel = f"geometry/{geo.id}_{quelle.name}"
                zf.write(str(quelle), arcname=ziel)
    return pfad_obj


def lade_cwp(pfad: str | Path) -> CWPProjekt:
    """Liest eine .cwp-Datei und gibt das Projekt zurueck."""
    pfad_obj = Path(pfad)
    if not pfad_obj.exists():
        raise CWPFehler(f"Projektdatei nicht gefunden: {pfad_obj}")
    try:
        with zipfile.ZipFile(pfad_obj, "r") as zf:
            if _MANIFEST_NAME not in zf.namelist():
                raise CWPFehler("Kein manifest.json im .cwp-Container gefunden.")
            with zf.open(_MANIFEST_NAME) as f:
                manifest = json.load(f)
    except zipfile.BadZipFile as e:
        raise CWPFehler(f"Ungueltiger ZIP-Container: {e}") from e

    schema = int(manifest.get("schema_version", 0))
    if schema > CWP_SCHEMA_VERSION:
        raise CWPFehler(
            f"Projekt-Schema-Version {schema} ist neuer als unterstuetzt "
            f"({CWP_SCHEMA_VERSION}). Bitte CAMWOSA aktualisieren."
        )
    if schema < CWP_SCHEMA_VERSION:
        manifest = _migriere(manifest, von=schema, zu=CWP_SCHEMA_VERSION)

    return CWPProjekt.model_validate(manifest)


def extrahiere_geometrie(
    pfad: str | Path, geometrie_id: str, ziel_verzeichnis: str | Path
) -> Path:
    """Extrahiert eine eingebettete Geometrie-Datei."""
    pfad_obj = Path(pfad)
    ziel_obj = Path(ziel_verzeichnis)
    ziel_obj.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(pfad_obj, "r") as zf:
        for name in zf.namelist():
            if name.startswith(f"geometry/{geometrie_id}_"):
                ziel = ziel_obj / Path(name).name
                with zf.open(name) as src, ziel.open("wb") as dst:
                    dst.write(src.read())
                return ziel
    raise CWPFehler(f"Geometrie-ID {geometrie_id} nicht im Container gefunden.")


def auto_save(projekt: CWPProjekt, snapshot_dir: str | Path) -> Path:
    """Schreibt einen Auto-Save-Snapshot fuer Crash-Recovery."""
    snap = Path(snapshot_dir) / f"autosave_{projekt.metadaten.name}.cwp.tmp"
    return speichere_cwp(projekt, snap)


def _migriere(manifest: dict, *, von: int, zu: int) -> dict:
    """Schema-Migration. Bisher nur Stub — wird befuellt sobald Versionen existieren."""
    if von == 0 and zu == 1:
        manifest["schema_version"] = 1
    return manifest


__all__ = [
    "CWPFehler",
    "auto_save",
    "extrahiere_geometrie",
    "lade_cwp",
    "speichere_cwp",
]
