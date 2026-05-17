# Wrap-Mode (2D-Design auf Zylinder wickeln)

> **Status:** ✅ Backend + API + MCP + Pattern-Skalierung + Wrap-Relief + Tests. Frontend-Editor folgt.
> **Code:** [backend/camwosa/cam/wrap.py](../../backend/camwosa/cam/wrap.py)
> **API:** `POST /api/operations/wrap` · `/api/operations/wrap/pruefe` · `/api/wrap/pattern-skalieren` (A38) · `/api/wrap/toolpath` (Batch fuer mehrere Polygone) · `/api/heightmap/wrap-relief` (A34)
> **MCP:** `operation_wrap`, `wrap_pruefe_design`
> **Tests:** [test_wrap.py](../../backend/tests/cam/test_wrap.py), [test_wrap_api.py](../../backend/tests/api/test_wrap_api.py)

Industrie-Standard fuer **Gravur / Kontur / Tasche auf der Aussenflaeche eines zylindrischen Werkstuecks**. Das 2D-Design liegt abgewickelt vor (XY-Ebene), beim Erzeugen des Toolpath wird Y in den Werkstueck-Winkel A umgerechnet.

Wer eine **Vase / Schale / Saeule formen** will, braucht statt dessen den [Continuous-Lathe-Mode (Drechseln)](Drechseln).

## Wann nutzt man was

| Aufgabe | Modus |
|---------|-------|
| Schriftzug auf einer Drechsel-Saeule | **Wrap** |
| Logo / Bild gravieren auf Rundstab | **Wrap** |
| Praezisions-Schraubgewinde | **Wrap** (Helix-Pfad als XY) |
| Spiral-Nut mit „so ungefaehr"-Genauigkeit | [Drechseln/Helix](Drechseln) |
| Vase, Schale aussen, Bowling-Pin | [Drechseln](Drechseln) |
| PCB-Style-Spuren auf rundem Sensor-Gehaeuse | **Wrap** |

## Funktionsprinzip

1. **2D-Design** liegt in der abgewickelten Form vor:
   - X-Achse = Werkstueck-Laengsachse (bleibt linear)
   - Y-Achse = Bogenlaenge auf dem Werkstueck-Umfang
2. **Umrechnung** im Generator:
   ```
   A_grad = Y_mm × 360 / (2π × Werkstueck_Radius)
          = Y_mm × 57.2958 / Radius_mm
   ```
3. **G-Code** enthaelt X+A+Z simultan pro Bewegung — bei uns wird das A als
   Y-Wert in Grad ausgegeben (GRBL-Genmitsu-Konvention: Y umgemappt auf A,
   `$101=88.889`).
4. **Z** = `Werkstueck_Radius − Eintauchtiefe` — die Werkzeug-Spitze sitzt
   unter der Aussenflaeche.

## Beispiel: Schriftzug rundherum

Du willst „CAMWOSA" um einen Ø40mm Stab gravieren, 0.5mm tief:
- Werkstueck-Radius = 20mm → Umfang = 125.66mm
- Schriftzug-Hoehe entlang X: 12mm
- Schriftzug-Laenge entlang Y: max 100mm (passt unter den Umfang)
- `max_tiefe = 0.5, stepdown = 0.5` → 1 Pass
- Im G-Code wird beim Buchstaben-Ende Y=100mm zu A=286.5° → das Werkstueck
  dreht sich um 286.5° waehrend X+Z dem Buchstaben-Pfad folgen

## Parameter

```python
class WrapParameter:
    werkzeug_id: str
    spindel_rpm: float
    vorschub: float                  # mm/min (Hinweis: bei stark variablen Y
                                     #         kann sich das tip-tip-Speed
                                     #         aendern — siehe G93-Hinweis)
    eintauch_vorschub: float
    sicherheitshoehe: float = 5.0
    werkstueck_radius_mm: float = 20.0
    max_tiefe: float = 1.0           # Gravur-/Schnitt-Tiefe
    stepdown: float = 0.5            # Bei tiefen Schnitten: pro Pass
    geschlossen: bool = False        # Schluss zurueck zum Start?
    aufmass_y_mm: float = 0.0        # Reserviert fuer Ueberlapp bei Vollumdrehung
```

## Design-Pruefung

`pruefe_design_fuer_radius(punkte_xy, radius_mm)` checkt VOR der Toolpath-Erzeugung:

- **Y-Spanne > Umfang**: Design wickelt sich mehrfach um — meist nicht gewollt
- **Negative Y-Werte**: erzeugt negative A-Werte (Drehung rueckwaerts) —
  bei `$131=9999` zulaessig, aber Hinweis
- **Leeres Design**

Wird auch automatisch beim Erzeugen aufgerufen — Warnungen kommen im
Response-Body mit.

## API

```json
POST /api/operations/wrap
{
  "werkzeug_id": "vbit_60grad",
  "punkte_xy": [[0, 0], [12, 0], [12, 100], [0, 100], [0, 0]],
  "parameter": {
    "werkzeug_id": "vbit_60grad",
    "spindel_rpm": 18000, "vorschub": 800, "eintauch_vorschub": 200,
    "werkstueck_radius_mm": 20.0,
    "max_tiefe": 0.5, "stepdown": 0.5,
    "geschlossen": true
  }
}
```

Antwort: Toolpath wie ueblich, plus `warnungen: []` mit Sicherheits-Hinweisen.

## Hinweis G93 (Inverse Time Feed)

Die Industrie nutzt fuer Wrap-Operationen typisch **G93 Inverse Time Feed**:
statt mm/min wird der Vorschub als „1/Minuten fuer die Bewegung" angegeben.
So bleibt die Tool-Tip-Geschwindigkeit konstant unabhaengig vom effektiven
Werkstueck-Durchmesser. Aktuell schreibt unser Postprozessor noch G94
(mm/min) — bei Wrap-Mode mit variablem Y-Anteil kann der tatsaechliche
Tool-Tip-Vorschub abweichen. Saubere G93-Unterstuetzung steht auf der Roadmap.

## MCP

```python
operation_wrap(werkzeug_id, punkte_xy, parameter)
wrap_pruefe_design(punkte_xy, werkstueck_radius_mm)
```

Claude kann z.B. „Wickle den Schriftzug X auf einen Ø40mm Stab" via MCP umsetzen.

## Frontend (WrapView)

[WrapView](../../frontend/src/views/WrapView.tsx) ist als eigene Sidebar-View
„Wrap (Zylinder)" eingebunden:

- **WrapDesignEditor** ([Code](../../frontend/src/editor/WrapDesignEditor.tsx)): 2D-Pfad in der abgewickelten Ansicht (Konva). X waagerecht (Werkstueck-Laengsachse), Y senkrecht (Bogenlaenge). Umfang-Linie gelb-gestrichelt — Punkte oberhalb werden rot, Bereich darüber rot-getönt.
- **WrapPreview3D** ([Code](../../frontend/src/components/WrapPreview3D.tsx)): Three.js zeigt live wie der Pfad auf den Zylinder gewickelt aussieht. Werkzeug-Indikator (blauer Kegel) am letzten Pfad-Punkt. Drag rotiert, Wheel zoomt.
- **Vorlagen-Buttons**: Rechteck 50×40, Diagonale, Spirale, Linie als Startpunkt
- **Pattern-Transformationen** ([WrapPatternTransform](../../frontend/src/editor/WrapPatternTransform.tsx)):
  - **Skalieren auf Soll-Maße**: „Pattern soll genau 15mm hoch sein" → Wert eingeben + Klick
  - **Rundum-Passen (1 Umdrehung)**: Y-Spanne wird genau Werkstueck-Umfang — fuer Muster die exakt rundherum gehen
  - **Auto-Fit Werkstueck**: proportional so gross wie moeglich, passt in Umfang UND in 90% Werkstueck-Laenge
  - **Bei 0,0 starten** (Normalisieren): verschiebt das Pattern an den Werkstueck-Anfang
  - **Prozent-Slider**: 10–500 %, freies Skalieren
  - **Verschieben**: dX, dY in mm
  - **Design-Rotation**: rotiert das ABGEWICKELTE Design (z.B. Schrift schraeg auf Saeule)
  - **BoundingBox-Anzeige**: Breite X / Hoehe Y / Start XY live aktualisiert
- **Live-Pruefung**: 300ms-Debounce gegen den Backend-Endpoint `wrap/pruefe` — Warnungen erscheinen unter dem Editor sobald das Design ueber den Umfang rauslaeuft
- **Parameter-Setup**: Werkstueck-Radius, Werkstueck-Laenge, Spindel-RPM, Vorschub, Plunge, Max-Tiefe, Stepdown, „Geschlossener Pfad"-Checkbox
- Erzeugter Toolpath landet direkt im App-Store als Operation

## Pattern-Skalierung (Master-Plan A38)

Drei Modi fuer das Skalieren eines DXF / Text-Pfades auf das Werkstueck —
direkt im Backend via `skaliere_pattern_fuer_werkstueck()` oder API
`POST /api/wrap/pattern-skalieren`:

| `modus` | Was passiert |
|---------|--------------|
| `feste_skalierung` | Pattern auf gewuenschte ``soll_breite_mm`` / ``soll_hoehe_mm`` skalieren, optional aspekt-erhaltend. |
| `auf_werkstueck_anpassen` | Y-Spanne wird **exakt** Werkstueck-Umfang (Pattern geht 1× rundherum). X folgt proportional (oder eigene ``soll_breite_mm``). |
| `wiederholen` | Pattern bleibt Original-skaliert, wird entlang Y so oft gekachelt dass es exakt einmal um den Umfang passt (Y-Schritt wird angepasst). |

Antwort-Metadaten enthalten ``skalierung_x/y``, ``y_spanne_endgueltig_mm``,
``anzahl_wiederholungen``. Plus Warnungen, falls das Ergebnis-Pattern den
Werkstueck-Umfang ueberschreitet (z.B. weil ``soll_hoehe_mm`` zu gross
gesetzt wurde).

### Batch-Toolpath fuer mehrere Polygone

`POST /api/wrap/toolpath` nimmt eine Liste von Polygonen entgegen und erzeugt
**einen** Toolpath, der zwischen den Polygonen auf Sicherheitshoehe springt.
Praktisch fuer:
- Mehrere Buchstaben aus Text-zu-Pfad (jeder Buchstabe ein Polygon)
- Logos aus DXF mit mehreren getrennten Konturen
- Multi-Sequenz-Muster (Schriftzug + Linie + Ornament)

## Verwandt

- [Drechseln](Drechseln) — Continuous-Lathe-Mode fuer rotationssymmetrische Formen
- [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary) — schreibt Y-Werte als Winkel
- [Rotary-Profil](Rotary-Profil) — Werkstueck-Spannung + Drehzahl-Setup
- [Text-zu-Pfad](Text-zu-Pfad.md) — generiert Polygone aus Schrift
- [Bild-zu-Relief](Bild-zu-Relief.md) — Wrap-Relief auf Zylinder (Phase C)
