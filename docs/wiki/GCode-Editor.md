# G-Code-Editor

> **Status:** ✅ Monaco mit eigenem CAMWOSA-Syntax-Highlighting + Befehls-Bibliothek.
> **Code:** [frontend/src/views/GCodeEditorView.tsx](../../frontend/src/views/GCodeEditorView.tsx) · [components/gcodeHighlighter.ts](../../frontend/src/components/gcodeHighlighter.ts) · [components/GCodeBibliothek.ts](../../frontend/src/components/GCodeBibliothek.ts)

Vollwertiger G-Code-Editor in Monaco mit dunklem Theme passend zum CAMWOSA-Design-System.

## Syntax-Highlighting

Eigene Sprache `gcode-camwosa` mit Monarch-Tokenizer:

| Token | Farbe | Beispiele |
|-------|-------|-----------|
| G-Code (`G0`, `G1`, `G90`, ...) | Blau (`#4A9EFF`), bold | Bewegungs- + Modal-Befehle |
| M-Code (`M3`, `M5`, `M6`, ...) | Gelb (`#FFB800`), bold | Spindel/Werkzeug-Befehle |
| Werkzeug-Nummer (`T1`, ...) | Lila (`#B388FF`) | |
| Vorschub (`F2000`) | Gruen (`#00C26E`) | |
| Spindel-RPM (`S18000`) | Orange-Akzent (`#FF6B00`), bold | |
| Achsen-Werte (`X10.5`, `Y0`, `Z-2`) | Weiss | |
| Kommentar (`; ...` / `( ... )`) | Grau italic | |

## CAMWOSA-spezifische Hervorhebungen

Zusaetzlich werden CAMWOSA-Setup-Hinweise visuell ausgezeichnet, damit sie im Editor-Review nicht uebersehen werden:

| Pattern | Klasse | Farbe |
|---------|--------|-------|
| `; ===================` (Banner-Linie) | `camwosa-banner` | Orange-Akzent, bold |
| `; DRECHSEL-JOB ...` | `camwosa-banner` | Orange-Akzent, bold |
| `; --- DRECHSELN: ...` | `camwosa-banner` | Orange-Akzent, bold |
| `; WICHTIG`, `; WARNUNG`, `; ⚠` | `camwosa-warnung` | Warn-Gelb |
| `; %wait`, `; %MAKRO_NAME` (CNCjs-Macros) | `camwosa-macro` | Info-Blau, italic |

So sticht der Drechsel-Setup-Block (vom Rotary-Postprozessor automatisch generiert) sofort ins Auge:

```gcode
; ============================================================
; DRECHSEL-JOB — VOR DEM START PRUEFEN          <- orange, bold
;   - 1 Drechsel-Toolpath(s) im File
;   - Werkstueck-Drehzahl(en) U/min: 250
;   WICHTIG: Werkstueck-Drehung BEVOR Werkzeug eintaucht starten   <- warn-gelb
; ============================================================
```

## Editor-Features

- Cursor-Position-Tracking: aktuelle Zeile wird als G/M-Befehl identifiziert, rechts erscheint die Befehls-Erklaerung
- Befehls-Bibliothek rechts mit Such-Filter + Kategorien (Bewegung, Spindel, Werkzeug, Koordinaten, Einheiten, Ende)
- „Aus Operationen generieren"-Button (postprozessiert die berechneten Toolpaths)
- Export-Button („Exportieren (.nc)") — Datei-Download

## Design-Konsistenz

Theme `camwosa-dark` ist auf das [Design-System](Design-System) abgestimmt:
- Editor-Hintergrund: `--bg-base` (`#0A0A0B`)
- Cursor + aktive Zeilennummer: Akzent-Orange
- Selection: Akzent-Soft (`rgba(255,107,0,0.2)`)
- Font: `JetBrains Mono` (gleiche Mono-Schrift wie restliche UI)

## Verwandt

- [Postprozessor-GRBL](Postprozessor-GRBL)
- [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary)
- [Drechseln](Drechseln) — der Postprozessor schreibt die orange hervorgehobenen Drechsel-Banner
- [Design-System](Design-System)
