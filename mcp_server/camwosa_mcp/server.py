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


def _post_datei(pfad: str, datei_pfad: str, form: dict) -> Any:
    """POST multipart/form-data mit einer Datei (fuer Bild-Uploads)."""
    with open(datei_pfad, "rb") as fh:
        files = {"datei": (datei_pfad.rsplit("/", 1)[-1], fh)}
        data = {k: str(v) for k, v in form.items() if v is not None}
        with httpx.Client(timeout=120) as c:
            r = c.post(f"{BACKEND_URL}{pfad}", files=files, data=data)
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


@mcp.tool()
def spanausduennung_faktor(
    stepover_mm: float,
    werkzeug_durchmesser_mm: float,
    vorschub_mm_min: float | None = None,
) -> dict:
    """Spanausduennung / Chip Thinning (J3): Vorschub-Korrekturfaktor bei kleinem
    radialen Eingriff (ae < d/2, z.B. Adaptiv/Schlichten).

    Bei kleinem Stepover wird die reale Spandicke kleiner als der Zahnvorschub
    vermuten laesst → Vorschub muss erhoeht werden um die Soll-Spandicke (und
    damit Standzeit + Oberflaeche) zu halten. Liefert faktor (>=1.0) und, wenn
    vorschub_mm_min angegeben, den korrigierten Vorschub."""
    payload = {
        "stepover_mm": stepover_mm,
        "werkzeug_durchmesser_mm": werkzeug_durchmesser_mm,
    }
    if vorschub_mm_min is not None:
        payload["vorschub_mm_min"] = vorschub_mm_min
    return _post("/api/feeds/chip-thinning", payload)


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
    arc_fitting: bool = False,
    arc_toleranz_mm: float = 0.05,
    fahrweg_optimierung: bool = False,
    freifahrt_hoehe: float | None = None,
    modal: bool = False,
    rapid_safety: bool = False,
    spindel_hochlauf_s: float | None = None,
    rampe_eintauchen: bool = False,
    rampen_winkel_grad: float = 5.0,
    rampen_vorschub: float | None = None,
    rampen_vorschub_faktor: float = 1.0,
) -> dict:
    """Postprocesst eine Liste von Toolpaths zu G-Code.

    arc_fitting (J1): lineare Punktfolgen auf Kreisboegen → G2/G3.
    fahrweg_optimierung (J9): Schnitt-Gruppen per Nearest-Neighbor umsortieren
    (kurze Wege = kuerzere Zeit).
    freifahrt_hoehe (J10): Zwischen-Eilgaenge knapp ueber der Geometrie statt
    auf voller Sicherheitshoehe (mm, einstellbar; erste Anfahrt/Schluss bleiben
    sicher).
    modal (P2): redundante Achsworte/Feed/Bewegungs-Wort entfernen (kleinere Datei,
    kein Z-Jitter).
    rapid_safety (P3): diagonale Eilgaenge in sichere Reihenfolge splitten.
    spindel_hochlauf_s (P1): Hochlauf-Pause (G4 P) nach M3; None = aus aktiver
    Spindel (rampen_zeit_s)."""
    return _post("/api/operations/postprocess", {
        "maschine_id": maschine_id,
        "werkzeug_id": werkzeug_id,
        "toolpaths": toolpaths,
        "postprozessor_id": postprozessor_id,
        "arc_fitting": arc_fitting,
        "arc_toleranz_mm": arc_toleranz_mm,
        "fahrweg_optimierung": fahrweg_optimierung,
        "freifahrt_hoehe": freifahrt_hoehe,
        "modal": modal,
        "rapid_safety": rapid_safety,
        "spindel_hochlauf_s": spindel_hochlauf_s,
        "rampe_eintauchen": rampe_eintauchen,
        "rampen_winkel_grad": rampen_winkel_grad,
        "rampen_vorschub": rampen_vorschub,
        "rampen_vorschub_faktor": rampen_vorschub_faktor,
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


# ---------------------------------------------------------------------------
# Spezial-Operationen (alpha.5) + 3D-Frässtrategien (alpha.6, Cluster I)
# MCP-Paritaet zur REST-API.
# ---------------------------------------------------------------------------


@mcp.tool()
def operation_drag_engraving(parameter: dict, geometrie) -> dict:
    """Drag-Engraving / Schleppgravur mit Diamantgravierer (Spindel AUS).

    Werkzeug muss Typ DRAG_GRAVIERER oder DIAMANTGRAVIERER sein.
    Pflicht in ``parameter``: werkzeug_id. Optional: vorschub, eintauch_vorschub,
    tiefe, dwell_an_ecken_sekunden, ecken_winkel_schwelle_grad,
    lead_in_tangential_mm.

    ``geometrie``: einzelnes GeometrieObjekt-dict oder Liste davon
    (typ, layer, punkte, geschlossen)."""
    return _post("/api/spezial-ops/drag-engraving", {
        "parameter": parameter,
        "geometrie": geometrie,
    })


@mcp.tool()
def operation_auto_inlay(parameter: dict, geometrie: dict) -> dict:
    """Auto-Inlay: erzeugt Tasche + passenden Plug aus EINER geschlossenen Kontur.

    Pflicht in ``parameter``: werkzeug_radius_mm. Optional: spiel_mm,
    tasche_tiefe_mm, plug_uebermass_oben_mm.

    Liefert tasche_geometrie + plug_geometrie (als Polylinien) + Flaechen."""
    return _post("/api/spezial-ops/auto-inlay", {
        "parameter": parameter,
        "geometrie": geometrie,
    })


@mcp.tool()
def operation_thread_milling(parameter: dict) -> dict:
    """Thread-Milling / Gewindefraesen mit Helix-Bewegung.

    Pflicht in ``parameter``: werkzeug_id, spindel_rpm, vorschub,
    eintauch_vorschub, nenn_durchmesser, gewinde_steigung, gewinde_tiefe.
    Optional: art (innen/aussen), richtung (rechts/links), mittelpunkt_x/y,
    z_oberkante, segmente_pro_umdrehung."""
    return _post("/api/spezial-ops/thread-milling", {"parameter": parameter})


@mcp.tool()
def circular_pocket_pfade(parameter: dict) -> dict:
    """Circular-Pocketing: konzentrische Kreis-Spiralen.

    Pflicht in ``parameter``: aussen_radius, werkzeug_durchmesser.
    Optional: mittelpunkt_x/y, stepover_prozent, von_aussen_nach_innen,
    fertigungs_aufmass."""
    return _post("/api/spezial-ops/circular-pocket-pfade", parameter)


@mcp.tool()
def radial_pocket_pfade(parameter: dict) -> dict:
    """Radial-Pocketing: Sonnenstrahlen vom Mittelpunkt.

    Pflicht in ``parameter``: aussen_radius, werkzeug_durchmesser.
    Optional: mittelpunkt_x/y, anzahl_speichen, fertigungs_aufmass."""
    return _post("/api/spezial-ops/radial-pocket-pfade", parameter)


@mcp.tool()
def diagnose_z_grid(messpunkte: list[dict], werkzeug_typ: str = "schaftfraeser") -> dict:
    """Z-Grid-Diagnose: ist das Werkstueck eben aufgespannt?

    ``messpunkte``: Liste von {x, y, z} aus Z-Probing.
    ``werkzeug_typ``: beeinflusst die Schwellwerte (Schlicht-Werkzeuge strenger).

    Liefert Befund (eben_ok/leichte_neigung/starke_neigung/unebene_oberflaeche)
    + Klartext + Empfehlung + Neigung."""
    return _post("/api/diagnostics/z-grid", {
        "messpunkte": messpunkte,
        "werkzeug_typ": werkzeug_typ,
    })


@mcp.tool()
def operation_planfraesen(parameter: dict) -> dict:
    """Planfraesen / Face-Milling — rechteckige Flaeche ebnen (Cluster I1).

    Pflicht in ``parameter``: werkzeug_id, spindel_rpm, vorschub,
    eintauch_vorschub, x_max, y_max, abtrag. Optional: x_min, y_min, z_start,
    maximaler_stepdown, richtung (x/y), stepover_prozent, ueberstand_mm.

    Synergie mit Z-Grid-Diagnose: bei „unebene_oberflaeche" diese Op zum Planen."""
    return _post("/api/spezial-ops/planfraesen", {"parameter": parameter})


@mcp.tool()
def operation_3d_parallel(parameter: dict, heightmap: dict) -> dict:
    """3D-Parallel-Schlichten auf STL-Heightmap (Cluster I2).

    Pflicht in ``parameter``: werkzeug_id, spindel_rpm, vorschub,
    eintauch_vorschub. Optional: stepover_modus (distanz/scallop),
    stepover_distanz_mm, scallop_hoehe_mm, bahn_winkel_grad, aufmass_mm,
    toleranz_mm, zickzack.

    ``heightmap``: {shape, aufloesung, x_min, y_min, z_max, z_values_dtype,
    z_values_base64} — z.B. aus dem STL-Import oder Bild-zu-Heightmap.

    Werkzeug-Form wird beruecksichtigt (Kugel/Schaft/Torus)."""
    return _post("/api/spezial-ops/3d-parallel", {
        "parameter": parameter,
        "heightmap": heightmap,
    })


@mcp.tool()
def zeitschaetzung(
    toolpaths: list,
    maschine_id: str | None = None,
    eilgang_mm_min: float | None = None,
    overhead_faktor: float = 1.15,
    werkzeugwechsel_sekunden: float = 45.0,
) -> dict:
    """Schaetzt die Bearbeitungszeit einer Operation oder eines ganzen Jobs (K5).

    Schnitt- und Eilgang-Zeit getrennt, Werkzeugwechsel-Pausen, Beschleunigungs-
    Overhead. Liefert gesamt_sekunden/minuten + Klartext (z.B. "23 Min 12 Sek").

    Entweder maschine_id (nutzt deren Eilgang) ODER eilgang_mm_min angeben."""
    return _post("/api/operations/zeitschaetzung", {
        "toolpaths": toolpaths,
        "maschine_id": maschine_id,
        "eilgang_mm_min": eilgang_mm_min,
        "overhead_faktor": overhead_faktor,
        "werkzeugwechsel_sekunden": werkzeugwechsel_sekunden,
    })


@mcp.tool()
def bitmap_trace(
    datei_pfad: str,
    schwelle: float = 0.5,
    invertieren: bool = False,
    pixel_pro_mm: float = 4.0,
    ziel_breite_mm: float | None = None,
    glaettung_toleranz_mm: float = 0.2,
    min_flaeche_mm2: float = 1.0,
) -> dict:
    """Bitmap → Vektor-Schneid-Kontur (L1). Ein PNG/JPG-Logo (s/w) in 2D-Outlines
    zum Ausschneiden/Aushoehlen/Gravieren umwandeln.

    Anders als Bild-zu-Relief (3D-Heightmap) liefert dies 2D-Vektoren.
    schwelle: Graustufen-Schwelle 0-1. invertieren: helle statt dunkle Bereiche.
    ziel_breite_mm: skaliert die Ausgabe (None = aus Aufloesung).

    Liefert geschlossene Polylinien als GeometrieObjekte."""
    return _post_datei("/api/cad/bitmap-trace", datei_pfad, {
        "schwelle": schwelle,
        "invertieren": invertieren,
        "pixel_pro_mm": pixel_pro_mm,
        "ziel_breite_mm": ziel_breite_mm,
        "glaettung_toleranz_mm": glaettung_toleranz_mm,
        "min_flaeche_mm2": min_flaeche_mm2,
    })


def main() -> None:
    """Startet den MCP-Server (stdio)."""
    mcp.run()


if __name__ == "__main__":
    main()
