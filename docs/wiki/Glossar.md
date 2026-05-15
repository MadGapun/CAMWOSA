# Glossar

CAM- und CNC-Begriffe wie sie in CAMWOSA verwendet werden, mit deutscher und englischer Entsprechung.

## CAM-Operationen

| Deutsch | Englisch | Erklärung |
|---------|----------|-----------|
| Kontur | Profile / Contour | Werkzeug folgt einer Kurve |
| Tasche | Pocket | Geschlossene Fläche wird ausgeräumt |
| Bohren | Drilling | Reine Z-Bewegung an definierten Punkten |
| Gravieren | Engrave | Folgt einer Kurve mit definierter Tiefe |
| V-Carving | V-Carving | Gravur mit variabler Tiefe (V-Bit) |
| Schruppen | Roughing | Material grob abtragen |
| Schlichten | Finishing | Letzter Durchgang für saubere Oberfläche |
| Relief | Relief | 2.5D-Geometrie aus Heightmap |
| Adaptive Clearing | Adaptive Clearing / Trochoidal | Konstanter Werkzeug-Eingriff bei hoher Spanabnahme |

## CAM-Parameter

| Deutsch | Englisch | Symbol | Einheit | Erklärung |
|---------|----------|--------|---------|-----------|
| Vorschub | Feed Rate | Vf, F | mm/min | Geschwindigkeit der Schnittbewegung |
| Eilgang | Rapid | G0 | mm/min | Bewegung ohne Materialabtrag |
| Eintauchvorschub | Plunge Rate | — | mm/min | Senkrechte Z-Bewegung in Material |
| Schnitttiefe pro Durchgang | Depth of Cut / Stepdown | ap | mm | Wieviel pro Z-Pass |
| Seitliche Zustellung | Stepover | ae | mm oder % | Seitlicher Versatz pro Bahn |
| Schnittgeschwindigkeit | Cutting Speed | Vc | m/min | Umfangsgeschwindigkeit am Werkzeug |
| Zahnvorschub | Feed per Tooth | fz | mm/Zahn | Vorschub pro Schneide |
| Spindeldrehzahl | Spindle Speed | n, S | RPM, U/min | Drehzahl der Spindel |
| Spanvolumen | Material Removal Rate | Q | cm³/min | Materialabtrag pro Zeit |
| Sicherheitshöhe | Clearance Height | — | mm | Z-Höhe für Eilgang über Werkstück |
| Aufmass | Stock-to-Leave / Allowance | — | mm | Material das für späteren Schlichtgang stehen bleibt |
| Tab / Haltesteg | Tab | — | mm | Verbindungsstück damit Teil nicht ausbricht |
| Rampe | Ramp | — | ° | Schräges Eintauchen |
| Helix-Eintauchen | Helical Plunge | — | — | Schraubiges Eintauchen |
| Lead-In / Lead-Out | Lead-In / Lead-Out | — | — | Werkzeug-Anfahrt/-Abfahrt zur Kontur |
| Gleichlauf | Climb Milling | — | — | Werkzeug dreht "mit" der Vorschubrichtung |
| Gegenlauf | Conventional Milling | — | — | Werkzeug dreht gegen Vorschubrichtung |
| Spitzenwinkel | Tip Angle | — | ° | Bei V-Bits, z.B. 60° |
| Spanbrechen | Peck Drilling | G83 | — | Bohren mit Rückzug zur Spanabfuhr |

## Werkzeuge

| Deutsch | Englisch | Kurz |
|---------|----------|------|
| Schaftfräser | Flat End Mill | Standardwerkzeug, flache Stirn |
| Kugelfräser | Ball End Mill | Halbkugel-Spitze, für 3D-Konturen |
| Torusfräser / Eckenfräser | Bull Nose / Toroidal | Eckenradius, lange Standzeit |
| V-Bit | V-Bit / V-Carving Bit | V-förmige Spitze für Gravuren |
| Gravierstichel | Engraving Bit | Sehr feine Spitze |
| Bohrer | Drill | Reine Bohrungen |
| Einschneider | Single Flute | 1 Schneide für Spanabfuhr (Alu, Acryl) |
| Fischschwanz | Fishtail | Senkrecht eintauchend, saubere Konturen |
| Schruppfräser | Roughing End Mill | Geriffelte Schneide, hoher Spanabtrag |
| Diamantgravierer | Diamond Drag Engraver | Schleif-Werkzeug für harte Materialien |
| Schaft-Durchmesser | Shank Diameter | — |
| Schneidlänge | Cutting Length / Length of Cut | — |
| Gesamtlänge | Overall Length | — |
| Schneidenanzahl | Number of Flutes | — |
| Upcut / Downcut / Compression | Upcut / Downcut / Compression | Spanrichtung |
| Beschichtung | Coating | TiN, TiAlN, DLC etc. |

## Maschine / Steuerung

| Deutsch | Englisch | Erklärung |
|---------|----------|-----------|
| Arbeitsraum | Work Envelope | Maximaler Verfahrweg X/Y/Z |
| Nullpunkt | Origin / Workpiece Zero | Ursprung des Werkstück-Koordinatensystems |
| Werkstück-Koordinatensystem | Work Coordinate System (WCS) | G54-G59 |
| Maschinen-Koordinatensystem | Machine Coordinate System | Absolut, vom Maschinen-Nullpunkt |
| Park-Position | Park Position | Sichere Position für Werkzeugwechsel |
| Aufspannung | Setup / Workholding | Wie das Werkstück auf der Maschine fixiert ist |
| Schraubzwinge | Clamp | — |
| Schraubstock | Vise | — |
| Spannfutter | Chuck | Bei Rotary |
| Reitstock | Tailstock | Bei Rotary |
| Wachstisch | Wasteboard / Spoilboard | Opfer-Platte unter Werkstück |
| T-Nutenplatte | T-Track Table | Maschinentisch mit T-Nuten |
| Probing / Antasten | Probing | Werkzeug findet Werkstück-Position |
| GRBL | GRBL | Open-Source-Firmware für Mikrocontroller-CNC |
| Soft-Limits | Soft Limits | Software-Grenzen des Arbeitsraums |
| Hard-Limits | Hard Limits | Endschalter-Grenzen |

## CAMWOSA-spezifisch

| Begriff | Bedeutung |
|---------|-----------|
| `.cwp` | CAMWOSA Project — ZIP-Container mit Projekt-Daten |
| Setup | In sich abgeschlossener Job mit eigener G-Code-Datei |
| Setup-Pause | Anweisung zwischen zwei Setups (Umspannen / Werkzeugwechsel / Inspektion) |
| Variante | Auspraegung eines Projekts (z.B. anderes Material) |
| Maschinen-Modus | XYZ-Standard oder Rotary innerhalb desselben Maschinenprofils |
| Postprozessor | Modul das Toolpath in maschinenspezifischen G-Code umwandelt |
| Arbeitsplan | Druckbare Checkliste aus den Setups eines Projekts |

## G-Code-Befehle (Auswahl)

| Code | Bedeutung |
|------|-----------|
| G0 | Eilbewegung (kein Materialabtrag) |
| G1 | Lineare Schnittbewegung |
| G2 / G3 | Kreisbogen im / gegen Uhrzeigersinn |
| G17 / G18 / G19 | Arbeitsebene XY / XZ / YZ |
| G20 / G21 | Einheiten Zoll / mm |
| G54..G59 | Werkstück-Koordinatensystem 1..6 |
| G81 | Standard-Bohrzyklus |
| G82 | Bohrzyklus mit Verweildauer |
| G83 | Tief-Bohrzyklus mit Spanbrechen |
| G90 / G91 | Absolute / Relative Koordinaten |
| M0 | Programm-Pause |
| M3 / M4 / M5 | Spindel CW / CCW / Stop |
| M6 | Werkzeugwechsel (in GRBL als M0-Pause) |
| M30 | Programm-Ende |

## Material-Begriffe

| Deutsch | Englisch | Anmerkung |
|---------|----------|-----------|
| Janka-Härte | Janka Hardness | Holz-Härte-Index |
| Dichte | Density | g/cm³ |
| Sperrholz / Multiplex | Plywood | — |
| Spanplatte | Particle Board / Chipboard | — |
| MDF | MDF | Mitteldichte Faserplatte |
| HDF | HDF | Hochdichte Faserplatte |
| Acryl / PMMA | Acrylic / PMMA | — |
| HPL | HPL | High Pressure Laminate |
| Renshape | Renshape | Modellbau-Material |

## Begriffs-Konsistenz

Damit das Wiki, der Code, die UI und das MCP konsistent bleiben:

- **Im UI immer das deutsche Wort verwenden** (außer Markennamen wie GRBL).
- **Code-Identifier dürfen englisch sein** (klassische Konvention), z.B. `feed_rate`, `stepdown`.
- **MCP-Tool-Namen auf Deutsch** wie in [Spezifikation](../SPECIFICATION.md) (Beispiel: `operation_tasche`, nicht `operation_pocket`).
- **Translation-Keys auf Deutsch** (`t('operation.tasche.titel')`).
