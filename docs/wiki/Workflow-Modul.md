# Multi-Setup Workflow-Modul

> **Status:** ✅ Implementiert (Phase 1: Setups + Pausen + Sicherheits-Checks + Arbeitsplan PDF/Markdown).
> **Issue:** [#13](https://github.com/MadGapun/CAMWOSA/issues/13)
> **Code:** [backend/camwosa/workflow/](../../backend/camwosa/workflow/) · **Tests:** [backend/tests/workflow/test_workflow.py](../../backend/tests/workflow/test_workflow.py)

Echte CNC-Werkstuecke brauchen oft mehrere Aufspannungen. Das Workflow-Modul macht das nativ:
- Eine Folge von **Setups** (jedes mit eigener G-Code-Datei)
- **Setup-Pausen** zwischen Setups (Werkzeugwechsel / Umspann / optionaler Stop)
- **Multi-Setup-Sicherheits-Checks**
- **Druckbarer Arbeitsplan** (PDF und Markdown)

## Datentypen

```python
class Setup:
    id: str
    name: str
    maschinen_modus: str          # "standard_xyz" | "rotary_y" | ...
    spannmittel: str
    werkzeug_id: str
    nullpunkt: tuple[float, float, float]
    operationen: list[OperationsKonfig]
    pause_vor: SetupPause | None
    foto_pfad: str | None
    geschaetzte_zeit_minuten: float

class SetupPause:
    typ: SetupPauseTyp            # WERKZEUGWECHSEL | UMSPANN | OPTIONALER_STOP
    titel: str
    anweisung: str                # Multi-line
    foto_pfad: str | None
    werkzeug_neu_id: str | None
    nullpunkt_neu: tuple | None
```

## Multi-Setup-Sicherheits-Checks

```python
from camwosa.workflow import pruefe_workflow

bericht = pruefe_workflow(variante)
if bericht.hat_blocker:
    for p in bericht.probleme:
        print(p.stufe, p.text)
```

Geprueft wird:
- **Modus-Wechsel ohne Pause** (KRITISCH) — z.B. von 3-Achs auf Rotary muss eine Umspann-Pause da sein.
- **Werkzeugwechsel ohne explizite Pause** (WARNUNG)
- **Pause ohne Anweisung** (WARNUNG)

## Arbeitsplan (PDF + Markdown)

```python
from camwosa.workflow import erzeuge_arbeitsplan_pdf, erzeuge_arbeitsplan_markdown

# PDF
bytes_data = erzeuge_arbeitsplan_pdf(
    variante, "Lotus-Schale", maschine, ziel_pfad="arbeitsplan.pdf",
)

# Markdown (z.B. fuer In-UI-Ansicht)
md = erzeuge_arbeitsplan_markdown(variante, "Lotus-Schale", maschine)
```

Beispiel-Output:

```
[ 1] [  ] Setup: 2D-Rohling
     Modus: standard_xyz   Werkzeug: schaft_6mm_2s_hm   Zeit: 25 min
     Spannmittel: Schraubzwingen x 4
     Nullpunkt: X=0.0 Y=0.0 Z=0.0

[ 2] [  ] PAUSE: Auf Rotary umspannen
     Typ: umspann
     Rotary einbauen, $101 pruefen, Macro ROTARY EIN

[ 3] [  ] Setup: Rotary-Schruppen
     Modus: rotary_y   Werkzeug: schaft_6mm_2s_hm   Zeit: 45 min
```

## G-Code pro Setup generieren

Jedes Setup bekommt seine **eigene G-Code-Datei** (sauberer als M0-Pausen in einer langen Datei):

```python
from camwosa.workflow import schreibe_gcode_pro_setup

dateien = schreibe_gcode_pro_setup(
    variante,
    maschine,
    werkzeug_index={"schaft_6mm_2s_hm": werkzeug},
    toolpaths_pro_setup={"setup1": [tp1], "setup2": [tp2, tp3]},
    ziel_verzeichnis="output/",
)
# {"setup1": Path("output/setup1_2D_Rohling.nc"), "setup2": ...}
```

CNCjs laedt einfach die naechste Datei, wenn du am Maschinen-Bediener bist.

### Getrennte Dateien bei Umbau / Umkabeln (Maschine aus) — M7

Eine **`M0`-Pause** im G-Code setzt voraus, dass die Maschine **eingeschaltet und
verbunden** bleibt — der Bediener drückt nach dem Eingriff einfach „Resume".

Manche Umbauten gehen aber **nur bei ausgeschalteter Maschine**: das **Umkabeln**
der Motoren beim Wechsel XYZ ↔ Rotary, oder das **Umverdrahten der Spindel**. Wird
die Maschine ausgeschaltet, **reißt die Streaming-Verbindung ab** — eine einzelne
Datei mit `M0`-Pause läuft dann nicht durch.

Dafür gibt es das Flag **`getrennte_datei`** auf Umspann-/Pause-/Achswechsel-Schritten
(in der Workflow-Ansicht: Checkbox *„Getrennte G-Code-Datei (Maschine aus / Umkabeln)"*
an der Pause). Ist es gesetzt, **endet der G-Code an dieser Stelle** und der Rest
kommt in eine eigene Datei. Die erste Datei bekommt am Ende einen Hinweis:

```
; >>> Maschine ausschalten + umbauen (Umspannen): Auf Rotary umkabeln — Danach naechste Datei laden. <<<
```

Ablauf am Bediener: Datei A laufen lassen → Maschine **aus** → umkabeln → Maschine
**an** → neu verbinden/homen → Datei B laden und starten.

- **Achswechsel** (`AchsWechselSchritt`, z.B. XYZ↔Rotary) hat `getrennte_datei`
  **standardmäßig an** — er bedeutet praktisch immer Umkabeln.
- **Umspannen/Pause** haben es standardmäßig aus (reines Umspannen geht bei laufender
  Maschine per `M0`) — du schaltest es ein, wenn der Eingriff Strom-Aus braucht.

> Passt zum **„kein direkter Sender-Push"**-Prinzip: getrennte Dateien sind genau der
> dateibasierte Übergabepunkt, an dem der Mensch die Maschine sicher stromlos macht.

## Werkstück-Umspannung (A49) — 2-/N-seitige Bearbeitung

Wenn du das Werkstück zwischen zwei Setups **umdrehst** (2-seitig) oder
**weiterdrehst** (N-seitig indexiert), müssen die Toolpaths von Seite B
geometrisch passen. CAMWOSA rechnet das automatisch um — du musst nichts von
Hand spiegeln.

**Schnellstart — Mehrseitig-Assistent:** In der Workflow-Ansicht oben rechts auf
*„⇄ Mehrseitig einrichten"*. Zwei Modi:
- **2-seitig (wenden):** Wenderichtung (an Y = links/rechts, an X = vorn/hinten)
  + Werkstück B×T wählen → legt automatisch „Seite B" mit gespiegelter Lage und
  einer Umspann-Pause an.
- **N-seitig (drehen):** Anzahl Seiten + B×T → legt N Setups an, jedes um 360°/N
  weitergedreht, mit Dreh-Pause dazwischen (für indexierte Bearbeitung /
  Klemmen-Umgehung).

Die Operationen pro Seite fügst du danach normal hinzu. Wer es manuell mag, stellt
die Lage direkt am Setup ein:

**So geht's (manuell):**

1. In der **Workflow-Ansicht** beim Setup unter *„Umspannung — Werkstück-Lage"*
   die Lage einstellen:
   - **Spiegeln/Wenden** an X (vorn/hinten) oder Y (links/rechts) — der klassische
     Brett-Umklapp-Fall.
   - **Drehung** 0/90/180/270° (für indexierte N-seitige Aufspannung).
   - **Z invertieren** (gewendet, Oberseite↔Unterseite).
   - **Werkstück B×T (mm)** — wird beim Spiegeln/Drehen als Mitte gebraucht.
2. Im **G-Code-Editor** beim Generieren oben *„Werkstück-Lage"* wählen — dort
   stehen alle Setups, die eine Umspannung hinterlegt haben. Wählst du eines, wird
   dessen Transformation **vor allen anderen Schritten** auf alle Toolpaths
   angewendet, dann erst Rampen/Fahrweg-Optimierung/Rapid-Safety (so rechnen die
   Sicherheits-Schritte auf den **finalen** Maschinen-Koordinaten).

**Bögen werden automatisch korrekt umgedreht:** Beim Spiegeln kippt die
Bogen-Drehrichtung (G2 ↔ G3) und die I/J-Mittelpunkt-Vektoren werden
mittransformiert. Das ist der Punkt, an dem hand-gespiegelter G-Code sonst falsche
Kreise fräst.

> ⚠️ **Spiegeln ohne Werkstückmaß** spiegelt um die Null-Linie → negative
> Koordinaten. Trage immer die Werkstück-Breite/Tiefe im Setup ein. Der
> G-Code-Editor warnt, wenn das Maß fehlt.

API: `POST /api/operations/postprocess` mit `transformation: {spiegeln, drehung_grad,
invertiere_z, offset, werkstueck_breite_mm, werkstueck_tiefe_mm}`. Einzelnen Toolpath
transformieren: `POST /api/operations/transformiere`. MCP:
`gcode_erzeugen(..., transformation={...})` bzw. `toolpath_transformieren(...)`.

## Setup-Foto

Jedes Setup hat einen optionalen `foto_pfad` — beim ersten Lauf einmal fotografiert, beim Wiederholungs-Lauf hat man Vergleichsbild.

## MCP-Tools

| Tool | Zweck |
|------|-------|
| `setup_erstellen(variante_id, name, maschinen_modus)` | Neues Setup hinzufuegen |
| `setup_pause_einfuegen(setup_id, typ, anweisung)` | Pause vor Setup setzen |
| `arbeitsplan_generieren(variante_id, format)` | PDF/Markdown erzeugen |
| `workflow_pruefen(variante_id)` | Sicherheits-Bericht |
| `gcode_pro_setup_schreiben(variante_id, ziel)` | Eine Datei pro Setup |

## Erweiterungen (Phase 1+)

- Foto-Slot mit Bild-Vergleich (Schieberegler in UI)
- Zeit-Tracking (geplant vs. tatsaechlich)
- Werkzeug-Standzeit-Update zwischen Setups (Phase E2)

## Verwandt

- [Projekt-Format](Projekt-Format.md)
- [Postprozessor-GRBL](Postprozessor-GRBL.md)
- [Sicherheits-Checks](Sicherheits-Checks.md)
- [Arbeitsplan](Arbeitsplan.md)
