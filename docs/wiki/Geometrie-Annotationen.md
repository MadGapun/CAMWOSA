# Geometrie-Annotationen

> **Status:** ✅ Datenmodell + Validate-Endpoints. UI-Editor folgt.
> **Code:** [backend/camwosa/project/schema.py](../../backend/camwosa/project/schema.py) (GeometrieAnnotation, GeometrieAnnotationTyp), [backend/camwosa/api/endpoints/annotationen.py](../../backend/camwosa/api/endpoints/annotationen.py)
> **Tests:** [test_annotationen.py](../../backend/tests/api/test_annotationen.py)

Mit Annotationen kann der User **nachtraegliche Markierungen** auf importierte Geometrien (DXF, STL, eigene Zeichnungen) setzen — ohne die Original-Datei zu mutieren. Typischer Anwendungsfall: eine **Anschlagbohrung** in ein importiertes 3D-Modell legen, damit das Werkstueck spaeter sauber auf der Spannplatte fixiert werden kann.

## Annotation-Typen

| Typ | Zweck | Pflichtfelder |
|-----|-------|---------------|
| `anschlagbohrung` | Bohrung fuer Anschlagstift / Fixier-Schraube | `x`, `y`, `durchmesser_mm`, `tiefe_mm` |
| `refpunkt` | Referenzpunkt fuer Nullpunkt-Setzen | `x`, `y` |
| `kommentar` | Text-Marker fuer den User | `x`, `y`, `text` |
| `ausschnitt` | Markiert einen Bereich der zusaetzlich gefraest werden soll | `x`, `y`, `durchmesser_mm` |

## Datenmodell

```python
class GeometrieAnnotation:
    id: str
    typ: GeometrieAnnotationTyp
    x: float
    y: float
    z: float = 0.0
    durchmesser_mm: float | None
    tiefe_mm: float | None
    text: str = ""
```

`GeometrieSnapshot.annotationen` ist eine Liste davon. Die Annotationen werden mit dem Projekt im .cwp-Container gespeichert.

## Anwendung im Workflow

Eine Annotation **mutiert die Original-Geometrie nicht**. Stattdessen erzeugt das Frontend (oder ein automatischer Workflow-Schritt) aus den Annotationen separate Operationen:

- `anschlagbohrung` → erzeugt einen `BohrenSchritt` mit den Annotation-Punkten
- `ausschnitt` → erzeugt einen `TaschenSchritt`
- `refpunkt` / `kommentar` → nur Anzeige, kein G-Code

So bleibt der Edit-Vorgang umkehrbar — wenn der User die Annotation loescht, ist die Geometrie wieder unveraendert.

## Annotation → Operation (Automatik)

Wandelt eine Annotation-Liste automatisch in CAM-Operationen um — typischer
Use-Case: 4 Anschlagbohrungen an den Ecken eines Werkstuecks werden zu **einer**
Bohren-Operation mit allen 4 Punkten zusammengefasst.

### Gruppierungs-Strategie

- **Anschlagbohrungen** werden nach `(tiefe_mm, durchmesser_mm)` gruppiert. Pro
  Gruppe entsteht **eine Bohren-Operation** mit allen passenden Punkten.
- **Ausschnitte** → eine Tasche-Operation pro Punkt (Kreis-Geometrie).
- **Refpunkte / Kommentare** werden ignoriert (kein CAM-Output), aber als
  Hinweis im Antwort-Bericht aufgelistet.

### Werkzeug-Wahl

Heuristik mit 4 Stufen:

1. Exakter Match auf Durchmesser + bevorzugter Typ (Bohrer fuer Bohrungen, Fraeser fuer Ausschnitte)
2. Naechster groesserer Durchmesser, bevorzugter Typ
3. Naechster groesserer Durchmesser, beliebiger Typ
4. Erstes verfuegbares Werkzeug

Mismatches landen als Hinweis: „Werkzeug X hat Ø 5mm, Annotation forderte 3mm".

### Frontend

[AnnotationenEditor](../../frontend/src/editor/AnnotationenEditor.tsx) bietet
einen Akzent-Button „→ Operationen erzeugen" — sobald mindestens eine
Annotation existiert und `onOperationenErzeugt` als Prop gesetzt ist.

In [ZeichnenView](../../frontend/src/views/ZeichnenView.tsx) wird der Callback
mit `operationHinzufuegen` aus dem App-Store verdrahtet — die neuen Operationen
erscheinen sofort im Tab „Operationen" inklusive aller Hinweise (Werkzeug-
Mismatches, ignorierte Refpunkte).

## API

| Endpoint | Zweck |
|----------|-------|
| `GET /api/annotationen/typen` | Liste der unterstuetzten Annotation-Typen |
| `POST /api/annotationen/validate` | Eine Annotation validieren |
| `POST /api/annotationen/validate-liste` | Liste mit Dedup + Sammel-Fehlerbericht |
| `POST /api/annotationen/zu-operationen` | Wandelt Annotationen → CAM-Operationen |

`POST /api/annotationen/zu-operationen`:

```json
{
  "annotationen": [...GeometrieAnnotation],
  "werkzeug_ids": ["b3", "b4"]   // optional, default = alle verfuegbaren
}
```

Antwort:
```json
{
  "operationen": [...OperationsKonfig],
  "hinweise": ["Werkzeug ... hat Ø 5mm, Annotation forderte 3mm", ...]
}
```

## Frontend-Integration

[ZeichnenView](../../frontend/src/views/ZeichnenView.tsx) bindet [AnnotationenEditor](../../frontend/src/editor/AnnotationenEditor.tsx) in der rechten Spalte ein:

1. User klickt im Editor auf z.B. „+ Anschlagbohrung" → Annotation wird angelegt
2. User klickt „↗ Klicken" beim Annotation-Eintrag → ZeichnenView wechselt in Pick-Modus
3. Naechster Klick im 2D-Canvas → Position x/y wird aus der Maus uebernommen, Pick-Modus endet
4. Annotation wird im Canvas direkt visualisiert (Symbol + Farbe je Typ)

### Canvas-Visualisierung

| Typ | Form | Farbe |
|-----|------|-------|
| `anschlagbohrung` | Kreis mit Durchmesser + Fadenkreuz | `#FFB800` (warning-gelb) |
| `ausschnitt` | Kreis gestrichelt + Fadenkreuz | `#B388FF` (lila) |
| `refpunkt` | Kreuz | `#4A9EFF` (info-blau) |
| `kommentar` | Kleiner Punkt + Text-Label (ab Zoom > 2) | `#A8A8B0` (sekundaer) |

Im Pick-Modus pulsiert die anvisierte Annotation und der Canvas zeigt oben links einen Akzent-Hint („Klick im Canvas → setzt Position").

## Persistierung im Projekt

Annotationen leben an zwei Stellen — je nach Bezug:

| Ort | Bedeutung |
|-----|-----------|
| `GeometrieSnapshot.annotationen` | Pro Geometrie — Annotation gehoert zu einer bestimmten Datei (DXF / STL / Zeichnung) |
| `Variante.annotationen` | Global pro Variante — Annotation gehoert zum Werkstueck als Ganzes (typischer Fall fuer Anschlagbohrungen) |

Der Frontend speichert Anschlagbohrungen auf Variante-Ebene, weil sie das Werkstueck als Ganzes spannen sollen — nicht einzelne Geometrien.

## Verwandt

- [Projekt-Format](Projekt-Format)
- [ArbeitsSchritt](ArbeitsSchritt)
- [CAD-Plugin-System](CAD-Plugin-System)
- [UI-Integration](UI-Integration)
