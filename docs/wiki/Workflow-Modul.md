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
