# Arc-Fitting (G2/G3)

> **Status:** ✅ Backend fertig (alpha.8, Cluster J1).
> **Code:** [`backend/camwosa/gcode/arc_fitting.py`](../../backend/camwosa/gcode/arc_fitting.py)
> **Tests:** [`backend/tests/gcode/test_arc_fitting.py`](../../backend/tests/gcode/test_arc_fitting.py) (10/10 grün)
> **API:** `POST /api/operations/postprocess` mit `arc_fitting: true`

## Wozu

Die CAM-Generatoren sampeln Kreise, Bögen, Helix und Circular-Pocketing in
viele kurze G1-Segmente (oft 32–64 pro Kreis). Der GRBL-Postprozessor *kann*
aber G2/G3 (Kreisbogen-Interpolation). Arc-Fitting erkennt lineare Punktfolgen,
die auf einem gemeinsamen Kreis liegen, und ersetzt sie durch eine einzige
`BOGEN_CW` / `BOGEN_CCW`-Bewegung.

**Effekt:**
- **Massive G-Code-Reduktion** — ein 64-Segment-Kreis wird zu 1–2 Bögen
- **Ruhigerer Maschinenlauf** — kontinuierliche Bogen-Interpolation statt
  Polygonzug mit hunderten Mini-Rucken
- Kleinere `.nc`-Dateien (wichtig bei 3D-Bahnen + Circular-Pocketing)

## Wie es funktioniert

Greedy-Algorithmus über zusammenhängende LINEAR-Läufe:
1. Bestimme den Kreis durch die ersten 3 Punkte (Umkreismittelpunkt)
2. Erweitere den Bogen solange die folgenden Punkte innerhalb der Toleranz
   auf dem Kreis liegen + die Drehrichtung konsistent bleibt
3. Bei ≥ `min_segmente` Segmenten → ersetze durch einen Bogen (i/j relativ
   zum Startpunkt, GRBL-Konvention), sonst LINEAR beibehalten

## Sicherheits-Regeln

- Nur **LINEAR**-Bewegungen werden gefittet (Eilgang/Plunge/bestehende Bögen
  bleiben unverändert)
- Nur bei **konstantem Z** — echte 2D-Bögen in der XY-Ebene. 3D-Bahnen mit
  Z-Variation werden NICHT gefittet (Helix-Bögen mit Z-Interpolation sind ein
  separater, fortgeschrittener Fall)
- Nur bei **konstantem Feed**
- Bogen-Gesamtwinkel < 340° (vermeidet Vollkreis-Probleme)
- **Endpunkt-treu** — der letzte Punkt jeder Bahn bleibt exakt erhalten

## Benutzung

```python
from camwosa.gcode.arc_fitting import fitte_toolpath, fitte_boegen

# Ganzer Toolpath (Convenience, setzt Metadaten arc_fitted)
neu = fitte_toolpath(toolpath, toleranz_mm=0.05, min_segmente=4)
print(neu.metadaten["arc_fit_bewegungen_vorher"],
      "→", neu.metadaten["arc_fit_bewegungen_nachher"])

# Oder direkt auf einer Bewegungsliste
neue_bewegungen = fitte_boegen(toolpath.bewegungen, toleranz_mm=0.05)
```

## REST-API

Arc-Fitting läuft als optionaler Schritt vor dem Postprozessor:

```
POST /api/operations/postprocess
{
  "maschine_id": "...", "werkzeug_id": "...",
  "toolpaths": [...],
  "arc_fitting": true,
  "arc_toleranz_mm": 0.05
}
```

MCP: `gcode_erzeugen(..., arc_fitting=True, arc_toleranz_mm=0.05)`.

## Parameter

| Parameter | Default | Bedeutung |
|---|---|---|
| `toleranz_mm` | 0.05 | max. Abweichung eines Punkts vom Fit-Kreis |
| `min_segmente` | 4 | Mindestzahl LINEAR-Segmente, die ein Bogen ersetzen muss |
| `max_radius_mm` | 2000 | größere „Kreise" sind faktisch Geraden → nicht fitten |
| `max_bogen_grad` | 340 | Bogen-Winkel-Limit (Vollkreise vermeiden) |

## Bekannte Einschränkungen

- **Keine Helix-Bögen** (G2/G3 mit Z-Interpolation) — Bahnen mit Z-Änderung
  bleiben linear. Sinnvolle Erweiterung für Helix-Bohren / Thread-Milling.
- **Spline-Fitting** (G5) wird nicht gemacht — nur Kreisbögen.

## Verwandt

- [Postprozessor-GRBL](Postprozessor-GRBL) — die G2/G3-Ausgabe
- [Circular+Radial Pocketing](Circular-Radial-Pocketing) — profitiert stark
- [Operation-Kontur](Operation-Kontur) · [Operation-Bohren](Operation-Bohren) (Helix)
