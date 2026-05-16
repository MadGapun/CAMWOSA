# Integriertes Zeichnen

> **Status:** ✅ Phase 1 (Linie, Rechteck, Kreis, Polygon, Punkt + Snap-Grid + Auswahl + Uebernahme als Geometrie).
> **Issue:** [#7](https://github.com/MadGapun/CAMWOSA/issues/7)
> **Code:** [frontend/src/views/ZeichnenView.tsx](../../frontend/src/views/ZeichnenView.tsx) · [frontend/src/state/drawingStore.ts](../../frontend/src/state/drawingStore.ts)

LightBurn-inspiriertes 2D-Zeichenmodul fuer schnelle Formen direkt in CAMWOSA — ohne Umweg ueber externes CAD.

## Bedienung

- **Linke Werkzeug-Palette:** Werkzeug waehlen (Auswahl, Linie, Rechteck, Kreis, Polygon, Punkt)
- **Klick + Drag** auf Stage:
  - Linie: Anfangs- + Endpunkt
  - Rechteck: zwei diagonale Eckpunkte
  - Kreis: Mittelpunkt + Radius (zweiter Klick)
- **Polygon:** mehrere Klicks, **Doppelklick** schliesst
- **Punkt:** ein Klick (z.B. fuer Bohrposition)
- **Auswahl:** Klick auf Objekt + Pan via Drag
- **Mausrad:** Zoom

## Snap

`Snap-Grid` (mm) im Header. Default 1 mm. Bei Wert 0 ist Snap deaktiviert.

## Uebernahme als Geometrie

Button **„Als Geometrie uebernehmen"** kopiert alle gezeichneten Objekte in den globalen `geometrien`-Store. Die Operations-View und Toolpath-Vorschau verwenden diese Liste — gezeichnete Objekte sind ab dem Moment **gleichwertig zu importierten DXFs**.

## Phase-1-Funktionsumfang

| Funktion | Status |
|----------|--------|
| Linie | ✅ |
| Rechteck (2 Eckpunkte) | ✅ |
| Kreis (Mittelpunkt + Radius) | ✅ |
| Polygon (Klicks + Doppelklick) | ✅ |
| Punkt | ✅ |
| Snap-Grid | ✅ |
| Auswahl (Klick auf Objekt) | ✅ |
| Loeschen (Liste rechts oder Auswahl + Del) | ✅ |
| Zoom + Pan | ✅ |
| Achsen + Origin sichtbar | ✅ |
| Uebernahme als Geometrie | ✅ |

## Geplant fuer Phase 2

- Boolean: Vereinigung / Differenz / Schnitt
- Verschieben / Rotieren / Skalieren / Spiegeln
- Lineares + polares Array
- Trimmen / Verlaengern
- Fillet / Chamfer
- Offset (Parallel-Kurve)
- Snap zu Endpunkt / Mitte / Schnittpunkt / Tangente
- Layer-Verwaltung
- Text-Gravur (mit System-Fonts via fontTools)
- Bemassung
- DXF-Import direkt im Zeichnen-Modul (statt nur via DXF-Import-Dialog)

## Architektur

- **State:** `useDrawingStore` (zustand) mit `objekte`, `werkzeug`, `snap_grid`.
- **Datentyp:** `ZeichenObjekt extends GeometrieObjekt` — direkt in Backend-Form serialisierbar.
- **Stage:** Konva mit Y-Achse umgedreht (CAM-Konvention: Y nach oben).

## Bekannte Einschraenkungen

- Keine Layer (alle Objekte auf Layer "Zeichnung").
- Keine Speicherung im `.cwp`-Container ueber Geometrien hinaus (Phase 2).
- Keine Undo/Redo (Phase 2).

## Verwandt

- [DXF-Import](DXF-Import.md)
- [Frontend](Frontend.md)
- [Operation-Kontur](Operation-Kontur.md)
