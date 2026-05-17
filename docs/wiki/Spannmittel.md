# Spannmittel-Modell

> **Status:** ✅ Backend fertig (alpha.3). UI-Verdrahtung folgt.
> **Code:** [`backend/camwosa/db/spannmittel.py`](../../backend/camwosa/db/spannmittel.py)
> **Tests:** [`backend/tests/db/test_spannmittel.py`](../../backend/tests/db/test_spannmittel.py) (8/8 grün)

## Wozu

Bisher konnte man im Projekt nur als Freitext notieren *"Werkstück mit
Schraubzwingen oben und unten gespannt"*. Das ist für den Menschen lesbar,
aber das **CAM kann nicht prüfen**, ob der Toolpath an einer Klemme vorbei
geht.

Mit dem Spannmittel-Modell hinterlegt man die **Position und Sperrzone**
jeder Klemme **strukturiert**, und der Toolpath-Generator kann
automatisch checken: *"Bewegt sich der Fräser durch ein Spannmittel?"*

## Spannmittel-Typen

| Typ | Beschreibung | Sperrzone |
|---|---|---|
| `SCHRAUBSTOCK` | parallele Backen, typisch für Metall | Box auf jeder Backenseite |
| `SCHRAUBZWINGE` | einzelne Holz-Zwinge | runder Sicherheits-Radius |
| `VAKUUM_TISCH` | Vakuum-Saugplatte | kein Sperrbereich, nur Mindest-Z |
| `SPANNFUTTER` | Rotary 3-/4-Backen-Futter | runder Sicherheits-Radius |
| `REITSTOCK` | Rotary-Gegenpunkt | runder Sicherheits-Radius |
| `T_NUT` | T-Nut-Spanner im Maschinen-Tisch | runder Sicherheits-Radius |
| `DOPPELKLEBE` | doppelseitiges Klebeband | kein Sperrbereich |
| `FRAES_FREUND` | lasergeschnittene Spann-Geometrie | benutzerdefinierte Box |

## Datenmodell

```python
from camwosa.db.spannmittel import Spannmittel, SpannmittelTyp

zwinge = Spannmittel(
    typ=SpannmittelTyp.SCHRAUBZWINGE,
    name="Zwinge oben links",
    position_x=20, position_y=200,
    z_hoehe_mm=15,                  # wie hoch die Klemme aus Tisch ragt
    sicherheits_radius_mm=12,       # Werkzeug-Crash-Schutz
)
schraubstock = Spannmittel(
    typ=SpannmittelTyp.SCHRAUBSTOCK,
    name="Hauptschraubstock",
    position_x=100, position_y=100,
    z_hoehe_mm=20,
    sicherheits_box_x_mm=120,       # Box statt Radius
    sicherheits_box_y_mm=30,
)
```

Jedes Spannmittel hat **entweder** Radius **oder** Box-Sperrzone, nicht beides.

## Toolpath-Pruefung

```python
from camwosa.db.spannmittel import (
    punkt_in_sperrzone,
    pruefe_toolpath_gegen_spannmittel,
)

# Einzelpunkt-Check
ist_kollision = punkt_in_sperrzone(zwinge, x=25, y=205, z=5)

# Ganzen Toolpath gegen alle Spannmittel
verletzungen = pruefe_toolpath_gegen_spannmittel(toolpath, [zwinge, schraubstock])
for v in verletzungen:
    print(f"Bewegung {v.bewegungs_index}: {v.beschreibung}")
```

## Integration mit Setup

Pro Workflow-Setup kann man eine Liste von Spannmitteln hinterlegen — die
gelten dann für alle Operationen in diesem Setup, weil zwischen Setups eh
umgespannt wird.

## Bekannte Einschränkungen

- **Keine 3D-Geometrie** der Klemme — wir nutzen einfache Sperrzonen-Primitive.
  Für detaillierte Crash-Erkennung (Werkzeughalter gegen Spannmittel-Schraube)
  braucht's später ein eigenes Modul (E3 im Master-Plan).
- **Keine UI-Visualisierung** im Frontend — noch (Cluster D + H).
- **Z-Höhe ist konstant** — Klemmen die geneigt aufgesetzt werden (Stufenklemme)
  modellieren wir noch nicht.

## Verwandt

- [Sicherheits-Checks](Sicherheits-Checks)
- [Workflow-Modul](Workflow-Modul) — Setup-Definition
- [Multi-Werkzeug-Setup](Multi-Werkzeug-Setup)
