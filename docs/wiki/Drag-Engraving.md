# Drag-Engraving (Schleppgravur)

> **Status:** ✅ Backend fertig (alpha.5). UI-Integration folgt.
> **Code:** [`backend/camwosa/cam/drag_engraving.py`](../../backend/camwosa/cam/drag_engraving.py)
> **Tests:** [`backend/tests/cam/test_drag_engraving.py`](../../backend/tests/cam/test_drag_engraving.py) (12/12 grün)
> **API:** `POST /api/spezial-ops/drag-engraving`

## Wozu

Diamantgravierer oder federbelastete Schleppgravierer brauchen einen **anderen
G-Code als normale Gravur** mit Fräser:

- **Spindel ist AUS** (`M5`) — das Werkzeug dreht sich nicht aktiv
- **Werkzeug ist passiv** und folgt der Bewegungsrichtung
- **Plunge muss langsam sein** (≈ 1/10 vom Vorschub) — sonst Diamantspitze ab
- **An scharfen Ecken** muss kurz angehalten werden, damit der Diamant sich
  neu ausrichtet
- **Optional tangentialer Lead-In** — sonst gibt's am Start einen „Tropfen"

Wer das mit der normalen Gravur-Op macht, lässt entweder die Spindel laufen
(zerkratzt die Spitze) oder ploppt mit M3/M5 zwischen jeder Bewegung — beides
ungesund für das Werkzeug.

## Werkzeug-Pflicht

Die Op weigert sich, wenn das ausgewählte Werkzeug **nicht** vom Typ
`DRAG_GRAVIERER` oder `DIAMANTGRAVIERER` ist. Begründung: bei normalen Fräsern
mit Spindel-AUS würde das Werkzeug am Material kratzen statt zu schreiben.

## Benutzung (Python)

```python
from camwosa.cam.drag_engraving import (
    DragEngravingParameter,
    erzeuge_drag_engraving_toolpath,
)

params = DragEngravingParameter(
    werkzeug_id="t_drag_diamant_03",
    vorschub=800,                     # mm/min
    eintauch_vorschub=80,             # 1/10 vom Vorschub — Diamant schonen
    tiefe=0.15,                       # mm
    dwell_an_ecken_sekunden=0.15,     # Pause an scharfen Knicken
    ecken_winkel_schwelle_grad=30,    # was als "scharf" gilt
    lead_in_tangential_mm=2.0,        # gegen Tropfen am Start
)

tp = erzeuge_drag_engraving_toolpath(geometrie, werkzeug, params)
# Resultierender Toolpath hat spindel_rpm=0.0 (Postprozessor erzeugt M5)
```

## Was der G-Code bekommt

Ein typischer Pfad:
```
M5            ; Spindel AUS
G0 X..Y..Z3   ; zum Pre-Position (tangential 2mm vorher)
G1 Z-0.15 F80 ; Plunge — langsam!
G1 X..Y.. F800; tangential einfahren
G1 X..Y.. F800; entlang des Pfads
G4 P0.15      ; Dwell an scharfer Ecke
G1 X..Y.. F800; weiter
G0 Z3         ; Lift
```

`G4 Pn` ist die GRBL-Dwell-Syntax und wird vom Postprozessor erzeugt sobald
er ein `Bewegung.kommentar == "DWELL Xs (...)"` sieht.

## REST-API

```
POST /api/spezial-ops/drag-engraving
Body:
{
  "parameter": {
    "werkzeug_id": "t_drag_diamant_03",
    "vorschub": 800,
    "eintauch_vorschub": 80,
    "tiefe": 0.15,
    "dwell_an_ecken_sekunden": 0.15,
    "ecken_winkel_schwelle_grad": 30,
    "lead_in_tangential_mm": 2.0
  },
  "geometrie": {
    "typ": "polylinie", "layer": "0",
    "punkte": [[0,0], [50,0], [50,30], [0,30]],
    "geschlossen": true
  }
}

Response: Toolpath (siehe Toolpath-Format) mit
metadaten = {"drag_engraving": true, "tiefe_mm": 0.15, "ecken_dwell_s": 0.15}
```

## Bekannte Einschränkungen

- **Tiefen-Variation** wird nicht unterstützt — bei Drag bleibt die Tiefe
  konstant (kommt am Federdruck an, nicht an Z-Position)
- **Multi-Pass** macht keinen Sinn — Diamant schneidet in einem Durchgang
- **V-Carving-Variante** mit Drag-Bit gibt's nicht (gehört in eine eigene
  Gravur-Strategie)

## Verwandt

- [Werkzeug-Typen](Werkzeug-Typen) — DRAG_GRAVIERER und DIAMANTGRAVIERER
- [Operation-Gravur](Operation-Gravur) — die "normale" Variante mit V-Bit
- [Spezial-Operationen](Spezial-Operationen)
