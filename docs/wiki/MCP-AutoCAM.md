# MCP-AutoCAM (`auto_cam_erstellen`)

> **Status:** ✅ Backend + MCP-Tool + 13 Tests.
> **Code:** [backend/camwosa/workflow/auto_cam.py](../../backend/camwosa/workflow/auto_cam.py) · **Tests:** [test_auto_cam.py](../../backend/tests/workflow/test_auto_cam.py)
> **Master-Plan-Position:** [B6](Master-Plan.md)

Hochwertiger MCP-Tool fuer **„Claude erstellt eine komplette Bearbeitung"**: ein Aufruf, ein fertiges Projekt mit Variante, Setup, Operationen, ArbeitsSchritt-Liste — ohne dass der User durch alle Editoren klicken muss.

## Drei Aufgaben-Typen (heute)

### 1. `tasche`

Rechteckige Tasche mit **regelbasierter Schrupp+Schlicht-Entscheidung**.

```python
auto_cam_erstellen(
    aufgabe="tasche",
    name="Schluesselbrett-Aussparung",
    maschine_id="genmitsu_proverxl_4030_v2",
    material_id="buche_massiv",
    parameter={
        "breite_mm": 80, "hoehe_mm": 40, "tiefe_mm": 8,
        "werkzeug_durchmesser_mm": 6,   # Wunsch-Schruppen
        "material_haerte": "hart",       # senkt Schrupp+Schlicht-Schwelle
    },
)
```

**Heuristik**:
- Tiefe ≥ 5mm (weich) bzw. ≥ 3mm (hart/metall) → Schruppen + Schlichten in 2 Operationen
- Schrupp-Werkzeug: Schaftfraeser nahe am Wunsch-Durchmesser
- Schlicht-Werkzeug: naechstkleiner Schaft- oder Kugelfraeser
- ArbeitsSchritt-Liste mit Werkzeugwechsel (Separate-Datei-Strategie)
- Ohne kleineres Werkzeug → nur Schruppen + Hinweis

### 2. `anschlagbohrungen`

4 Loecher in den Ecken eines Werkstuecks.

```python
auto_cam_erstellen(
    aufgabe="anschlagbohrungen",
    name="Stifte fuer 200x150mm Brett",
    maschine_id="genmitsu_proverxl_4030_v2",
    material_id="buche_massiv",
    parameter={
        "werkstueck_breite_mm": 200,
        "werkstueck_hoehe_mm": 150,
        "randabstand_mm": 15,
        "durchmesser_mm": 3,
        "tiefe_mm": 8,
    },
)
```

**Heuristik**:
- Sucht Bohrer-Typ bevorzugt, Schaftfraeser als Fallback
- Warnt bei Werkzeug-Durchmesser-Abweichung
- Eine Bohren-Operation mit allen 4 Punkten

### 3. `beschriftung_wrap`

Text auf Rundmaterial wickeln (Continuous-Lathe-Vorbereitung).

```python
auto_cam_erstellen(
    aufgabe="beschriftung_wrap",
    name="Saeule mit Schriftzug",
    maschine_id="genmitsu_proverxl_4030_v2",
    material_id="buche_massiv",
    parameter={
        "text": "MADGAPUN",
        "werkstueck_radius_mm": 20,
        "gravur_tiefe_mm": 0.5,
    },
)
```

**Heuristik**:
- Bevorzugt V-Bit oder Gravierstichel
- Setup wird im `rotary_y`-Modus angelegt
- Text-zu-Pfad-Konversion ist noch nicht implementiert (Hinweis im Ergebnis) — User muss die Pfad-Punkte selbst nachpflegen

## Antwort-Format

```json
{
  "projekt": { /* komplettes CWPProjekt-JSON */ },
  "hinweise": [
    "Tiefe 8.0mm >= Schwelle (weich) -> Schrupp+Schlicht mit schaft_6mm + schaft_2mm",
    "Werkzeug-Durchmesser 3.175mm weicht von Wunsch 3mm ab — Loch wird entsprechend groesser."
  ]
}
```

Die **Hinweise** machen die Entscheidungen transparent — der User sieht WARUM Claude welches Werkzeug gewählt hat, welche Strategie angewandt wurde, etc.

## Bewusst regelbasiert, nicht LLM-basiert

Die Entscheidungen sind in `auto_cam.py` als **klare Python-Regeln** umgesetzt — keine generative KI. Vorteile:

- **Reproduzierbar**: gleiche Eingabe → gleiche Ausgabe
- **Erklaerbar**: jede Entscheidung steht im Code
- **Lokal**: keine Cloud-Anrufe, keine API-Kosten
- **Schnell**: kein Netzwerk-Roundtrip noetig

Wer **echte LLM-Entscheidungen** will: Claude ruft den MCP-Tool selbst mit seinen Wunsch-Parametern auf. Damit ist die KI im _Claude-Loop_, nicht im Backend.

## Zukuenftige Aufgaben-Typen

Die Architektur (Dispatcher in `auto_cam_erstellen`) ist auf Erweiterung ausgelegt. Sinnvolle Naechste:

- `kontur_ausschneiden` — Aussenkontur mit Tabs (existing Quick-CAM-Template)
- `drechseln_profil` — komplette Drechsel-Aufgabe aus Profil-Punkten
- `bild_relief` — kombiniert Bild-zu-Heightmap + Relief-Operation
- `bild_relief_wrap` — Phase C: Heightmap auf Zylinder

## Verwandt

- [QuickCAM](QuickCAM) — Frontend-Template-System (User klickt eine Vorlage)
- [ArbeitsSchritt](ArbeitsSchritt) — Multi-Werkzeug-Workflow-Datenmodell
- [Multi-Werkzeug-Setup](Multi-Werkzeug-Setup) — Schrupp+Schlicht in einer Aufspannung
- [MCP-Server](MCP-Server) — Claude-Integration
