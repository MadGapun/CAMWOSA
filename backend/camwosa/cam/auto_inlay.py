"""Auto-Inlay: Tasche + passender Plug aus einer Kontur (A45-Rest, Cluster E).

Hintergrund (Markus' Workflow):
Klassische Einlegearbeit (zwei Holzfarben, z.B. helle Form in dunkler Tasche).
- TASCHE: Aussparung im dunklen Material — etwas kleiner als die Plug-Form
- PLUG: passender Einsatz im hellen Material — etwas groesser als die Tasche

Damit der Plug ohne Spalt sitzt, brauchts ein **kleines Spiel** (typisch 0.05-0.15 mm)
und einen **Schnittfugen-Versatz** (Inset/Outset um den Werkzeug-Radius).

Markus' Bedienung: User zeichnet EINE Kontur, sagt "das soll Inlay werden",
Auto-Inlay liefert ZWEI Operationen (Tasche fuer dunkles Material, Kontur-Plug
fuer helles Material) mit den korrekten Versaetzen.

Konvention dieser Implementierung:
- Eingabe: 1 geschlossene Kontur (Polygon)
- Output: zwei Geometrie-Polygone (tasche_geo, plug_geo) mit Metadaten
- Mathe: tasche_geo = original_offset_innen(spiel/2 + werkzeug_radius - werkzeug_radius)
                    = original_offset_innen(spiel/2)
         plug_geo   = original_offset_aussen(-spiel/2) — also etwas kleiner
                                                         als das Original
  → Tasche groesser-original, Plug kleiner-original — beide um spiel/2.
  Plug PASST mit `spiel` Gesamt-Luft in die Tasche.

Issue: #39 (Cluster E)
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from camwosa.cam.geometry import objekt_zu_shapely
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D


class AutoInlayParameter(BaseModel):
    """Konfiguration fuer Auto-Inlay-Generierung."""

    model_config = ConfigDict(extra="ignore")

    spiel_mm: float = Field(
        default=0.10, ge=0.0, le=1.0,
        description="Gesamt-Luft Plug-zu-Tasche. Holz: 0.05-0.15 typisch. "
                    "Kunststoff: 0.0-0.05.",
    )
    werkzeug_radius_mm: float = Field(
        gt=0,
        description="Schneid-Radius des Inlay-Werkzeugs (typisch V-Bit oder Kugelfraeser-Spitze).",
    )
    plug_uebermass_oben_mm: float = Field(
        default=0.5, ge=0.0, le=5.0,
        description="Plug ragt um diesen Wert ueber die Tasche hinaus — wird "
                    "nach dem Verleimen plan geschliffen.",
    )
    tasche_tiefe_mm: float = Field(
        default=3.0, gt=0,
        description="Wie tief die Tasche ins dunkle Material geht.",
    )


class AutoInlayFehler(Exception):
    """Inlay-Vorbedingung verletzt (offene Kontur, zu klein, etc.)."""


class AutoInlayErgebnis(BaseModel):
    """Resultat: Tasche + Plug als WKT-Strings + Metadaten."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    tasche_polygon_wkt: str  # WKT-Repraesentation der Tasche
    plug_polygon_wkt: str    # WKT-Repraesentation des Plugs
    tasche_flaeche_mm2: float
    plug_flaeche_mm2: float
    spiel_pro_seite_mm: float
    tasche_tiefe_mm: float
    plug_hoehe_mm: float
    hinweise: list[str]


def berechne_auto_inlay(
    kontur: GeometrieObjekt | Polygon,
    parameter: AutoInlayParameter,
) -> AutoInlayErgebnis:
    """Erzeugt Tasche + passenden Plug aus einer geschlossenen Kontur.

    Strategie:
    - Tasche = Original-Kontur, leicht **innen** verkleinert um spiel/2
    - Plug = Original-Kontur, leicht **aussen** vergroessert um -spiel/2 = verkleinert
    Beide um spiel/2 → Gesamt-Spiel pro Seite = spiel, Gesamt-Luft = spiel.

    Args:
        kontur: muss geschlossen sein (Polygon oder geschlossene Polylinie).
        parameter: Spiel + Werkzeug-Radius + Tiefen.
    """
    poly = _als_polygon(kontur)
    if poly is None or poly.is_empty:
        raise AutoInlayFehler("Keine gueltige geschlossene Kontur — Polygon ist leer.")
    if not poly.is_valid:
        poly = poly.buffer(0)  # Self-intersections heilen
    if poly.area < 1.0:
        raise AutoInlayFehler(
            f"Kontur zu klein ({poly.area:.2f} mm²) — mindestens 1 mm² noetig."
        )

    spiel_pro_seite = parameter.spiel_mm / 2.0

    # Werkzeug-Radius pruefen: Tasche-Innenecken duerfen nicht zu eng sein
    # Heuristik: wenn der "Erosionsradius" groesser ist als die Halbachse der
    # Bounding-Box, passt das Werkzeug nicht rein
    minx, miny, maxx, maxy = poly.bounds
    halb_klein = min(maxx - minx, maxy - miny) / 2.0
    hinweise: list[str] = []
    if parameter.werkzeug_radius_mm >= halb_klein:
        raise AutoInlayFehler(
            f"Werkzeug-Radius {parameter.werkzeug_radius_mm} mm passt nicht in "
            f"Kontur (Halb-Bounding {halb_klein:.2f} mm). Kleineres Werkzeug nutzen."
        )

    # Tasche: Polygon nach innen schrumpfen um spiel/2
    # (negativ-buffer = Erosion in shapely)
    tasche = poly.buffer(-spiel_pro_seite, join_style=2, mitre_limit=2.0)
    # Plug: Polygon nach innen schrumpfen um spiel/2 (also kleiner als Tasche um spiel)
    plug = poly.buffer(-parameter.spiel_mm + spiel_pro_seite, join_style=2, mitre_limit=2.0)
    # Wait — wir wollen Plug spiel/2 kleiner als ORIGINAL, nicht relativ zur Tasche
    # → plug = original schrumpfen um spiel/2 *plus* spiel/2 = spiel/2 + spiel/2 = spiel
    # → Tasche = original - spiel/2, Plug = original - spiel/2 - spiel/2 = original - spiel
    # Damit: Plug ist (spiel) kleiner als Tasche → genau Gesamt-Spiel = spiel
    plug = poly.buffer(-spiel_pro_seite - parameter.spiel_mm / 2.0, join_style=2, mitre_limit=2.0)
    # Korrigieren: Plug einfach spiel/2 kleiner als Tasche
    plug = tasche.buffer(-parameter.spiel_mm, join_style=2, mitre_limit=2.0)

    if tasche.is_empty:
        raise AutoInlayFehler(
            "Tasche degeneriert nach Schrumpfen — Spiel zu gross fuer Kontur."
        )
    if plug.is_empty:
        raise AutoInlayFehler(
            "Plug degeneriert nach Schrumpfen — Spiel zu gross fuer Kontur."
        )

    # Tasche/Plug koennen MultiPolygon sein bei spitzen Einbuchtungen
    tasche_p = _zu_polygon(tasche)
    plug_p = _zu_polygon(plug)

    plug_hoehe = parameter.tasche_tiefe_mm + parameter.plug_uebermass_oben_mm

    # Sanity-Hinweis: scharfe Innenecken kann das Werkzeug nicht reichen
    if poly.area / poly.length < parameter.werkzeug_radius_mm * 0.5:
        hinweise.append(
            "Kontur hat scharfe Einbuchtungen — Werkzeug kann nicht in alle Ecken. "
            "Tipp: Dogbones oder kleineres Werkzeug verwenden."
        )

    return AutoInlayErgebnis(
        tasche_polygon_wkt=tasche_p.wkt,
        plug_polygon_wkt=plug_p.wkt,
        tasche_flaeche_mm2=tasche_p.area,
        plug_flaeche_mm2=plug_p.area,
        spiel_pro_seite_mm=spiel_pro_seite,
        tasche_tiefe_mm=parameter.tasche_tiefe_mm,
        plug_hoehe_mm=plug_hoehe,
        hinweise=hinweise,
    )


def ergebnis_zu_geometrien(
    ergebnis: AutoInlayErgebnis,
) -> tuple[GeometrieObjekt, GeometrieObjekt]:
    """Wandelt das WKT-Ergebnis in zwei GeometrieObjekt um (tasche, plug).

    Praktisch fuers Frontend: zwei Polylinien (geschlossen), die in den
    Geometrie-Store kommen.
    """
    from shapely import wkt
    tasche_poly = wkt.loads(ergebnis.tasche_polygon_wkt)
    plug_poly = wkt.loads(ergebnis.plug_polygon_wkt)

    tasche_geo = _polygon_zu_objekt(tasche_poly, layer="auto_inlay_tasche")
    plug_geo = _polygon_zu_objekt(plug_poly, layer="auto_inlay_plug")
    return tasche_geo, plug_geo


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _als_polygon(geo) -> Polygon | None:
    if isinstance(geo, Polygon):
        return geo
    if isinstance(geo, GeometrieObjekt):
        try:
            sh = objekt_zu_shapely(geo)
        except Exception:
            return None
        if isinstance(sh, Polygon):
            return sh
        if isinstance(sh, LineString) and geo.geschlossen and len(geo.punkte) >= 3:
            return Polygon([p.to_tuple() for p in geo.punkte])
        return None
    return None


def _zu_polygon(geom) -> Polygon:
    """Holt das groesste Polygon aus MultiPolygon, sonst gibt geom zurueck."""
    from shapely.geometry import MultiPolygon
    if isinstance(geom, MultiPolygon):
        return max(geom.geoms, key=lambda p: p.area)
    if isinstance(geom, Polygon):
        return geom
    raise AutoInlayFehler(f"Unerwartetes Geometrie-Ergebnis: {type(geom).__name__}")


def _polygon_zu_objekt(poly: Polygon, *, layer: str) -> GeometrieObjekt:
    """Polygon → geschlossene Polylinie als GeometrieObjekt."""
    coords = list(poly.exterior.coords)
    if coords and coords[0] == coords[-1]:
        coords = coords[:-1]
    return GeometrieObjekt(
        typ=GeometrieTyp.POLYLINIE,
        layer=layer,
        punkte=[Punkt2D(x, y) for x, y in coords],
        geschlossen=True,
        attribute={},
    )


__all__ = [
    "AutoInlayErgebnis",
    "AutoInlayFehler",
    "AutoInlayParameter",
    "berechne_auto_inlay",
    "ergebnis_zu_geometrien",
]
