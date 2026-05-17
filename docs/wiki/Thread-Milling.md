# Thread-Milling (Gewindefraesen)

> **Status:** ✅ Backend fertig (alpha.5). UI-Integration folgt.
> **Code:** [`backend/camwosa/cam/thread_milling.py`](../../backend/camwosa/cam/thread_milling.py)
> **Tests:** [`backend/tests/cam/test_thread_milling.py`](../../backend/tests/cam/test_thread_milling.py) (9/9 grün)
> **API:** `POST /api/spezial-ops/thread-milling`

## Wozu

Gewindefräsen statt Gewindeschneiden hat mehrere Vorteile:

- **Universeller Fräser** — ein Gewindefräser kann z.B. M3–M10 (egal welche
  Größe, solange die Bahn passt)
- **Weniger Drehmoment** — kein einzelnes Werkzeug das durch ein blockiertes
  Loch bricht
- **Besser für Sacklöcher** — keine Späne im Lochboden
- **Besser bei harten Materialien** (Stahl, Alu) — kontrollierte Schnittlast

## Wie es funktioniert

Werkzeug fährt einen **Helix** mit Gewindesteigung als Z-Pitch und der
Gewindenenndurchmesser-passenden Bahnradius:

```
       _   _
      / \_/ \      <- jeder Helix-"Buckel" = 1 Gewindegang
     /     \
    /       \
   |   ___   |
    \_/   \_/
```

- **Innengewinde**: Fräser kreist innerhalb des Lochs
  - Bahn-Radius = (Nenn − Werkzeug) / 2
- **Außengewinde**: Fräser kreist um den Bolzen
  - Bahn-Radius = (Nenn + Werkzeug) / 2

Die **Drehrichtung** hängt von Gewinde-Richtung × Innen/Außen ab:
- Innen + Rechts → CCW (G3)
- Innen + Links → CW (G2)
- Außen + Rechts → CW
- Außen + Links → CCW

## Benutzung (Python)

```python
from camwosa.cam.thread_milling import (
    GewindeArt, GewindeRichtung,
    ThreadMillingParameter,
    erzeuge_thread_milling_toolpath,
)

params = ThreadMillingParameter(
    werkzeug_id="t_gewindefr_3mm",
    spindel_rpm=12000, vorschub=400, eintauch_vorschub=80,
    nenn_durchmesser=6.0,      # M6
    gewinde_steigung=1.0,      # M6 hat 1.0 mm Steigung
    gewinde_tiefe=8.0,         # 8 mm tief
    art=GewindeArt.INNEN,
    richtung=GewindeRichtung.RECHTS,
    werkzeug_durchmesser_korrektur=0.0,  # falls Fraeser nicht exakt nominal
    segmente_pro_umdrehung=36,           # Linear-Interpolation (mehr = glatter)
    mittelpunkt_x=100, mittelpunkt_y=50, # wo das Gewinde sitzen soll
    z_oberkante=0.0,                     # Z der Werkstuecks-Oberkante
)

tp = erzeuge_thread_milling_toolpath(werkzeug, params)
```

## Validierung

Die Funktion wirft `ThreadMillingFehler`, wenn:
- Werkzeug ≥ 95% vom Nenn-Durchmesser (passt nicht ins Loch bei Innen)
- Gewindetiefe < halbe Steigung (kein vollständiger Gang möglich)

## G-Code-Pattern

```
G0 X100 Y50 Z3          ; zum Mittelpunkt + Sicherheit
G0 X101.5 Y50 Z3        ; an Helix-Startpunkt (Radius 1.5)
G1 Z0 F80               ; Eintauch
G1 X.. Y.. Z-0.22 F400  ; Helix-Segment 1
G1 X.. Y.. Z-0.44 F400  ; Helix-Segment 2
...                     ; ... insgesamt n_umdrehungen × segmente
G1 X100 Y50 Z-8 F400    ; ZURUECK ZUR MITTE (wichtig!)
G0 X100 Y50 Z3          ; Lift
```

Die **Rückkehr zur Mitte** vor dem Lift ist essenziell — sonst kratzt der
Fräser beim Hochfahren am gerade geschnittenen Gewinde und beschädigt es.

## REST-API

```
POST /api/spezial-ops/thread-milling
Body:
{
  "parameter": {
    "werkzeug_id": "t_gewindefr_3mm",
    "spindel_rpm": 12000, "vorschub": 400, "eintauch_vorschub": 80,
    "nenn_durchmesser": 6.0, "gewinde_steigung": 1.0, "gewinde_tiefe": 8.0,
    "art": "innen", "richtung": "rechts"
  }
}
```

Response: Toolpath mit `metadaten.thread_milling = true` + Gewinde-Daten.

## Bekannte Einschränkungen

- **Tiefere Gewindeprofile** (z.B. Trapez, Säge) sind nicht unterstützt —
  nur metrisches Spitzgewinde
- **Mehrere Durchmesser-Sweeps** (z.B. erst grob, dann fein) muss man als
  separate Operationen anlegen
- **Werkzeug-Profil** wird ignoriert — der Fräser könnte theoretisch ein
  Vollprofil-Gewindefräser sein und in einem Pass das ganze Gewinde schneiden;
  wir machen nur Bahn-Kompensation, kein Profil-Versatz

## Verwandt

- [Operation-Bohren](Operation-Bohren) — für Vor-Loch
- [Werkzeug-Typen](Werkzeug-Typen) — Gewindefräser-Spezifika
