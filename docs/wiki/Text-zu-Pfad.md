# Text → Pfad

> **Status:** ✅ Backend + API + 18 Tests · integriert in `auto_cam_erstellen.beschriftung_wrap`.
> **Code:** [backend/camwosa/cad/text_zu_pfad.py](../../backend/camwosa/cad/text_zu_pfad.py)
> **Tests:** [test_text_zu_pfad.py](../../backend/tests/cad/test_text_zu_pfad.py) (12) · [test_text_api.py](../../backend/tests/api/test_text_api.py) (6)
> **API:** `POST /api/text/zu-pfad` · `POST /api/text/zu-pfad/punktlisten`
> **Master-Plan-Position:** [A37](Master-Plan.md)

## Worum es geht

Aus einer Zeichenfolge wie ``"MADGAPUN"`` werden 2D-Polygone — direkt nutzbar
fuer Gravur, Wrap-Mode, Operationen-Kontur und ``auto_cam_erstellen.beschriftung_wrap``.

Buchstaben mit Loechern (O, P, B, A, R, D, e, a, o, ...) werden als
shapely-Polygone mit ``interiors`` zurueckgeliefert.

## Tech-Stack

- **fontTools** (pure-Python, in den Default-Dependencies) — keine
  Binary-Deps wie freetype.
- **shapely** fuer die Polygon-Datenstruktur.
- **Eigener Pen** liest die TrueType-Pen-API und erzeugt Subpfade — quadratic
  + cubic Beziers werden in N Linienstuecke approximiert (Default 12).

## Font-Auswahl

Default: System-Font-Fallback in dieser Reihenfolge:

```
Windows:  Arial → Calibri → Segoe UI
Linux:    DejaVuSans → LiberationSans
macOS:    Arial → Helvetica
```

Wenn keiner davon installiert ist, wird `FontFehler` geworfen. User kann
auch einen eigenen Pfad uebergeben:

```python
from camwosa.cad.text_zu_pfad import text_zu_pfade, TextPfadParameter

polygone = text_zu_pfade(
    "Mein Logo",
    TextPfadParameter(
        hoehe_mm=12,
        font_pfad="/pfad/zu/MeineSchrift.ttf",
    ),
)
```

## Parameter

| Feld | Default | Bedeutung |
|------|---------|-----------|
| `hoehe_mm` | 10.0 | Cap-Height in mm (etwa Punkt-Groesse) |
| `font_pfad` | None | Eigene TTF/OTF, sonst System-Default |
| `zeichen_abstand_extra_mm` | 0.0 | Negativ = engerer Satz (Kerning-Override) |
| `zeilen_abstand_faktor` | 1.2 | Bei mehrzeiligem Text |
| `kurven_aufloesung` | 12 | Mehr = glattere Beziers, mehr Punkte |

## Loch-Erkennung

Buchstaben wie ``O``, ``P`` haben innere Konturen. Verschiedene Font-Formate
nutzen verschiedene Orientierungs-Konventionen (CW vs. CCW). Wir verlassen
uns deshalb **nicht** auf die Orientierung, sondern bauen die Parent-Child-
Hierarchie ueber **shapely-Contains-Tests**:

1. Alle Subpfade werden als Polygone gelesen
2. Fuer jedes Polygon-Paar pruefen wir Contains
3. Verschachtelungs-Tiefe: gerade = Aussenkontur, ungerade = Loch
4. Loch wird seinem direkten Eltern-Polygon zugeordnet

Das ist robust auch fuer komplexe Glyphen wie ``8`` (zwei Loecher) oder
verschachtelte Logos.

## API

```bash
# Vollformat — Polygone mit Aussen + Loechern
curl -X POST http://localhost:8765/api/text/zu-pfad \
     -H "Content-Type: application/json" \
     -d '{"text": "MADGAPUN", "hoehe_mm": 10}'

# Kurzform — flache Punktlisten (Aussen + Loecher gleichwertig)
curl -X POST http://localhost:8765/api/text/zu-pfad/punktlisten \
     -H "Content-Type: application/json" \
     -d '{"text": "MADGAPUN", "hoehe_mm": 10}'
```

Antwort: `polygone[] / punktlisten[] + bounding_box + anzahl_polygone`.

## Integration

`auto_cam_erstellen.beschriftung_wrap` nutzt die Funktion automatisch.
Frueher gab es einen Hinweis ``"Text-zu-Pfad-Konversion noch nicht
implementiert"``, der ist jetzt durch die echte Pfad-Erzeugung ersetzt. Die
erzeugten Punktlisten landen in
``operation.parameter["__text_punkte"]``.

## Limitierungen

- **Kein OpenType-Layout** (kein automatisches Kerning aus Font, keine
  Ligaturen wie „fi", keine arabische Verbundschrift). Wir nutzen die rohe
  Glyph-Advance.
- **Keine Vertical Metrics** (Asien-Schriften) — alle Texte laufen horizontal.
- **Composite-Glyphen** (z.B. Umlaute via Basisbuchstabe + Diakritisches
  Zeichen) werden ueber den fontTools-Pen korrekt aufgeloest — Test mit
  ``ü``/``ä``/``ö`` durchgelaufen.

## Verwandt

- [Operation Gravur](Operation-Gravur.md) — Standard-Gravur mit dem Pfad
- [Wrap-Mode](Wrap-Mode.md) — Pfad auf Zylinder wickeln
- [MCP-AutoCAM](MCP-AutoCAM.md) — `auto_cam_erstellen.beschriftung_wrap`
