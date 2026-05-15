# GRBL-Standard-Postprozessor

> **Status:** ✅ Implementiert.
> **Issue:** [#4](https://github.com/MadGapun/CAMWOSA/issues/4)
> **Code:** [backend/camwosa/postprocessor/grbl_standard.py](../../backend/camwosa/postprocessor/grbl_standard.py) · **Tests:** [backend/tests/postprocessor/test_grbl.py](../../backend/tests/postprocessor/test_grbl.py)

Der Standard-Postprozessor erzeugt G-Code fuer GRBL 1.1 in mm und absoluten Koordinaten.

## Was er erzeugt

```gcode
; CAMWOSA G-Code
; Maschine: Genmitsu ProVerXL 4030 V2
; Werkzeug: 6mm Schaftfraeser 2-Schneider Hartmetall (D=6.0mm)
G21
G90
G17
G94
M3 S18000
G0 X0.000 Y0.000 Z5.000  ; Anfahrt
G1 X0.000 Y0.000 Z-2.000 F400
G1 X100.000 Y0.000 Z-2.000 F2000
...
G0 Z5.000
G0 X0.000 Y0.000
M5
M30
```

## Verwendung

```python
from camwosa.postprocessor import PostKontext, registry
from camwosa.gcode.toolpath import Toolpath

post = registry().get("grbl_standard")()
ctx = PostKontext(maschine=maschine, werkzeug=werkzeug)
zeilen = post.post_alle(ctx, [toolpath_a, toolpath_b])

with open("output.nc", "w") as f:
    f.write("\n".join(zeilen))
```

## Konventionen

| Aspekt | Verhalten |
|--------|-----------|
| Einheiten | mm (G21) |
| Koordinaten | absolut (G90) |
| Ebene | XY (G17) |
| Vorschub | mm/min (G94) |
| Spindel | M3/M5 |
| Werkzeugwechsel | M0-Pause + Hinweis (GRBL kennt kein M6) |
| Kommentare | `; ...` |
| Programm-Ende | M30 |

## Werkzeugwechsel

GRBL kennt **kein** M6. CAMWOSA macht stattdessen:
1. Spindel aus (M5)
2. Auf Sicherheitshoehe heben (G0 Z)
3. Auf Park-Position fahren (G0 X Y)
4. Kommentar mit Werkzeug-Anweisung
5. M0-Pause — der Bediener muss in CNCjs auf "Continue" druecken

## Erweiterungen

Genmitsu-spezifische Variante: [Postprozessor-GRBL-Genmitsu](Postprozessor-GRBL-Genmitsu.md)
Rotary-Variante: [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary.md)
Eigene Postprozessoren: [Postprozessor-Plugins](Postprozessor-Plugins.md)

## Bekannte Einschraenkungen

- Kein G43 (Tool Length Offset) — GRBL unterstuetzt es nicht.
- Kein Bohrzyklus G81/G83 — wird derzeit als Folge von G0/G1-Befehlen ausgegeben.
  - Begruendung: GRBL unterstuetzt G81/G83 nicht in allen Varianten. Manuelles Pecking ist robuster.

## Verwandt

- [Postprozessor-Plugins](Postprozessor-Plugins.md)
- [Postprozessor-GRBL-Genmitsu](Postprozessor-GRBL-Genmitsu.md)
- [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary.md)
- [Operation-Kontur](Operation-Kontur.md)
