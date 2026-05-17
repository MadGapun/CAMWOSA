# Auto-Inlay (Einlegearbeit)

> **Status:** ✅ Backend fertig (alpha.5). UI-Integration folgt.
> **Code:** [`backend/camwosa/cam/auto_inlay.py`](../../backend/camwosa/cam/auto_inlay.py)
> **Tests:** [`backend/tests/cam/test_auto_inlay.py`](../../backend/tests/cam/test_auto_inlay.py) (12/12 grün)
> **API:** `POST /api/spezial-ops/auto-inlay`

## Wozu

Klassische Einlegearbeit: helle Form in dunkler Tasche (oder umgekehrt). Du
zeichnest **EINE Kontur**, das Tool generiert dir die **beiden Geometrien**:

- **Tasche** — Aussparung im dunklen Material (etwas kleiner als die Plug-Form
  durch das Werkzeug-Schlitz, sonst passt nichts rein)
- **Plug** — Einsatz im hellen Material, geringfügig kleiner als die Tasche
  (sonst presst er beim Verkleben das Material auseinander)

Mit einem **konfigurierbaren Spiel** (Holz: 0.05-0.15 mm, Kunststoff: 0-0.05 mm)
zwischen beiden, sodass der Plug ohne Spalt sitzt.

Wer das per Hand mit Offset-Operationen baut, vergisst meist eine der beiden
Korrekturen und ärgert sich dann über die schlechte Passung.

## Wie es funktioniert

Aus einer Kontur werden zwei Polygone berechnet:

```
                +-------------------+
                |                   |  <- Original (User-Zeichnung)
                |  +---------------+|
                |  |               || <- Tasche (= Original - spiel/2)
                |  |  +-----------+||
                |  |  |   PLUG    |||  <- Plug (= Tasche - spiel)
                |  |  |           |||
                |  |  +-----------+||
                |  +---------------+|
                +-------------------+
```

Beide werden um `spiel/2` vom Original erodiert — damit ist der Plug genau
`spiel` mm Gesamt-Luft kleiner als die Tasche.

## Benutzung (Python)

```python
from camwosa.cam.auto_inlay import (
    AutoInlayParameter,
    berechne_auto_inlay,
    ergebnis_zu_geometrien,
)

params = AutoInlayParameter(
    spiel_mm=0.10,                  # Holz: 0.05-0.15
    werkzeug_radius_mm=1.0,         # 2mm Fraeser → 1mm Radius
    tasche_tiefe_mm=3.0,            # ins dunkle Material
    plug_uebermass_oben_mm=0.5,     # Plug ragt oben raus, wird plangeschliffen
)

ergebnis = berechne_auto_inlay(geometrie, params)
print(ergebnis.tasche_flaeche_mm2)
print(ergebnis.plug_flaeche_mm2)

# Als GeometrieObjekte fuers Frontend
tasche_geo, plug_geo = ergebnis_zu_geometrien(ergebnis)
# tasche_geo.layer = "auto_inlay_tasche"
# plug_geo.layer = "auto_inlay_plug"
```

Aus den beiden Geometrien kannst du dann normale Operationen anlegen:
- **Tasche** → Operation `tasche` mit `tiefe = tasche_tiefe_mm`
- **Plug** → Operation `kontur` (Außenseite) mit `tiefe = plug_hoehe_mm`

## Validierung

Die Funktion wirft `AutoInlayFehler`, wenn:
- die Kontur kleiner als 1 mm² ist
- die Kontur offen ist
- das Werkzeug größer als die halbe Bounding-Box ist (würde nicht ins Polygon
  passen)
- das Spiel so groß ist, dass der Plug nach dem Schrumpfen degeneriert

Bei scharfen Einbuchtungen kommt ein **Hinweis** (kein Fehler) — der Werkzeug
kann diese Ecken nicht erreichen.

## REST-API

```
POST /api/spezial-ops/auto-inlay
Body:
{
  "parameter": {
    "spiel_mm": 0.1,
    "werkzeug_radius_mm": 1.0,
    "tasche_tiefe_mm": 3.0,
    "plug_uebermass_oben_mm": 0.5
  },
  "geometrie": {
    "typ": "polylinie", "layer": "0",
    "punkte": [[0,0], [50,0], [50,30], [0,30]],
    "geschlossen": true
  }
}

Response:
{
  "ergebnis": {
    "tasche_polygon_wkt": "POLYGON ((...))",
    "plug_polygon_wkt":   "POLYGON ((...))",
    "tasche_flaeche_mm2": ...,
    "plug_flaeche_mm2":   ...,
    "spiel_pro_seite_mm": 0.05,
    "tasche_tiefe_mm":    3.0,
    "plug_hoehe_mm":      3.5,
    "hinweise":           []
  },
  "tasche_geometrie": {"typ": "polylinie", "punkte": [...], "geschlossen": true},
  "plug_geometrie":   {"typ": "polylinie", "punkte": [...], "geschlossen": true}
}
```

## Bekannte Einschränkungen

- **Nur 2D-Inlay** — Z-Profil ist konstant (Tasche-Boden flach)
- **Kein V-Carve-Inlay** — für V-Carving-basierte Einleger (mit variabler
  Tiefe für scharfe Buchstaben-Spitzen) ist ein separates Modul geplant
- **Innen-Aussparungen** im Polygon (z.B. Buchstabe „O") werden zur größten
  Fläche reduziert — Multi-Polygone werden nicht voll unterstützt

## Verwandt

- [Operation-Tasche](Operation-Tasche)
- [Operation-Kontur](Operation-Kontur)
- [Spezial-Operationen](Spezial-Operationen)
