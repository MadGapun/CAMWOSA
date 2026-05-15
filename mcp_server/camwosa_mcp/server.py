"""CAMWOSA MCP-Server (FastMCP).

Bridge zur Backend-API auf http://127.0.0.1:8765.

Tools 1:1 zur UI-API gemaess MCP-First-Prinzip (siehe Wiki:
docs/wiki/Architektur.md#mcp-first-prinzip).
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastmcp import FastMCP


BACKEND_URL = os.environ.get("CAMWOSA_BACKEND_URL", "http://127.0.0.1:8765")

mcp = FastMCP(
    name="CAMWOSA",
    instructions="""
        Du bist mit einem CAMWOSA-Backend verbunden. CAMWOSA ist ein 2.5D CAM-Tool fuer
        GRBL-Maschinen (z.B. Genmitsu ProVerXL).

        Du kannst:
        - Maschinen, Werkzeuge, Materialien anzeigen
        - DXF-Dateien analysieren
        - CAM-Operationen anlegen (Kontur/Tasche/Bohren/Gravur)
        - Feeds & Speeds berechnen
        - Sicherheits-Checks ausfuehren
        - Verschnittoptimierung (Nesting) ausfuehren
        - .cwp-Projekte erzeugen und bearbeiten

        Wichtig:
        - Vor jeder G-Code-Erzeugung Sicherheits-Checks laufen lassen
        - Bei kritischen Warnungen User explizit fragen bevor Override
        - Auf Deutsch antworten (User spricht Deutsch)
    """,
)


def _get(pfad: str, **params) -> Any:
    with httpx.Client(timeout=60) as c:
        r = c.get(f"{BACKEND_URL}{pfad}", params=params)
        r.raise_for_status()
        return r.json()


def _post(pfad: str, json: dict) -> Any:
    with httpx.Client(timeout=120) as c:
        r = c.post(f"{BACKEND_URL}{pfad}", json=json)
        r.raise_for_status()
        return r.json()


# ---------------------------------------------------------------------------
# Maschinen / Werkzeuge / Material
# ---------------------------------------------------------------------------


@mcp.tool()
def maschinen_anzeigen() -> list[dict]:
    """Listet alle verfuegbaren Maschinen-Profile."""
    return _get("/api/machines/")


@mcp.tool()
def maschine_details(maschine_id: str) -> dict:
    """Details eines Maschinen-Profils."""
    return _get(f"/api/machines/{maschine_id}")


@mcp.tool()
def werkzeuge_anzeigen() -> list[dict]:
    """Listet alle Werkzeuge."""
    return _get("/api/tools/")


@mcp.tool()
def werkzeug_details(werkzeug_id: str) -> dict:
    """Details eines Werkzeugs."""
    return _get(f"/api/tools/{werkzeug_id}")


@mcp.tool()
def materialien_anzeigen() -> list[dict]:
    """Listet alle Materialien."""
    return _get("/api/materials/")


@mcp.tool()
def material_details(material_id: str) -> dict:
    """Details eines Materials inkl. Schnittparameter-Presets."""
    return _get(f"/api/materials/{material_id}")


# ---------------------------------------------------------------------------
# Feeds & Speeds
# ---------------------------------------------------------------------------


@mcp.tool()
def feeds_speeds_berechnen(
    maschine_id: str,
    werkzeug_id: str,
    material_id: str,
    rpm_wunsch: float | None = None,
) -> dict:
    """Berechnet optimale Schnittparameter fuer Werkzeug-Material-Maschinen-Kombi."""
    return _post("/api/feeds/berechnen", {
        "maschine_id": maschine_id,
        "werkzeug_id": werkzeug_id,
        "material_id": material_id,
        "rpm_wunsch": rpm_wunsch,
    })


# ---------------------------------------------------------------------------
# Postprozessoren
# ---------------------------------------------------------------------------


@mcp.tool()
def postprozessoren_anzeigen() -> list[dict]:
    """Listet alle verfuegbaren Postprozessoren."""
    return _get("/api/postprocessors/")


# ---------------------------------------------------------------------------
# CAM-Operationen
# ---------------------------------------------------------------------------


@mcp.tool()
def operation_kontur(
    werkzeug_id: str,
    geometrie: dict,
    parameter: dict,
) -> dict:
    """Erzeugt einen Kontur-Toolpath.

    Beispiel:
        operation_kontur(
            werkzeug_id="schaft_6mm_2s_hm",
            geometrie={"typ": "polylinie", "punkte": [[0,0],[100,0],[100,50],[0,50]],
                       "geschlossen": True, "layer": "KONTUR"},
            parameter={"spindel_rpm": 18000, "vorschub": 2000,
                       "eintauch_vorschub": 400, "max_tiefe": 6, "stepdown": 2,
                       "seite": "aussen"}
        )
    """
    return _post("/api/operations/kontur", {
        "werkzeug_id": werkzeug_id,
        "geometrie": geometrie,
        "parameter": {**parameter, "werkzeug_id": werkzeug_id},
    })


@mcp.tool()
def operation_tasche(werkzeug_id: str, geometrie: dict, parameter: dict) -> dict:
    """Erzeugt einen Tasche-Toolpath."""
    return _post("/api/operations/tasche", {
        "werkzeug_id": werkzeug_id,
        "geometrie": geometrie,
        "parameter": {**parameter, "werkzeug_id": werkzeug_id},
    })


@mcp.tool()
def operation_bohren(werkzeug_id: str, punkte: list, parameter: dict) -> dict:
    """Erzeugt einen Bohren-Toolpath. punkte: Liste von [x, y]."""
    return _post("/api/operations/bohren", {
        "werkzeug_id": werkzeug_id,
        "punkte": punkte,
        "parameter": {**parameter, "werkzeug_id": werkzeug_id},
    })


@mcp.tool()
def operation_gravur(werkzeug_id: str, geometrie: dict, parameter: dict) -> dict:
    """Erzeugt einen Gravur-Toolpath."""
    return _post("/api/operations/gravur", {
        "werkzeug_id": werkzeug_id,
        "geometrie": geometrie,
        "parameter": {**parameter, "werkzeug_id": werkzeug_id},
    })


@mcp.tool()
def gcode_erzeugen(
    maschine_id: str,
    werkzeug_id: str,
    toolpaths: list,
    postprozessor_id: str | None = None,
) -> dict:
    """Postprocesst eine Liste von Toolpaths zu G-Code."""
    return _post("/api/operations/postprocess", {
        "maschine_id": maschine_id,
        "werkzeug_id": werkzeug_id,
        "toolpaths": toolpaths,
        "postprozessor_id": postprozessor_id,
    })


# ---------------------------------------------------------------------------
# Sicherheits-Checks
# ---------------------------------------------------------------------------


@mcp.tool()
def sicherheits_pruefung(
    maschine_id: str,
    werkzeug_id: str,
    toolpath: dict,
    z_oberkante_material: float = 0.0,
) -> dict:
    """Prueft einen Toolpath auf Crash-Ursachen.

    WICHTIG: Vor jeder G-Code-Erzeugung aufrufen. Wenn ``hat_blocker``=true,
    den User explizit fragen bevor das Override-Flag gesetzt wird.
    """
    return _post("/api/safety/check", {
        "maschine_id": maschine_id,
        "werkzeug_id": werkzeug_id,
        "toolpath": toolpath,
        "z_oberkante_material": z_oberkante_material,
    })


# ---------------------------------------------------------------------------
# Nesting
# ---------------------------------------------------------------------------


@mcp.tool()
def nesting_starten(
    teile: list,
    platten: list,
    abstand_zwischen_teilen: float = 5.0,
) -> dict:
    """Verschnittoptimierung. Teile + Platten als Liste von Dicts."""
    return _post("/api/nesting/run", {
        "teile": teile,
        "platten": platten,
        "abstand_zwischen_teilen": abstand_zwischen_teilen,
    })


# ---------------------------------------------------------------------------
# DXF + Projekt
# ---------------------------------------------------------------------------


@mcp.tool()
def dxf_analysieren(dxf_pfad: str) -> dict:
    """Analysiert eine lokale DXF-Datei (Pfad muss fuer das Backend lesbar sein).

    Diese Funktion liest die Datei lokal ueber das Backend — der MCP-Aufrufer muss
    den Pfad relativ zum Backend nennen koennen.
    """
    # Vereinfachte Variante: Backend muss die Datei lesen koennen.
    # Spaeter: separater Endpoint mit Pfad statt Upload.
    raise NotImplementedError(
        "MCP-DXF-Analyse braucht direkten Datei-Pfad-Endpoint. "
        "Alternativ: DXF im UI importieren, dann Geometrie direkt mit MCP nutzen."
    )


@mcp.tool()
def projekt_neu(
    name: str,
    maschine_id: str,
    rohmaterial: dict,
    autor: str = "",
) -> dict:
    """Erzeugt ein neues, leeres Projekt."""
    return _post("/api/projects/new", {
        "name": name,
        "maschine_id": maschine_id,
        "rohmaterial": rohmaterial,
        "autor": autor,
    })


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@mcp.tool()
def backend_status() -> dict:
    """Backend-Health-Check. Sollte status='ok' und version zurueckgeben."""
    return _get("/health")


def main() -> None:
    """Startet den MCP-Server (stdio)."""
    mcp.run()


if __name__ == "__main__":
    main()
