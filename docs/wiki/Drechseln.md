# Drechseln (Continuous-Lathe-Mode)

> **Modus-Einordnung**: CAMWOSA kennt **drei Rotary-Operations-Modi** (Industrie-Standard):
>
> | Modus | Wann | G-Code-Form |
> |-------|------|-------------|
> | Indexed | mehrere Faces in einem Werkstueck | nur XYZ, A nur als Setup zwischen Phasen |
> | [Wrap](Wrap-Mode) | Gravur/Schriftzug/Kontur auf Zylinder | X+A+Z simultan pro Bewegung |
> | **Drechseln** (diese Seite) | rotationssymmetrische Aussenformen | nur X+Z, A dreht extern kontinuierlich |
>
> Wer einen Schriftzug auf eine Drechsel-Saeule gravieren will: → [Wrap-Mode](Wrap-Mode).
> Wer eine Vase aus einem Rundling drechseln will: → diese Seite.

> **Status:** ✅ Backend + Postprozessor + Frontend-Profil-Editor + 3D-Revolution-Preview.
> **Code:** [backend/camwosa/cam/drechseln.py](../../backend/camwosa/cam/drechseln.py) · [DrechselParameter](../../backend/camwosa/cam/parameter.py) · [DrechselnView](../../frontend/src/views/DrechselnView.tsx) · [DrechselProfilEditor](../../frontend/src/editor/DrechselProfilEditor.tsx)
> **API:** `POST /api/operations/drechseln` · **MCP:** `operation_drechseln`
> **Tests:** [test_drechseln.py](../../backend/tests/cam/test_drechseln.py), [test_drechseln_api.py](../../backend/tests/api/test_drechseln_api.py)

## Was das wirklich ist (Hardware-Realitaet)

CAMWOSA's „Drechseln" ist **kein klassisches Drechseln** auf einer Drehmaschine.
Auf der ProVerXL mit Rotary-Aufsatz arbeitet das System so:

- **Spindel haengt vertikal** an der Z-Achse — das **Fraeswerkzeug** rotiert mit
  hoher Drehzahl (typ. 10000–30000 RPM) und kommt **von oben**.
- **Werkstueck dreht sich langsam** um seine Laengsachse via Rotary-Aufsatz
  (typ. 100–500 U/min). Die A-Achse ist auf Y umgemappt.
- Bearbeitung passiert immer an der **OBERSEITE** des Werkstuecks — der
  Fraeser greift dort an, das Werkstueck dreht sich darunter durch, so dass
  ueber eine ganze Werkstueck-Umdrehung die komplette Aussen-Oberflaeche
  bestrichen wird.

Das ist technisch **„Wrap-Carving" / „4-Achs-Fraesen mit Werkstueck-Rotation"**,
aber das Ergebnis ist Drechsel-aehnlich (rotationssymmetrische Formen) und der
User-Begriff stimmt — deshalb heisst das Modul weiterhin „Drechseln".

## Geht / Geht nicht

| Was | Status |
|-----|--------|
| Aussenkontur (Vase, Schale aussen, Drechsel-Saeule, Bowling-Pin) | ✅ |
| Helix-Nut, Schraubmuster, Spirale | ✅ |
| Plandrehen-aehnliche Operationen (Z=const) | ✅ |
| Konische Formen | ✅ |
| **Innen-Drechseln** (Schalen-Innen) | ❌ Spindel haengt vertikal — Fraeser kommt nicht von der Seite rein |
| 360°-Bearbeitung ohne Werkstueck-Rotation | ❌ Werkstueck MUSS drehen |
| Hinterschneidungen | ❌ Werkzeug nicht abwinkelbar |

## Achsen-Konvention

| Achse | Bedeutung |
|-------|-----------|
| X | Position entlang der Werkstueck-Laengsachse (mm) |
| Y | im Toolpath nicht genutzt — A-Drehung laeuft global, kein G-Code |
| Z | Hoehe der Werkzeug-Spitze ueber der Mittel-Drehachse (= Soll-Radius) |
| A (Y umgemappt) | Werkstueck-Drehung mit ``drehzahl_werkstueck_upm`` — extern via Sender-Macro gestartet |

**Nullpunkt-Referenz: `mitte_drehachse`** — Z=0 sitzt exakt auf der Mittelachse des Rotary. Wenn das Rohmaterial Ø40mm hat, ist die Oberflaeche bei Z=20mm; der Fraeser positioniert sich auf Z=20 um knapp ueber dem Material zu fahren.

## Profil

Eingabe ist ein **Halbschnitt** des fertigen Werkstuecks: Liste von `(laenge_x_mm, radius_mm)`-Tupeln.

Beispiel — eine einfache Vase (außen):
```python
profil = [
    (0,   25),   # Boden, breit
    (20,  30),   # Schulter
    (50,  20),   # Bauch nach innen
    (100, 28),   # Hals weitet sich wieder
    (120, 24),   # Mundstueck
]
```
X muss aufsteigend sein. Radius darf nicht groesser als `rohmaterial_radius_mm` sein (sonst Validierungs-Fehler).

## Drei Strategien

### `laengs_schruppen`

Schaelt konzentrische Schalen ab — von außen nach innen, immer um `stepdown` reduziert. Pro Pass faehrt das Werkzeug einmal die volle Werkstueck-Laenge. Die X-Richtung alterniert pro Pass (Hin- und Rueckweg ohne Abheben). Wenn ein Z-Pass eine Stelle erreicht wo das Profil tiefer liegt, bleibt das Werkzeug auf dem Profil-Radius + Aufmass (so wird nicht reingeschnitten).

Schnelle Material-Abnahme — danach ist die Oberflaeche aber stufig. Schlichten ist haendisch oder per `profil_schlichten` notwendig.

### `profil_schlichten`

Werkzeug folgt dem Profil 1:1 in einem einzigen Pass. Saubere Oberflaeche, aber nur wenig Material-Abnahme pro Aufruf. Sinnvoll als Endpass nach dem Schruppen.

### `schrupp_und_schlicht` (Default)

Erst Schruppen mit Aufmass, dann Schlichten — beide Toolpath-Bloecke in einem Aufruf. Der typische „mach den Job"-Modus.

### `helix`

Helikale Nut, Schraube oder Spiral-Muster. Werkzeug faehrt synchronisiert
zu der Werkstueck-Drehung in X — pro Werkstueck-Umdrehung um
`helix_steigung_mm_pro_umdrehung` weiter.

**Vorschub-Synchronisation**: der X-Vorschub wird automatisch berechnet als
`steigung × drehzahl_werkstueck_upm` (Einheit mm/min). Beispiel: 2 mm/U bei
250 U/min → 500 mm/min X-Vorschub.

**Mehrere Passes**: tiefe Nuten (z.B. 6 mm) werden in `helix_anzahl_passes`
Schichten gefraest (pro Pass tiefer eintauchen). Zwischen Passes hebt das
Werkzeug NICHT ab — es taucht am X-Start zur nächsten Tiefe.

**Profil-Folgen**: bei konischem Werkstueck folgt die Helix dem Profil
(Z = Profil_Radius − Tiefe). Bei zylindrischem Werkstueck ist das eine
einfache, konstante Z-Position.

**X-Bereich**: `helix_x_start_mm` / `helix_x_ende_mm` können den X-Bereich
einschraenken (z.B. nur die mittleren 60 mm einer 100 mm Drechsel-Saeule
mit Schraubmuster versehen). Wenn beide `None` sind, wird der volle
Profil-Bereich genutzt.

⚠️ **Genauigkeits-Hinweis Helix-Mode**: Diese Variante baut auf der
**Annahme** dass die A-Achse konstant mit `drehzahl_werkstueck_upm` rotiert.
Sie funktioniert in der Praxis solange das Backenfutter nicht schlupft und
die Drehzahl stabil bleibt — bei Schlupf kann die Steigung abweichen.

Wer industrie-saubere Genauigkeit braucht (z.B. Praezisionsschraube), nutzt
besser den **[Wrap-Mode](Wrap-Mode)**: dort werden A-Werte explizit pro
Bewegung im G-Code ausgegeben, der Controller interpoliert exakt — Schlupf
wuerde dort ausgeregelt werden (sofern die A-Achse Stepper-getrieben ist).

Praktischer Unterschied:
- **Helix-Drechselmodus**: schnelles Anlegen, einfacher G-Code, fuer
  optisches Schraubmuster auf einer Drechsel-Saeule absolut ausreichend
- **Wrap-Modus**: praeziser, aber Design muss als 2D-Pfad in der
  abgewickelten Form vorliegen

## Parameter

```python
class DrechselParameter:
    # OperationParameter-Basis
    werkzeug_id: str
    spindel_rpm: float
    vorschub: float            # X-Vorschub mm/min
    eintauch_vorschub: float   # Z-Plunge mm/min
    sicherheitshoehe: float    # ueber Rohmaterial-Oberflaeche
    max_tiefe: float           # = max abzutragender Radius
    stepdown: float            # Radius-Reduktion pro Pass

    # Drechsel-spezifisch
    strategie: DrechselStrategie = SCHRUPP_UND_SCHLICHT
    rohmaterial_radius_mm: float
    aufmass_schlichten_mm: float = 0.3      # Reserve fuer Schlicht-Pass
    schlicht_zustellung_mm: float = 0.5     # Pass-Tiefe Schlichten (auch X-Schrittweite)
    drehzahl_werkstueck_upm: float = 200    # A-Achsen-Drehzahl
    profil: list[tuple[float, float]]       # [(laenge_x_mm, radius_mm), ...]
```

## Postprozessor-Integration

Der `grbl_genmitsu_rotary_y`-Postprozessor erkennt Drechsel-Toolpaths am Marker
`metadaten.ist_drechseln=True` und schreibt automatisch:

1. **Globaler Drechsel-Header** vor dem normalen `G21 G90`-Block:
   ```
   ; ============================================================
   ; DRECHSEL-JOB — VOR DEM START PRUEFEN
   ;   - 1 Drechsel-Toolpath(s) im File
   ;   - Werkstueck-Drehzahl(en) U/min: 250
   ;   - Rotary-Aufsatz montiert? Werkstueck zentriert? Reitstock fest?
   ;   - CNCjs: ROTARY EIN aufrufen (oder Aequivalent)
   ;   - WICHTIG: Werkstueck-Drehung BEVOR Werkzeug eintaucht starten
   ; ============================================================
   ```
2. **Pro Drechsel-Toolpath**: Strategie, Werkstueck-Drehzahl, Rohmaterial-Radius +
   ein `; %wait`-Hinweis fuer CNCjs (optionale Pause, damit der User die
   A-Achsen-Rotation manuell bestaetigen kann).
3. **Drechsel-Nachlauf**: Hinweis dass die A-Drehung jetzt gestoppt werden darf.

So bekommt der User im G-Code-Editor (Monaco) eine sichtbare Setup-Checkliste
oben im File und kann nichts vergessen.

## Wichtige Annahmen + offene Punkte

- **Werkstueck-Drehung wird NICHT automatisch geschaltet**: CAMWOSA schreibt
  G-Code in Dateien, kein direkter Sender-Push. Der User startet die A-Drehung
  vor dem Job manuell (CNCjs-Makro „ROTARY EIN" o.Ae.) und stoppt sie danach.
- **Werkzeug-Geometrie-Kompensation (Z-Offset)**: Der Algorithmus erkennt
  Kugel- und Torusfraeser und hebt den Z-Wert automatisch um den Werkzeug-
  Radius an — sodass die Schneide den Soll-Radius trifft, nicht der
  Werkzeug-Mittelpunkt. Schaftfraeser/V-Bit/Bohrer: kein Offset.
- **Fraeser-Eingriffsbreite in X** wird nicht voll modelliert — der
  Algorithmus geht von einer punktfoermigen Werkzeug-Spitze aus. Bei dicken
  Kugelfraesern muss der User die Schlicht-Zustellung defensiv waehlen,
  sonst bleiben sichtbare Spuren zwischen den Bahnen.
- **Drehzahl-Konstanz** ist beim Helix-Mode kritisch. Wenn das Backenfutter
  schlupft, faellt die Steigungs-Genauigkeit.
- **Kein Innen-Drechseln moeglich (hardware-bedingt)** — Spindel haengt
  vertikal, der Fraeser kommt nicht von der Seite in einen Hohlraum rein.
  Wer Schalen-Innen will, spannt das Werkstueck danach um und bearbeitet
  es als Standard-XYZ-Job mit Tasche-Operation. KEIN Software-Ausbau in
  Sicht — geht nur mit anderer Hardware.

## Frontend

[DrechselnView](../../frontend/src/views/DrechselnView.tsx) ist eine eigene View
(Sidebar-Eintrag „Drechseln") und bringt:

- **DrechselProfilEditor** ([editor/DrechselProfilEditor.tsx](../../frontend/src/editor/DrechselProfilEditor.tsx))
  - Links: 2D-Halbschnitt in Konva. Klick = neuer Punkt · Drag = verschieben (Snap 0.5mm) · Rechtsklick = löschen. Rohmaterial-Radius als gelb gestrichelte Linie.
  - Rechts: **3D-Revolution-Preview** mit Three.js `LatheGeometry` — das Profil wird live um die X-Achse rotiert und zeigt das fertige Werkstück (mit Rohmaterial als Wireframe-Zylinder).
  - Kamera dreht automatisch um die Werkstücks-Achse für 3D-Eindruck.
- **3 Vorlagen-Buttons**: Vase, Zylinder Ø36×100, Kegel
- **Strategie-Dropdown** mit allen 4 Strategien (Schruppen, Schlichten, Schrupp+Schlicht, Helix)
- **Helix-Sektion** erscheint nur bei Strategie `helix` — mit Live-Anzeige des sync-Vorschubs (= Steigung × Drehzahl)
- Erzeugt direkt ein `OperationEintrag` im App-Store mit dem fertigen Toolpath

## API

`POST /api/operations/drechseln`:

```json
{
  "werkzeug_id": "dreh_meissel",
  "parameter": {
    "werkzeug_id": "dreh_meissel",
    "spindel_rpm": 10000,
    "vorschub": 300, "eintauch_vorschub": 150,
    "sicherheitshoehe": 5,
    "max_tiefe": 15, "stepdown": 1.5,
    "rohmaterial_radius_mm": 20,
    "aufmass_schlichten_mm": 0.3,
    "schlicht_zustellung_mm": 0.5,
    "drehzahl_werkstueck_upm": 300,
    "profil": [[0, 18], [50, 12], [100, 18]],
    "strategie": "schrupp_und_schlicht"
  }
}
```

Antwort: vollstaendiger Toolpath mit Metadaten — direkt im Frontend simulier- und postprozessierbar.

## MCP

```python
operation_drechseln(werkzeug_id, parameter)
```

Claude kann z.B. sagen: „Mach mir eine 100 mm lange Drechselei mit Bauch in der Mitte (Profil 18-12-18 mm Radius) aus Ø 40 mm Buche".

## Verwandt

- [Rotary-Profil-System](Rotary-Profil)
- [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary)
- [Operation-Plugins](Operations-Plugins)
- [ArbeitsSchritt](ArbeitsSchritt) — Drechsel-Operationen koennen als OperationSchritt in den Multi-Schritt-Workflow
