# ArbeitsSchritt — flexibles Workflow-Element

> **Status:** ✅ Datenmodell + Pruefungen + Legacy-Konvertierung.
> **Code:** [backend/camwosa/project/schritte.py](../../backend/camwosa/project/schritte.py) · **Tests:** [backend/tests/project/test_schritte.py](../../backend/tests/project/test_schritte.py)

Ein **ArbeitsSchritt** ist die kleinste anordnbare Einheit im Workflow eines Setups. Statt einem starren „pause_vor + operationen[]"-Block kann ein Setup jetzt beliebig viele Schritte in beliebiger Reihenfolge haben — auch mehrere Werkzeugwechsel, Pausen, Manual-NC-Bloecke etc.

## Warum?

Reale Workflows passen nicht in das alte Modell:

- Werkzeugwechsel **mitten** im Setup (gleiches Spannmittel, anderes Werkzeug)
- **Manual NC** mittendrin (Vakuumpumpe an, Spindel-Warm-Up, Z-Probe)
- **Achswechsel** mitten im Setup (von Rotary auf XYZ, Werkstueck bleibt)
- **Mehrere Pausen** hintereinander (Spindel-Wechsel + Werkstueck-Drehung)
- Pause vor *einer einzelnen Operation* statt vor dem ganzen Setup

## Schritt-Typen

```python
class ArbeitsSchritt:
    # Discriminated Union: ein Schritt ist genau einer dieser Typen
    OperationSchritt        # fuehrt eine CAM-Operation aus
    WerkzeugWechselSchritt  # wechselt Werkzeug, optional mit Mensch-Pause
    UmspannSchritt          # Werkstueck neu einspannen
    AchsWechselSchritt      # Modus aendert sich (XYZ <-> Rotary, etc.)
    ManualNCSchritt         # beliebige G-Code-Zeilen direkt einfuegen
    PauseSchritt            # generische Mensch-Pause
```

Pydantic-Discriminated-Union ueber `typ`-Feld — beim Deserialisieren wird automatisch der richtige Subtyp gewaehlt.

### Datei-Trennung bei Umbau (`getrennte_datei`, M7)

`UmspannSchritt`, `PauseSchritt` und `AchsWechselSchritt` haben ein Flag
`getrennte_datei`. Ist es gesetzt, **trennt der G-Code-Export an dieser Stelle in
eine neue Datei** (statt einer `M0`-Pause im selben Job). Das ist noetig, wenn die
Maschine fuer den Eingriff **ausgeschaltet** werden muss (Umkabeln XYZ↔Rotary,
Spindel umverdrahten) — dann reisst die Streaming-Verbindung ab und eine
Einzeldatei mit Pause laeuft nicht durch.

- `AchsWechselSchritt`: Default **True** (Moduswechsel = praktisch immer Umkabeln).
- `UmspannSchritt` / `PauseSchritt`: Default **False** (reines Umspannen geht bei
  laufender Maschine per `M0`).

Die erste Datei bekommt am Ende einen Hinweis-Kommentar
(`; >>> Maschine ausschalten + umbauen … — Danach naechste Datei laden. <<<`).
Verwandt: `WerkzeugWechselStrategie.SEPARATE_DATEI` macht dasselbe fuer
Werkzeugwechsel (Schruppen + Schlichten ohne ATC).

## Beispiel: gemischter Workflow

```python
setup.schritte = [
    WerkzeugWechselSchritt(id="s1", werkzeug_neu_id="t_6mm",
                           anweisung="6mm Schaftfraeser einsetzen, Z-Null setzen"),
    OperationSchritt(id="s2", operation_id="kontur_aussen"),
    ManualNCSchritt(id="s3", gcode_zeilen=["M62 P0 ; Vakuum AN", "G4 P2"]),
    OperationSchritt(id="s4", operation_id="tasche_innen"),
    WerkzeugWechselSchritt(id="s5", werkzeug_neu_id="t_2mm",
                           anweisung="2mm Fraeser einsetzen"),
    OperationSchritt(id="s6", operation_id="gravur_logo"),
    AchsWechselSchritt(id="s7", modus_alt="standard_xyz", modus_neu="rotary_y",
                       anweisung="Rotary-Aufsatz montieren"),
    PauseSchritt(id="s8", anweisung="Werkstueck im Spannfutter zentrieren"),
    OperationSchritt(id="s9", operation_id="rotary_gravur"),
]
```

## ManualNCSchritt — beliebige G-Code-Zeilen

Macht Sinn fuer:

| Zweck | Zeilen |
|-------|--------|
| Spindel-Warmlauf | `M3 S10000`, `G4 P30` |
| Programm-Stop fuer Inspektion | `M0` |
| Werkzeug-Vermessung (Z-Probe) | `G38.2 Z-10 F100` |
| Vakuumtisch ein/aus | `M62 P0` / `M63 P0` |
| Coolant Mist | `M7` / `M9` |
| Kommentar in Output | `; --- Phase: Schlichten ---` |

WICHTIG: keine Validierung der Zeilen — der User ist verantwortlich. Der Postprozessor schreibt sie unveraendert hinein.

## Pruefungen

`pruefe_schritt_liste()` liefert Probleme als Strings:

- ManualNC ohne `gcode_zeilen` ist sinnlos
- Operation direkt nach AchsWechsel ohne Pause dazwischen
- Doppelte Schritt-IDs
- Werkzeugwechsel-Schritte bekommen `werkzeug_alt_id` automatisch ausgefuellt

## Backwards-Kompatibilitaet

Bestehende Setups haben `schritte=[]` — `Setup.effektive_schritte()` erkennt das und baut die Schritt-Liste aus dem alten Format zusammen:

```
pause_vor → entsprechender Schritt-Typ (WerkzeugWechsel/Umspann/Pause)
operationen[] → je ein OperationSchritt
```

So funktionieren alte .cwp-Projekte unveraendert weiter. Sobald der User in der UI Schritte umsortiert oder einen Manual-NC einfuegt, wird `schritte[]` befuellt und ist dann die einzige Quelle.

## Verwandt

- [Workflow-Modul](Workflow-Modul)
- [Projekt-Format](Projekt-Format)
- [Werkzeug-Modell](Werkzeug-Modell)
