# Sicherheits-Checks

> **Status:** ✅ Implementiert (Phase 1 — alle 7 Checks).
> **Issue:** [#11](https://github.com/MadGapun/CAMWOSA/issues/11)
> **Code:** [backend/camwosa/safety/checks.py](../../backend/camwosa/safety/checks.py) · **Tests:** [backend/tests/safety/test_checks.py](../../backend/tests/safety/test_checks.py)

Sicherheits-Checks pruefen Toolpaths auf Crash-Ursachen **vor** dem G-Code-Export. Sie sind die wichtigste Schicht zwischen "CAM denkt" und "Maschine fraest".

## Verwendung

```python
from camwosa.safety import pruefe_toolpath, CheckStufe

bericht = pruefe_toolpath(toolpath, maschine, werkzeug, z_oberkante_material=0.0)

if bericht.hat_blocker:
    print("KRITISCH:")
    for e in bericht.ergebnisse:
        if e.stufe == CheckStufe.KRITISCH:
            print(f"  - {e.titel}: {e.beschreibung}")
else:
    print("Toolpath OK")
```

## Implementierte Checks

| ID | Stufe | Was wird geprueft |
|----|-------|-------------------|
| `g0_im_material` | KRITISCH | Eilbewegung (G0) unterhalb Material-OK |
| `arbeitsraum_x` / `_y` / `_z` | KRITISCH | Toolpath ausserhalb Maschinen-Arbeitsraum |
| `werkzeug_zu_kurz` | WARNUNG | Schnitttiefe > Werkzeug-Schneidlaenge |
| `plunge_ohne_rampe` | INFO | Senkrechtes Eintauchen bei Schaft-/Kugelfraeser |
| `rpm_zu_hoch` / `rpm_zu_niedrig` | WARNUNG | RPM ausserhalb Maschinen-Range |
| `rpm_fehlt` | KRITISCH | Toolpath mit Spindel-RPM = 0 |
| `plunge_zu_schnell` | INFO | Eintauchvorschub > Schnittvorschub |

## Stufen

| Stufe | Bedeutung | UI-Verhalten |
|-------|-----------|--------------|
| `KRITISCH` | Blocker — wahrscheinlicher Crash | G-Code-Export blockiert. Override per "VERSTANDEN"-Bestaetigung. |
| `WARNUNG` | Risiko vorhanden | Anzeige in gelb. Export moeglich. |
| `INFO` | Empfehlung | Hinweis in blau. |

## CheckBericht

```python
@dataclass
class CheckErgebnis:
    check_id: str
    stufe: CheckStufe
    titel: str
    beschreibung: str
    bewegungs_index: int | None  # Verweis fuer Klick-zur-Stelle in der Vorschau

@dataclass
class CheckBericht:
    ergebnisse: list[CheckErgebnis]
    hat_blocker: bool
    anzahl_kritisch: int
    anzahl_warnung: int
```

## Mehrere Toolpaths pruefen

Bei Multi-Setup mit mehreren Toolpaths:

```python
from camwosa.safety import pruefe_alle
bericht = pruefe_alle([tp1, tp2, tp3], maschine, werkzeug)
```

## Override-Workflow (UI)

1. UI zeigt rote Blocker-Markierung.
2. Klick auf Warnung -> Sprung zur Stelle in der 2D-Vorschau (`bewegungs_index`).
3. User kann ueber "Override"-Dialog (Eingabe von "VERSTANDEN") trotzdem exportieren.
4. Override wird im Projekt-Audit-Log mit Timestamp protokolliert.

(Der Override-Workflow ist UI-Sache und wird mit dem Frontend implementiert. Backend liefert nur den Bericht.)

## Erweiterung

Neue Checks hinzufuegen:
1. Funktion `_check_<name>` in `safety/checks.py`.
2. Aufruf in `pruefe_toolpath()` aufnehmen.
3. Test in `tests/safety/test_checks.py`.
4. Diesen Wiki-Eintrag aktualisieren.

## Verwandte Pre-Run-Pruefungen

- [Z-Grid-Diagnose](Z-Grid-Diagnose) — analysiert Z-Probing-Daten und meldet
  ob das Werkstueck eben aufgespannt ist. Vier Befund-Stufen mit Klartext-
  Empfehlung. (alpha.5, A47-Rest)
- **Spannmittel-Modell** (`db/spannmittel.py`) — 8 Typen mit Sicherheitszonen.
  `pruefe_toolpath_gegen_spannmittel()` checked Crash mit definierten
  Klemmen, Vakuum-Tisch, Reitstock etc. (alpha.3, A47)
- **Collet-Collision** via `Werkzeug.free_length_mm` — pruefen ob der
  Schaft/Collet das Werkstueck oder die Spannmittel erreicht (alpha.3, A46).

## Geplante Erweiterungen

- **Werkzeughalter-Kollision** (Phase E3): 3D-Geometrie des Halters gegen
  Werkstueck.
- **Adaptive-Clearing-Eingriffstiefe** (Phase E4): Kontrolle des konstanten
  Eingriffs.
- **Reference-Planes-Modell**: explizite Werkstueck-Referenz-Ebenen fuer
  Multi-Setup-Operationen.

## Verwandt

- [Postprozessor-GRBL](Postprozessor-GRBL.md)
- [Operation-Kontur](Operation-Kontur.md)
- [Multi-Setup-Workflow](Workflow-Modul.md)
