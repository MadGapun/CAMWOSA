# Datenmodell

> **Status:** ✅ Pydantic-Modelle implementiert, SQLAlchemy-Mapping in Arbeit.
> **Code:** [backend/camwosa/db/models.py](../../backend/camwosa/db/models.py) · **Tests:** [backend/tests/db/test_models.py](../../backend/tests/db/test_models.py)

Das Datenmodell ist die zentrale Basis fuer alle CAM-Operationen. Es ist als pydantic-2-Modelle implementiert, validiert beim Erzeugen und ist JSON-serialisierbar.

## Kern-Entitaeten

| Entitaet | Zweck | Pydantic-Klasse |
|----------|-------|-----------------|
| Maschine | Maschinen-Profil mit Arbeitsraum, Spindel, Modi | `Maschine` |
| Werkzeug | Fraeser-Definition (Geometrie + Material) | `Werkzeug` |
| Material | Material-Eigenschaften + Schnittparameter-Presets | `Material` |
| Rohmaterial | Rohteil im Projekt (Form, Position, Nullpunkt) | `Rohmaterial` |
| ProjektMetadaten | Name, Autor, Schema-Version | `ProjektMetadaten` |

## Maschine

```python
from camwosa.db.models import (
    Arbeitsraum, ControllerTyp, Maschine, MaschinenModus, SpindelTyp,
)

m = Maschine(
    id="genmitsu_proverxl_4030_v2",
    name="Genmitsu ProVerXL 4030 V2",
    hersteller="Genmitsu",
    modell="ProVerXL 4030 V2",
    controller=ControllerTyp.GRBL,
    arbeitsraum=Arbeitsraum(x=400, y=400, z=110),
    max_vorschub=3000,
    sicherer_vorschub=2000,
    eilgang=5000,
    spindel_typ=SpindelTyp.MANUELL,
    spindel_rpm_min=10000,
    spindel_rpm_max=30000,
    sicherheitshoehe=5.0,
    postprozessor="grbl_genmitsu",
    modi=[MaschinenModus.STANDARD_XYZ, MaschinenModus.ROTARY_Y],
)
```

**Validierungs-Regeln:**
- `sicherer_vorschub <= max_vorschub`
- `spindel_rpm_max >= spindel_rpm_min`
- `arbeitsraum.x/y/z > 0`
- Default-Modus: `STANDARD_XYZ`

## Werkzeug

```python
from camwosa.db.models import Werkzeug, WerkzeugTyp

t = Werkzeug(
    id="t01_schaft_6mm",
    name="6mm Schaftfraeser 2-Schneider Hartmetall",
    typ=WerkzeugTyp.SCHAFTFRAESER,
    durchmesser=6.0,
    schaft_durchmesser=6.0,
    schneidlaenge=22.0,
    gesamtlaenge=76.0,
    schneiden=2,
)
```

**Werkzeug-Typen** (Enum `WerkzeugTyp`):
- `SCHAFTFRAESER`, `KUGELFRAESER`, `TORUSFRAESER`
- `V_BIT` (braucht `spitzenwinkel`)
- `GRAVIERSTICHEL`, `BOHRER`
- `EINSCHNEIDER`, `FISCHSCHWANZ`
- `SCHRUPPFRAESER`, `DIAMANTGRAVIERER`

**Validierungs-Regeln:**
- `V_BIT` braucht `spitzenwinkel` (sonst ValidationError)
- `durchmesser > 0`, `schneiden 1..12`

## Material

Ein Material hat **mehrere Schnittparameter-Presets** — je Werkzeug einen.

```python
from camwosa.db.models import Material, MaterialKategorie, SchnittParameterPreset

buche = Material(
    id="buche_massiv",
    name="Buche massiv",
    kategorie=MaterialKategorie.HOLZ,
    janka_haerte=1300,
    dichte=0.72,
    presets=[
        SchnittParameterPreset(
            werkzeug_id="t01_schaft_6mm",
            rpm=18000, vorschub=2000, plunge=400,
            stepdown=2.0, stepover_prozent=40,
        )
    ],
)
```

## Rohmaterial

```python
from camwosa.db.models import (
    NullpunktReferenz, Rohmaterial, RohmaterialForm,
)

roh = Rohmaterial(
    form=RohmaterialForm.PLATTE,
    laenge=300, breite=200, hoehe=18,
    material_id="buche_massiv",
    nullpunkt=(0, 0, 0),
    z_referenz=NullpunktReferenz.MATERIAL_TOP,
)
```

**Formen:** `QUADER`, `ZYLINDER` (breite = Durchmesser), `PLATTE`, `FREI`.

## JSON-Serialisierung

Alle Modelle sind JSON-fähig (Roundtrip-getestet):

```python
as_json = m.model_dump_json()
m_neu = Maschine.model_validate_json(as_json)
assert m == m_neu
```

## Forward-Compatibility

Alle Modelle haben `model_config = {"extra": "ignore"}`. Zusaetzliche Felder in JSON werden beim Parsen ignoriert — so brechen aeltere Versionen nicht an neueren Profilen.

## Persistenz

- Default-Profile liegen als JSON in `data/machines/`, `data/tools/`, `data/materials/`.
- User-Profile in der lokalen SQLite-DB (siehe Repository-Pattern, kommt in naechster Iteration).
- Projekt-spezifische Snapshots im `.cwp`-Container (siehe [Projekt-Format](Projekt-Format.md)).

## Erweiterung

Neue Entitaets-Felder hinzufuegen:
1. Feld im pydantic-Modell ergaenzen (mit `default` damit alte Daten weiter laden).
2. Test in `tests/db/test_models.py` ergaenzen.
3. Wenn DB-relevant: Alembic-Migration (kommt mit DB-Layer).
4. Diesen Wiki-Eintrag aktualisieren.

Neue Entitaeten anlegen: zusaetzliches Modul in `backend/camwosa/db/`, Wiki-Eintrag spiegeln.

## Bekannte Einschraenkungen

- Aktuell **kein** Multi-Tenancy / User-Trennung (lokales Tool, ein Nutzer).
- Werkzeug-Bilder werden noch nicht im Modell gehalten (geplant: `bild_pfad` als optionaler String).
- Standzeit-Tracking (Phase E2) noch nicht im Werkzeug-Modell.

## Verwandt

- [Architektur](Architektur.md)
- [Maschinenprofil-Format](Maschinenprofil-Format.md)
- [Werkzeug-Bibliothek](Werkzeug-Bibliothek.md)
- [Material-Datenbank](Material-Datenbank.md)
- [Projekt-Format](Projekt-Format.md)
