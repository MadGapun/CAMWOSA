"""Quick-CAM-Templates fuer haeufige Einzelfraesaufgaben.

Jedes Template definiert:
- Was es macht (Tasche, Schriftzug, Bohrloch, Kontur)
- Welche Parameter der User pflegen muss (mit sinnvollen Defaults)
- Wie daraus ein lauffaehiges Projekt mit einem Setup + einer Operation entsteht

Ziel: in unter 60 Sekunden vom Programmstart zum lauffaehigen G-Code.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from camwosa.cam.parameter import (
    BohrStrategie,
    Eintauchstrategie,
    GravurStrategie,
    KonturSeite,
    TaschenStrategie,
)
from camwosa.db.cutting_presets import (
    OperationsTyp as CuttingOperationsTyp,
    finde_preset,
    lade_cutting_presets,
)
from camwosa.db.models import (
    Maschine,
    Material,
    ProjektMetadaten,
    Rohmaterial,
    RohmaterialForm,
    Werkzeug,
)
from camwosa.project.schema import (
    CWP_SCHEMA_VERSION,
    CWPProjekt,
    OperationsKonfig,
    Setup,
    Variante,
)
from camwosa.project.schritte import OperationSchritt


@dataclass
class TemplateParameter:
    """Beschreibung eines Eingabe-Parameters fuer das Frontend."""

    name: str
    label: str
    typ: str  # "float" | "int" | "text" | "punktliste"
    default: Any
    einheit: str = ""
    hinweis: str = ""


@dataclass
class QuickCAMTemplate:
    id: str
    name: str
    kurzbeschreibung: str
    icon: str  # Emoji oder Iconname
    operation_typ: str  # "tasche" | "gravur" | "bohren" | "kontur"
    parameter: list[TemplateParameter]
    erzeuge: Callable[[dict[str, Any]], dict[str, Any]]
    """``erzeuge(user_eingaben) -> dict mit 'parameter' (Pydantic-dump) + 'geometrie'``."""


# ---------------------------------------------------------------------------
# Template-Definitionen
# ---------------------------------------------------------------------------


def _tasche_rechteckig(e: dict[str, Any]) -> dict[str, Any]:
    breite = float(e["breite_mm"])
    hoehe = float(e["hoehe_mm"])
    return {
        "parameter_extras": {
            "max_tiefe": float(e["tiefe_mm"]),
            "stepdown": float(e.get("stepdown_mm", 2.0)),
            "stepover_prozent": float(e.get("stepover_prozent", 40.0)),
            "strategie": TaschenStrategie.OFFSET_KONTUR.value,
            "eintauch_strategie": Eintauchstrategie.RAMPE.value,
        },
        "geometrie": {
            "typ": "polylinie",
            "punkte": [
                [0, 0], [breite, 0], [breite, hoehe], [0, hoehe], [0, 0],
            ],
            "geschlossen": True,
        },
    }


def _gravur_text(e: dict[str, Any]) -> dict[str, Any]:
    return {
        "parameter_extras": {
            "max_tiefe": float(e.get("tiefe_mm", 0.5)),
            "stepdown": float(e.get("tiefe_mm", 0.5)),
            "strategie": GravurStrategie.KONSTANTE_TIEFE.value,
        },
        "geometrie": {
            "typ": "text",
            "text": str(e["text"]),
            "schriftart": str(e.get("schriftart", "default")),
            "groesse_mm": float(e.get("groesse_mm", 20.0)),
            "position": [
                float(e.get("x_mm", 0)), float(e.get("y_mm", 0)),
            ],
        },
    }


def _bohrloch_raster(e: dict[str, Any]) -> dict[str, Any]:
    spalten = int(e["spalten"])
    zeilen = int(e["zeilen"])
    dx = float(e["abstand_x_mm"])
    dy = float(e["abstand_y_mm"])
    punkte = [
        [c * dx, r * dy] for r in range(zeilen) for c in range(spalten)
    ]
    return {
        "parameter_extras": {
            "max_tiefe": float(e["tiefe_mm"]),
            "stepdown": min(float(e["tiefe_mm"]), 2.0),
            "strategie": BohrStrategie.PECK.value,
        },
        "geometrie": {
            "typ": "punktliste",
            "punkte": punkte,
        },
    }


def _kontur_ausschneiden(e: dict[str, Any]) -> dict[str, Any]:
    return {
        "parameter_extras": {
            "max_tiefe": float(e["tiefe_mm"]),
            "stepdown": float(e.get("stepdown_mm", 2.0)),
            "seite": KonturSeite.AUSSEN.value,
            "eintauch_strategie": Eintauchstrategie.RAMPE.value,
            "tabs_anzahl": int(e.get("tabs_anzahl", 4)),
            "tabs_hoehe": float(e.get("tabs_hoehe_mm", 1.5)),
        },
        "geometrie": {
            "typ": "rohgeometrie_dxf",
            "hinweis": "DXF-Datei separat importieren; Pfad/Layer im naechsten Schritt zuweisen",
        },
    }


_TEMPLATES: list[QuickCAMTemplate] = [
    QuickCAMTemplate(
        id="tasche_rechteckig",
        name="Rechteckige Tasche",
        kurzbeschreibung="Eine rechteckige Tasche an Position 0,0 — Maße + Tiefe eingeben.",
        icon="▭",
        operation_typ="tasche",
        parameter=[
            TemplateParameter("breite_mm", "Breite", "float", 50.0, "mm"),
            TemplateParameter("hoehe_mm", "Hoehe", "float", 30.0, "mm"),
            TemplateParameter("tiefe_mm", "Tiefe", "float", 5.0, "mm"),
            TemplateParameter("stepdown_mm", "Z-Pass", "float", 2.0, "mm",
                              "Wie viel pro Z-Schritt"),
            TemplateParameter("stepover_prozent", "Stepover", "float", 40.0, "%",
                              "Seitlicher Versatz in % vom Werkzeug-Ø"),
        ],
        erzeuge=_tasche_rechteckig,
    ),
    QuickCAMTemplate(
        id="gravur_text",
        name="Schriftzug gravieren",
        kurzbeschreibung="Text-Gravur an einer Position — Schrift + Groesse + Tiefe.",
        icon="✎",
        operation_typ="gravur",
        parameter=[
            TemplateParameter("text", "Text", "text", "Hallo"),
            TemplateParameter("groesse_mm", "Schriftgroesse", "float", 20.0, "mm"),
            TemplateParameter("tiefe_mm", "Gravur-Tiefe", "float", 0.5, "mm"),
            TemplateParameter("x_mm", "X-Position", "float", 0.0, "mm"),
            TemplateParameter("y_mm", "Y-Position", "float", 0.0, "mm"),
            TemplateParameter("schriftart", "Schriftart", "text", "default", "",
                              "Frontend bietet Auswahl an"),
        ],
        erzeuge=_gravur_text,
    ),
    QuickCAMTemplate(
        id="bohrloch_raster",
        name="Bohrloch-Raster",
        kurzbeschreibung="Bohrlochmuster (z.B. fuer Anschlagstifte) — Spalten x Zeilen.",
        icon="⋮⋮",
        operation_typ="bohren",
        parameter=[
            TemplateParameter("spalten", "Spalten", "int", 3),
            TemplateParameter("zeilen", "Zeilen", "int", 2),
            TemplateParameter("abstand_x_mm", "Abstand X", "float", 25.0, "mm"),
            TemplateParameter("abstand_y_mm", "Abstand Y", "float", 25.0, "mm"),
            TemplateParameter("tiefe_mm", "Bohr-Tiefe", "float", 10.0, "mm"),
        ],
        erzeuge=_bohrloch_raster,
    ),
    QuickCAMTemplate(
        id="kontur_ausschneiden",
        name="Kontur ausschneiden (mit Tabs)",
        kurzbeschreibung="Aussenkontur fraesen, Tabs lassen das Teil im Material bis zum Schluss.",
        icon="✂",
        operation_typ="kontur",
        parameter=[
            TemplateParameter("tiefe_mm", "Tiefe (= Materialstaerke)", "float", 6.0, "mm"),
            TemplateParameter("stepdown_mm", "Z-Pass", "float", 2.0, "mm"),
            TemplateParameter("tabs_anzahl", "Tabs", "int", 4, "",
                              "Anzahl Verbindungs-Stege"),
            TemplateParameter("tabs_hoehe_mm", "Tab-Hoehe", "float", 1.5, "mm"),
        ],
        erzeuge=_kontur_ausschneiden,
    ),
]


def _baue_operation_parameter(
    *,
    werkzeug: Werkzeug,
    material: Material,
    operation_typ: str,
    extras: dict[str, Any],
) -> dict[str, Any]:
    """Kombiniert Werkzeug-Defaults + CuttingPreset + Template-Extras zu vollstaendigem dict."""
    try:
        op_enum = CuttingOperationsTyp(operation_typ)
    except ValueError:
        op_enum = CuttingOperationsTyp.GENERIC

    preset = finde_preset(
        lade_cutting_presets(),
        material_id=material.id, werkzeug_id=werkzeug.id, operation_typ=op_enum,
    )
    if preset is not None:
        rpm = preset.rpm
        vorschub = preset.vorschub
        plunge = preset.plunge
        stepdown = preset.stepdown
    else:
        # Fallback aus Material.presets (Legacy)
        legacy = next((p for p in material.presets if p.werkzeug_id == werkzeug.id), None)
        if legacy is not None:
            rpm, vorschub, plunge, stepdown = (
                legacy.rpm, legacy.vorschub, legacy.plunge, legacy.stepdown,
            )
        else:
            rpm, vorschub, plunge, stepdown = 18000.0, 1500.0, 300.0, 1.0

    parameter: dict[str, Any] = {
        "werkzeug_id": werkzeug.id,
        "spindel_rpm": rpm,
        "vorschub": vorschub,
        "eintauch_vorschub": plunge,
        "sicherheitshoehe": 5.0,
        "stepdown": stepdown,
    }
    parameter.update(extras)
    return parameter


def templates() -> list[QuickCAMTemplate]:
    return list(_TEMPLATES)


def template_index() -> dict[str, QuickCAMTemplate]:
    return {t.id: t for t in _TEMPLATES}


def erzeuge_aus_template(
    template_id: str,
    user_eingaben: dict[str, Any],
    *,
    maschine: Maschine,
    werkzeug: Werkzeug,
    material: Material,
    rohmaterial: Rohmaterial | None = None,
    projekt_name: str = "QuickCAM-Projekt",
) -> CWPProjekt:
    """Erzeugt aus einem Template ein vollstaendiges, lauffaehiges Projekt."""
    tmpl = template_index().get(template_id)
    if tmpl is None:
        raise KeyError(f"Unbekanntes Template '{template_id}'")
    if rohmaterial is None:
        rohmaterial = Rohmaterial(
            form=RohmaterialForm.PLATTE,
            laenge=200.0, breite=200.0, hoehe=12.0,
            material_id=material.id,
        )
    erg = tmpl.erzeuge(user_eingaben)
    parameter = _baue_operation_parameter(
        werkzeug=werkzeug, material=material, operation_typ=tmpl.operation_typ,
        extras=erg["parameter_extras"],
    )
    parameter["__geometrie"] = erg["geometrie"]  # damit das Frontend sie sieht
    op = OperationsKonfig(
        id=f"op_{tmpl.id}",
        name=tmpl.name,
        typ=tmpl.operation_typ,
        parameter=parameter,
    )
    setup = Setup(
        id="setup_01",
        name=tmpl.name,
        werkzeug_id=werkzeug.id,
        operationen=[op],
        schritte=[OperationSchritt(id="s1", operation_id=op.id)],
    )
    jetzt = datetime.now(timezone.utc)
    return CWPProjekt(
        schema_version=CWP_SCHEMA_VERSION,
        metadaten=ProjektMetadaten(
            name=projekt_name,
            erstellt=jetzt, geaendert=jetzt,
            aktive_variante="default",
            notizen=f"QuickCAM-Template: {tmpl.name}",
        ),
        maschine=maschine,
        werkzeuge=[werkzeug],
        materialien=[material],
        geometrien=[],  # Geometrie liegt im op-Parameter
        varianten=[
            Variante(
                id="default", name="Default",
                rohmaterial=rohmaterial, setups=[setup],
            ),
        ],
    )
