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


def _put(pfad: str, json: dict) -> Any:
    with httpx.Client(timeout=120) as c:
        r = c.put(f"{BACKEND_URL}{pfad}", json=json)
        r.raise_for_status()
        return r.json()


def _delete(pfad: str) -> Any:
    with httpx.Client(timeout=60) as c:
        r = c.delete(f"{BACKEND_URL}{pfad}")
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
def operation_wrap(
    werkzeug_id: str,
    punkte_xy: list[list[float]],
    parameter: dict,
) -> dict:
    """Wrap-Mode: 2D-Design auf einen rotierenden Zylinder wickeln.

    Industrie-Standard fuer Gravur/Schriftzug/Kontur auf rundem Werkstueck.
    Y-Bewegungen werden zu A-Achsen-Winkeln umgerechnet
    (A_grad = Y_mm × 57.2958 / Radius). Im G-Code stehen X+Y(=A°)+Z simultan
    pro Bewegung.

    Pflicht in ``parameter``: werkzeug_id, spindel_rpm, vorschub,
    eintauch_vorschub, werkstueck_radius_mm, max_tiefe. Optional: stepdown,
    sicherheitshoehe, geschlossen.

    Unterscheidet sich von ``operation_drechseln``: dort dreht das Werkstueck
    extern kontinuierlich, hier werden A-Werte explizit im G-Code ausgegeben.
    Wrap ist fuer Gravuren/Konturen auf zylindrischer Aussenflaeche,
    Drechseln fuer rotationssymmetrische Formgebung."""
    return _post("/api/operations/wrap", {
        "werkzeug_id": werkzeug_id,
        "punkte_xy": punkte_xy,
        "parameter": parameter,
    })


@mcp.tool()
def wrap_pruefe_design(
    punkte_xy: list[list[float]],
    werkstueck_radius_mm: float,
) -> dict:
    """Sicherheits-Pruefung fuer Wrap-Design vor dem Erzeugen."""
    return _post("/api/operations/wrap/pruefe", {
        "punkte_xy": punkte_xy,
        "werkstueck_radius_mm": werkstueck_radius_mm,
    })


@mcp.tool()
def operation_drechseln(werkzeug_id: str, parameter: dict) -> dict:
    """Drechsel-Operation auf der Rotary-Achse (X-Bewegung entlang Werkstueck,
    Z = Radius, A-Achse rotiert kontinuierlich mit ``drehzahl_werkstueck_upm``).

    Pflicht in ``parameter``: werkzeug_id, spindel_rpm, vorschub,
    eintauch_vorschub, max_tiefe, stepdown, rohmaterial_radius_mm, profil
    (Liste von [laenge_x_mm, radius_mm]).

    Optional: strategie (laengs_schruppen / profil_schlichten /
    schrupp_und_schlicht), aufmass_schlichten_mm, schlicht_zustellung_mm,
    drehzahl_werkstueck_upm."""
    return _post("/api/operations/drechseln", {
        "werkzeug_id": werkzeug_id,
        "parameter": parameter,
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


# ---------------------------------------------------------------------------
# Werkzeug-CRUD + Smart-Helpers
# ---------------------------------------------------------------------------


@mcp.tool()
def werkzeug_anlegen(werkzeug: dict) -> dict:
    """Legt ein neues Werkzeug an (oder ueberschreibt es bei gleicher ID).

    Pflicht: id, name, typ, durchmesser, schaft_durchmesser, schneidlaenge,
    gesamtlaenge, schneiden. Optional: spitzenwinkel, spitzendurchmesser,
    max_arbeitstiefe_mm, segmente, halter_segmente, standzeit_max_minuten.
    """
    return _post("/api/tools/", werkzeug)


@mcp.tool()
def werkzeug_aktualisieren(werkzeug_id: str, werkzeug: dict) -> dict:
    """Aktualisiert ein Werkzeug. Die ID aus dem URL gewinnt gegen die im Body."""
    return _put(f"/api/tools/{werkzeug_id}", werkzeug)


@mcp.tool()
def werkzeug_loeschen(werkzeug_id: str) -> dict:
    """Loescht ein User-Werkzeug. Default-Werkzeuge (aus Sammel-Datei) sind nicht loeschbar — Override mit gleicher ID anlegen."""
    return _delete(f"/api/tools/{werkzeug_id}")


@mcp.tool()
def v_bit_winkel_berechnen(
    spitzendurchmesser_mm: float,
    durchmesser_max_mm: float,
    schneidlaenge_mm: float,
) -> dict:
    """Smart-Helper: berechnet bei V-Bit/Gravurstichel den Spitzenwinkel aus
    Spitzendurchmesser, Schneid-Durchmesser und Schneidlaenge."""
    return _post("/api/tools/helper/v-bit-winkel", {
        "spitzendurchmesser_mm": spitzendurchmesser_mm,
        "durchmesser_max_mm": durchmesser_max_mm,
        "schneidlaenge_mm": schneidlaenge_mm,
    })


@mcp.tool()
def v_bit_spitzendurchmesser_berechnen(
    spitzenwinkel_grad: float,
    schneidlaenge_mm: float,
    durchmesser_max_mm: float,
) -> dict:
    """Smart-Helper: berechnet bei V-Bit den Spitzendurchmesser aus Winkel,
    Schneidlaenge und Max-Durchmesser. 0 bedeutet die Spitze laeuft auf einen
    echten Punkt aus."""
    return _post("/api/tools/helper/v-bit-spitzendurchmesser", {
        "spitzenwinkel_grad": spitzenwinkel_grad,
        "schneidlaenge_mm": schneidlaenge_mm,
        "durchmesser_max_mm": durchmesser_max_mm,
    })


# ---------------------------------------------------------------------------
# Material-CRUD
# ---------------------------------------------------------------------------


@mcp.tool()
def material_anlegen(material: dict) -> dict:
    """Legt ein neues Material an."""
    return _post("/api/materials/", material)


@mcp.tool()
def material_aktualisieren(material_id: str, material: dict) -> dict:
    """Aktualisiert ein Material."""
    return _put(f"/api/materials/{material_id}", material)


@mcp.tool()
def material_loeschen(material_id: str) -> dict:
    """Loescht ein User-Material."""
    return _delete(f"/api/materials/{material_id}")


# ---------------------------------------------------------------------------
# CuttingPreset (separate Top-Level-Entitaet)
# ---------------------------------------------------------------------------


@mcp.tool()
def cutting_presets_anzeigen(
    material_id: str | None = None,
    werkzeug_id: str | None = None,
    operation_typ: str | None = None,
) -> list[dict]:
    """Listet CuttingPresets. Optional gefiltert nach material_id, werkzeug_id,
    operation_typ (generic/kontur/tasche/gravur/bohren/relief/schruppen/schlichten)."""
    params = {}
    if material_id: params["material_id"] = material_id
    if werkzeug_id: params["werkzeug_id"] = werkzeug_id
    if operation_typ: params["operation_typ"] = operation_typ
    return _get("/api/cutting-presets/", **params)


@mcp.tool()
def cutting_preset_lookup(
    material_id: str,
    werkzeug_id: str,
    operation_typ: str = "generic",
) -> dict:
    """Findet das beste Preset fuer (material, werkzeug, operation).

    Fallback-Reihenfolge: exakt -> generic -> 404. Antwortet mit
    {gefunden: bool, preset: {...}}."""
    return _post("/api/cutting-presets/lookup", {
        "material_id": material_id,
        "werkzeug_id": werkzeug_id,
        "operation_typ": operation_typ,
    })


@mcp.tool()
def cutting_preset_anlegen(preset: dict) -> dict:
    """Legt ein neues CuttingPreset an. Pflicht: id, material_id, werkzeug_id,
    rpm, vorschub, plunge, stepdown, stepover_prozent. Optional: operation_typ."""
    return _post("/api/cutting-presets/", preset)


@mcp.tool()
def cutting_preset_loeschen(preset_id: str) -> dict:
    """Loescht ein User-CuttingPreset (Legacy-Presets sind nicht loeschbar)."""
    return _delete(f"/api/cutting-presets/{preset_id}")


# ---------------------------------------------------------------------------
# QuickCAM-Templates
# ---------------------------------------------------------------------------


@mcp.tool()
def quickcam_templates() -> list[dict]:
    """Listet alle QuickCAM-Templates (Tasche, Schriftzug, Bohrlochmuster, Kontur)
    mit ihren Eingabe-Schemas."""
    return _get("/api/quickcam/templates")


@mcp.tool()
def quickcam_erzeugen(
    template_id: str,
    eingaben: dict,
    maschine_id: str,
    werkzeug_id: str,
    material_id: str,
    projekt_name: str = "QuickCAM-Projekt",
) -> dict:
    """Erzeugt aus einem Template + Maschine + Werkzeug + Material ein
    lauffaehiges CWPProjekt. Werte werden automatisch aus dem passenden
    CuttingPreset gezogen."""
    return _post("/api/quickcam/erzeugen", {
        "template_id": template_id,
        "eingaben": eingaben,
        "maschine_id": maschine_id,
        "werkzeug_id": werkzeug_id,
        "material_id": material_id,
        "projekt_name": projekt_name,
    })


# ---------------------------------------------------------------------------
# Geometrie-Annotationen
# ---------------------------------------------------------------------------


@mcp.tool()
def heightmap_aus_bild_statistik(
    bild_base64: str,
    max_tiefe_mm: float = 3.0,
    pixel_pro_mm: float = 5.0,
) -> dict:
    """Wandelt ein Bild (als base64-string) in eine Heightmap-Statistik um.

    Antwortet mit ``{shape_x, shape_y, anzahl_pixel, breite_mm, hoehe_mm,
    z_min, z_max, z_mittel, max_tiefe_mm}`` — schneller Sanity-Check vor
    der Toolpath-Erzeugung.

    Achtung: das volle Z-Array wird NICHT zurueckgegeben (zu gross fuer MCP-
    Antworten). Fuer den Toolpath nutze ``/api/heightmap/aus-bild`` per HTTP-
    Upload."""
    import base64
    from camwosa.stl.bild_heightmap import (
        BildHeightmapParameter, heightmap_aus_bild, heightmap_statistik,
    )
    bild = base64.b64decode(bild_base64)
    hm = heightmap_aus_bild(bild, BildHeightmapParameter(
        max_tiefe_mm=max_tiefe_mm, pixel_pro_mm=pixel_pro_mm,
    ))
    return heightmap_statistik(hm)


@mcp.tool()
def auto_cam_erstellen(
    aufgabe: str,
    name: str,
    maschine_id: str,
    material_id: str,
    werkzeug_ids: list[str] | None = None,
    parameter: dict | None = None,
) -> dict:
    """Erzeugt aus einer High-Level-Aufgabe ein komplettes Projekt.

    ``aufgabe`` ist eines von:
    - ``tasche`` — rechteckige Tasche mit Schruppen+Schlichten wenn tief genug.
      Parameter: ``breite_mm``, ``hoehe_mm``, ``tiefe_mm``, ``werkzeug_durchmesser_mm``, ``material_haerte``
    - ``anschlagbohrungen`` — 4 Loecher in den Ecken.
      Parameter: ``werkstueck_breite_mm``, ``werkstueck_hoehe_mm``, ``randabstand_mm``, ``durchmesser_mm``, ``tiefe_mm``
    - ``beschriftung_wrap`` — Text auf Rundmaterial wickeln.
      Parameter: ``text``, ``werkstueck_radius_mm``, ``gravur_tiefe_mm``

    Heuristik trifft die wichtigen Entscheidungen automatisch:
    - Schruppen+Schlichten ab Tiefe X (Material-abhaengig)
    - Werkzeug-Wahl nach Durchmesser-Naehe + Typ-Praeferenz
    - Multi-Tool-Workflow mit ArbeitsSchritt-Liste + Werkzeugwechsel-Eintrag

    Antwortet mit fertigem CWPProjekt + Liste der getroffenen Entscheidungen
    (`hinweise`)."""
    from camwosa.db.loader import (
        lade_maschinen, lade_materialien, lade_werkzeuge,
    )
    from camwosa.workflow.auto_cam import AufgabenTyp, auto_cam_erstellen as _auto_cam

    maschinen = {m.id: m for m in lade_maschinen()}
    materialien = {m.id: m for m in lade_materialien()}
    werkzeuge_alle = lade_werkzeuge()
    if werkzeug_ids:
        werkzeuge = [w for w in werkzeuge_alle if w.id in set(werkzeug_ids)]
    else:
        werkzeuge = werkzeuge_alle

    if maschine_id not in maschinen:
        return {"fehler": f"Maschine '{maschine_id}' unbekannt"}
    if material_id not in materialien:
        return {"fehler": f"Material '{material_id}' unbekannt"}

    try:
        aufg_enum = AufgabenTyp(aufgabe)
    except ValueError:
        return {"fehler": f"Aufgaben-Typ '{aufgabe}' unbekannt", "erlaubt": [a.value for a in AufgabenTyp]}

    try:
        erg = _auto_cam(
            aufg_enum,
            name=name,
            maschine=maschinen[maschine_id],
            material=materialien[material_id],
            werkzeuge=werkzeuge,
            parameter=parameter or {},
        )
    except Exception as e:  # noqa: BLE001
        return {"fehler": str(e)}

    return {
        "projekt": erg.projekt.model_dump(mode="json"),
        "hinweise": erg.hinweise,
    }


@mcp.tool()
def material_abtrag_simulieren(
    toolpaths: list[dict],
    werkzeug_id: str,
    werkstueck: dict,
    aufloesung_mm: float = 2.0,
    z_oberkante_material: float | None = None,
) -> dict:
    """Voxel-basierte Material-Abtrag-Simulation.

    Laesst die uebergebenen Toolpaths durch ein Werkstueck-Grid laufen und
    gibt die sichtbare Oberflaeche (Boundary-Voxel) + Volumen-Statistiken
    zurueck.

    Parameter:
    - toolpaths: Liste von Toolpath-Dicts (wie von operation_*-Tools geliefert)
    - werkzeug_id: ID des aktiven Werkzeugs
    - werkstueck: ``{laenge_x, breite_y, hoehe_z, nullpunkt_x?, nullpunkt_y?}``
    - aufloesung_mm: Voxel-Kantenlaenge (0.5 - 10, Default 2.0)
    - z_oberkante_material: optional, Default = werkstueck.hoehe_z

    Antwortet mit Boundary-Voxel-Liste + abgetragenem Volumen."""
    body: dict = {
        "toolpaths": toolpaths,
        "werkzeug_id": werkzeug_id,
        "werkstueck": werkstueck,
        "aufloesung_mm": aufloesung_mm,
    }
    if z_oberkante_material is not None:
        body["z_oberkante_material"] = z_oberkante_material
    return _post("/api/simulation/voxel", body)


@mcp.tool()
def annotation_typen() -> list[str]:
    """Liste der unterstuetzten Annotation-Typen
    (anschlagbohrung/refpunkt/kommentar/ausschnitt)."""
    return _get("/api/annotationen/typen")


@mcp.tool()
def annotationen_validieren(annotationen: list[dict]) -> dict:
    """Validiert eine ganze Annotation-Liste auf einmal — mit Dedup ueber id
    und Sammel-Fehlerbericht."""
    return _post("/api/annotationen/validate-liste", {"annotationen": annotationen})


@mcp.tool()
def annotationen_zu_operationen(
    annotationen: list[dict],
    werkzeug_ids: list[str] | None = None,
) -> dict:
    """Wandelt eine Annotation-Liste in CAM-Operationen um.

    - Anschlagbohrungen werden nach (Tiefe, Durchmesser) gruppiert → je eine
      Bohren-Operation pro Gruppe.
    - Ausschnitte → eine Tasche-Operation pro Punkt.
    - Refpunkte/Kommentare werden ignoriert.

    Mit ``werkzeug_ids`` kann die Werkzeug-Auswahl eingeschraenkt werden.
    Antwortet mit ``{operationen, hinweise}``."""
    body: dict = {"annotationen": annotationen}
    if werkzeug_ids:
        body["werkzeug_ids"] = werkzeug_ids
    return _post("/api/annotationen/zu-operationen", body)


# ---------------------------------------------------------------------------
# Spindel-CRUD
# ---------------------------------------------------------------------------


@mcp.tool()
def spindeln_anzeigen() -> list[dict]:
    """Listet alle verfuegbaren Spindeln."""
    return _get("/api/spindles/")


@mcp.tool()
def spindel_anlegen(spindel: dict) -> dict:
    """Legt eine neue Spindel an."""
    return _post("/api/spindles/", spindel)


@mcp.tool()
def spindel_loeschen(spindel_id: str) -> dict:
    """Loescht eine User-Spindel."""
    return _delete(f"/api/spindles/{spindel_id}")


def main() -> None:
    """Startet den MCP-Server (stdio)."""
    mcp.run()


if __name__ == "__main__":
    main()
