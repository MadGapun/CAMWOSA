# CAMWOSA — Funktionale Spezifikation

> Stand: 15.05.2026 · Status: Konzept

Dieses Dokument beschreibt was CAMWOSA können soll. Es ist die Grundlage für alle weiteren Issues und die Roadmap. Lebendiges Dokument — wird weiter ausgearbeitet.

## Inhalt

1. [Leitprinzipien](#leitprinzipien)
2. [Maschinen-Setup](#1-maschinen-setup)
3. [Werkzeug-Verwaltung](#2-werkzeug-verwaltung)
4. [Bearbeitungsoperationen](#3-bearbeitungsoperationen)
5. [Material-Datenbank](#4-material-datenbank)
6. [Feeds & Speeds Rechner](#5-feeds--speeds-rechner)
7. [Rohmaterial-Definition](#6-rohmaterial-definition)
8. [Simulation & Visualisierung](#7-simulation--visualisierung)
9. [Claude-Integration (MCP)](#8-claude-integration-mcp)
10. [Architektur](#9-architektur)
11. [Workflow von der Zeichnung zum G-Code](#10-workflow-von-der-zeichnung-zum-g-code)

---

## Leitprinzipien

**Sicherheit vor Bequemlichkeit.** Jeder Toolpath ist visualisiert und prüfbar bevor er die Maschine erreicht. Lieber eine Frage zu viel als ein Crash.

**Maker statt Konzern.** CAMWOSA ist für 2.5D-Arbeit auf Hobby- und Semi-Pro-Maschinen optimiert. Keine 5-Achs-Komplexität, kein Engineering-Overhead.

**Claude als Sparringspartner.** Jede Funktion ist auch über Sprache/Chat zugänglich. Du kannst eine Operation per Klick anlegen ODER Claude bitten sie zu erzeugen — beide Wege funktionieren.

**Lokal & datenschutzfreundlich.** Wie PBP: läuft auf deinem Rechner, deine Daten bleiben bei dir, keine Cloud-Abhängigkeit.

**Wenig Klicks, gute Defaults.** Wenn du nichts änderst, kommt ein vernünftiges Ergebnis raus. Profis können trotzdem alles anpassen.

---

## 1. Maschinen-Setup

Eine CAM-Software muss wissen welche Maschine den G-Code ausführt. Falsche Annahmen → Crash oder Ausschuss.

### Maschinen-Profil enthält

| Parameter | Beispiel ProVerXL 4030 V2 |
|---|---|
| Name & Hersteller | Genmitsu ProVerXL 4030 V2 |
| Controller-Typ | GRBL 1.1 |
| Arbeitsraum (X × Y × Z) | 400 × 400 × 110 mm |
| Max. Vorschub | 3.000 mm/min |
| Sicherer Vorschub | 2.000 mm/min |
| Eilgang (G0) | 5.000 mm/min |
| Spindel-Typ | Makita RT0700 (manuell) oder Spindel (PWM) |
| Spindel-RPM-Range | 10.000 – 30.000 |
| Achsen-Konfiguration | XYZ (Rotary optional via DeskProto) |
| Tischtyp | T-Nutenplatte / Wachstisch |
| Nullpunkt-Konvention | Material Top oder Tisch Top |
| Sicherheitshöhe (Clearance) | 5 mm über Werkstückoberkante |
| Werkzeugwechsel-Position | Park-Position (X/Y/Z) |
| Post-Prozessor | GRBL Standard / Genmitsu / LinuxCNC |

### Anforderungen

- Mehrere Maschinen-Profile parallel speichern (für Bekannte / spätere Erweiterung)
- Profil aktiv setzen — alle Operationen folgen den Limits des aktiven Profils
- Warnung wenn Toolpath Arbeitsraum verlässt
- Import/Export von Profilen als JSON (Community-Sharing)

### Voreingestellte Profile (mitgeliefert)

- Genmitsu ProVerXL 4030 V2 (Markus' Maschine — primäres Testgerät)
- Genmitsu PROVer 3018
- Shapeoko Standard
- OpenBuilds LEAD CNC
- Generic GRBL 3-Achs Router

---

## 2. Werkzeug-Verwaltung

Das Werkzeug bestimmt 80% der Schnittparameter. Eine gute Bibliothek ist Pflicht.

### Werkzeug-Typen

| Typ | Verwendung | Besonderheit |
|---|---|---|
| **Schaftfräser (Flat End Mill)** | Allgemeines Fräsen, flache Böden | Standardwerkzeug |
| **Kugelfräser (Ball End Mill)** | 3D-Konturen, Reliefs | Halbkugel-Spitze |
| **Torus-/Eckenfräser (Bull Nose)** | Schruppen mit Eckenradius | Lange Standzeit |
| **V-Bit (V-Carving Bit)** | Gravuren mit variabler Tiefe | Winkel: 30°, 60°, 90° |
| **Gravierstichel** | Feine Linien, PCB | Sehr klein |
| **Bohrer** | Bohrlöcher | Reine Z-Bewegung |
| **Einschneider** | Aluminium, Kunststoff | 1 Schneide für Spanabfuhr |
| **Fischschwanz (Fishtail)** | Saubere Konturen | Senkrecht eintauchend |
| **Schrupp-/Maisfräser** | Hoher Spanabtrag | Geriffelte Schneide |
| **Diamantgravierer** | Feine Gravur in harten Materialien | Schleif-Werkzeug |

### Eigenschaften pro Werkzeug

```
Werkzeug:
  ID: T01
  Name: "1/4 Schaftfräser 2-Schneider Hartmetall"
  Typ: SchaftFraeser
  Material: Hartmetall (Carbide) | HSS | Diamant
  Beschichtung: keine | TiN | TiAlN | DLC
  Geometrie:
    Durchmesser: 6.35 mm
    Schaft-Durchmesser: 6.35 mm
    Schneidlaenge: 22 mm
    Gesamtlaenge: 76 mm
    Anzahl Schneiden (Flutes): 2
    Spitzenwinkel: -  (nur V-Bit)
    Spitzenradius: -  (nur Ball/Bull-Nose)
  Drehrichtung: rechts (CW)
  Steigung: Upcut | Downcut | Compression
  Empfohlene Anwendung: Holz, Acryl, Aluminium (leicht)
  Notizen: "Mein Lieblings-Standardfräser fuer Buche"
  Bild: optional (eigenes Foto oder Hersteller-Bild)
```

### Funktionen

- **Werkzeug anlegen** — manuell oder via Hersteller-Import (Sorotec, Sienci, Carbide3D, …)
- **Werkzeug bearbeiten / loeschen / duplizieren**
- **Werkzeug-Gruppen** — z.B. "Holz-Werkzeuge", "Aluminium-Werkzeuge"
- **Schnittparameter pro Werkzeug speichern** — beste Erfahrungswerte für Material X
- **Standzeit-Tracking** (optional, später) — wie viele Minuten Schnittzeit pro Werkzeug
- **Import/Export** als JSON (zwischen Maschinen austauschbar, Community)

### Werkzeug-Voreinstellungen pro Material

Für jedes Werkzeug können mehrere Material-Presets gespeichert werden:

| Material | RPM | Vorschub | Plunge | Stepdown | Stepover |
|---|---|---|---|---|---|
| Buche | 18.000 | 2.000 mm/min | 400 mm/min | 2 mm | 40% |
| MDF | 20.000 | 2.500 mm/min | 500 mm/min | 3 mm | 45% |
| Acryl | 16.000 | 1.500 mm/min | 300 mm/min | 1.5 mm | 35% |
| Aluminium 6061 | 14.000 | 800 mm/min | 150 mm/min | 0.3 mm | 25% |

---

## 3. Bearbeitungsoperationen

Die Grundoperationen einer 2.5D-CAM. Jede erzeugt einen Toolpath aus Geometrie + Werkzeug + Parametern.

### 3.1 Kontur (Profile / Contour)

Fraest entlang einer Kurve.

**Optionen:**
- Innen / Aussen / Auf der Linie (Werkzeug-Kompensation)
- Anzahl Tiefen-Durchgänge (Stepdown)
- Eintauchstrategie: senkrecht / Rampe / Helix
- Werkzeug-Lift zwischen Konturen
- **Tabs (Haltestege)** — verhindert dass Teile vor Ende ausbrechen
- Aufmass (Finish-Allowance) für späteren Schlichtgang
- Schlichtgang am Ende (Spring Pass)
- Fräsrichtung: Gleichlauf (Climb) / Gegenlauf (Conventional)
- Werkzeug-Eingriff: Lead-In / Lead-Out (gerade, Bogen, Tangential)

### 3.2 Tasche (Pocket)

Räumt eine geschlossene Fläche aus.

**Strategien:**
- **Parallel (Zickzack / Raster)** — schnell, gleichmäßig
- **Spiral nach außen** — gut für runde Taschen
- **Spiral nach innen** — gut für rechteckige Taschen
- **Offset-Kontur** — folgt der Außenform schichtweise
- **Adaptive Clearing** (trochoidal) — konstanter Werkzeug-Eingriff, hohe Spanabnahme

**Optionen:**
- Stepdown (Tiefe pro Durchgang)
- Stepover (seitliche Zustellung in %)
- Schlichtgang an Wand / Boden
- Aufmass Wand und Boden separat
- Inseln (Aussparungen innerhalb der Tasche)
- Rest-Material aus vorherigem Werkzeug berücksichtigen

### 3.3 Bohren (Drilling)

Z-Bewegungen an definierten Punkten.

**Strategien:**
- **Standard** — direkt nach unten und hoch
- **Peck Drilling (Spanbrechen)** — schrittweise mit Rückzug
- **Tief-Peck** — Rückzug auf Sicherheitshöhe (Spanabfuhr)
- **Helix-Bohren** — Fräser fährt schraubig nach unten (auch für Löcher größer als Fräser)
- **Reib-Zyklus** — Kontur-Bohren mit Werkzeug-Durchmesser kleiner als Loch

**Eingaben:**
- Liste von Punkten (X/Y aus DXF-Kreismitten ableitbar)
- Tiefe (durchgehend oder definiert)
- Pause am Bohrgrund (Dwell) — für saubere Lochböden
- Spitzenwinkel-Berücksichtigung (echte Bohrtiefe vs. effektive)

### 3.4 Gravieren (Engrave)

Folgt einer Kurve mit definierter Tiefe.

**Optionen:**
- Auf der Linie (zentriert)
- Konstante Tiefe
- **V-Carving** — variable Tiefe durch V-Bit-Geometrie (Schrift mit Strichstärke)
- Mehrere Tiefen-Durchgänge
- Schlichtgang

### 3.5 Räumen / Schruppen (Roughing)

Material grob abtragen, Schlichten kommt später mit anderem Werkzeug.

**Optionen:**
- Höhere Vorschübe und Stepdown
- Aufmass das nach dem Schruppen noch übrig bleibt
- Vermeidung scharfer Ecken (für Schlichten reserviert)

### 3.6 Schlichten (Finishing)

Letzter Durchgang für saubere Oberfläche.

**Optionen:**
- Geringe Zustellung
- Glatte Bewegungen
- Höhere Spindeldrehzahl
- Spring Pass (Pass ohne Zustellung — Werkzeug-Flex ausgleichen)

### 3.7 2.5D-Relief (Phase 2)

Fraest eine STL-Geometrie schichtweise oder als Höhenfeld ab.

**Strategien:**
- Raster (Zeilen in X oder Y)
- Konturparallel
- 3D-Offset
- Heatmap-Vorschau der Tiefen

### 3.8 Spezielle Operationen (später)

- **Bohrbild aus DXF-Kreisen** — alle Kreise eines Layers als Bohrungen erkennen
- **T-Nuten / Hinterschnitt** mit T-Nutenfräser
- **Schwalbenschwanz** für Verbindungen
- **Fasen anlegen** mit V-Bit oder Fasen-Fräser
- **PCB-Isolationsfräsen** (langfristig, falls Bedarf)

---

## 4. Material-Datenbank

Pro Material sind Schnittwerte hinterlegt. Basis für den Feeds & Speeds Rechner.

### Material-Eigenschaften

```
Material:
  Name: "Buche massiv"
  Kategorie: Holz | Holzwerkstoff | Kunststoff | NE-Metall | Metall | Sonstiges
  Unter-Kategorie: Hartholz
  Janka-Haerte: 1300 (fuer Holz)
  Dichte: 0.72 g/cm3
  Zugfestigkeit: -
  Schnittgeschwindigkeit (Vc): 300-600 m/min (fuer Hartmetall)
  Empfohlene Zahnvorschuebe (fz) je Werkzeug-Durchmesser
  Empfohlene Spindeldrehzahl-Range
  Empfohlener Werkzeugtyp: Upcut Schaftfraeser, Hartmetall
  Risiken / Hinweise: "Brennt bei zu langsamem Vorschub, Maserung beachten"
  Spaeneabsaugung: empfohlen
  Klimaanlage: nein
```

### Vorgehaltene Material-Familien (Start)

**Hölzer (nach Janka-Härte sortiert)**
- Weichhölzer: Kiefer, Fichte, Tanne, Pappel, Lärche
- Mittel: Buche, Birke, Kirsche, Walnuss, Eiche
- Harthölzer: Esche, Robinie, Hickory, Ebenholz

**Holzwerkstoffe**
- MDF (verschiedene Dichten)
- Spanplatte (roh / beschichtet)
- Sperrholz / Multiplex
- OSB
- HDF
- Kork

**Kunststoffe**
- Acryl (PMMA)
- POM (Delrin)
- HDPE / PE
- PVC (Hart / Schaum)
- ABS
- PC (Polycarbonat)
- Nylon (PA6)
- GFK / CFK (mit Warnung: Atemschutz!)

**NE-Metalle**
- Aluminium: 6061, 7075, AlMg3, AlCuMg
- Messing: CuZn37 (klassisch)
- Kupfer (rein)
- Bronze

**Stähle** (eher unrealistisch auf ProVerXL — als Warnung verfügbar)
- Baustahl S235
- Werkzeugstahl
- Edelstahl 1.4301

**Sonstiges**
- Wachs (für Gussmodelle)
- Carbon-Platten (mit Atemschutz-Warnung)
- Schichtstoff (HPL)
- Renshape / Modellbauschaum

### Import / Export

- Material als JSON exportierbar
- Community-Materialien importieren (z.B. exotische Hölzer von anderen CAMWOSA-Nutzern)
- "Janka-Hardness Importer" — automatische Anlage aus Wikipedia-Daten

---

## 5. Feeds & Speeds Rechner

Berechnet aus Material + Werkzeug + Maschine die optimalen Schnittparameter.

### Grundformeln

```
Schnittgeschwindigkeit (Vc) in m/min:
  Vc = (π × D × n) / 1000
  wobei D = Werkzeugdurchmesser in mm, n = Spindeldrehzahl in RPM

Vorschub (Vf) in mm/min:
  Vf = fz × z × n
  wobei fz = Zahnvorschub (mm/Zahn), z = Anzahl Schneiden, n = RPM

Spanvolumen (Q) in cm³/min:
  Q = (ap × ae × Vf) / 1000
  wobei ap = Schnitttiefe, ae = seitliche Zustellung
```

### Eingaben

- Material (aus DB)
- Werkzeug (aus DB)
- Maschine (aus DB)
- Operation (Schruppen / Schlichten / Bohren / Gravieren)
- Gewünschte Spindel-RPM (oder "auto")

### Ausgaben

- Empfohlener Vorschub (mm/min)
- Empfohlener Eintauchvorschub (Plunge) (mm/min)
- Maximale Schnitttiefe pro Durchgang (ap)
- Seitliche Zustellung (ae) in % vom Durchmesser
- Berechneter Spanquerschnitt
- **Warnungen:**
  - Werkzeug zu klein für Vorschub (Bruchgefahr)
  - Werkzeug rubbelt (Burning Wood)
  - Maschinen-Vorschub übersteigt Limit
  - Material-Werkzeug-Kombination nicht empfohlen

### Lernende Anpassung (später)

- Nutzer markiert "war zu langsam" / "war zu schnell" → Preset wird angepasst
- Erfahrungswerte werden pro Werkzeug+Material gespeichert
- Optional: Anonyme Telemetrie-Sharing für Community-Daten

---

## 6. Rohmaterial-Definition

Das CAM-System muss wissen wo das Material anfängt und aufhört, sonst kann es keinen Toolpath generieren.

### Material-Geometrie

**Standardformen — direkt eingebbar:**
- **Quader** — Länge × Breite × Höhe
- **Zylinder / Rund** — Durchmesser × Höhe
- **Plattenmaterial** — Länge × Breite (Höhe = Materialstärke)
- **Frei (vom Modell abgeleitet)** — Bounding Box + Aufmass

**Import:**
- STL als Rohmaterial-Modell (z.B. unregelmaessiges Restholz)
- DXF-Konturen für unregelmaessige flache Formen

**Eigenes Zeichnen:**
- Rechteck mit Maßen
- Kreis mit Durchmesser
- Polygon
- Spline / Frei

### Positionierung

- **Nullpunkt setzen** — Klick auf Ecke / Mitte / beliebige Stelle
- **Ausrichtung** — Modell vs. Material rotieren
- **Z-Nullpunkt** — Oberseite Material / Unterseite / Tisch
- Versatz X/Y/Z zum Material-Ursprung

### Material-Slot (Halterung)

Optional — wo sind Klemmen, Schraubzwingen, Schraubstock?

- Klemmen-Positionen einzeichnen → Toolpath weicht aus
- Tab-Höhe automatisch über Klemmen
- Spannmittel-Bibliothek (Standard-Niederhalter, Schraubstock)

---

## 7. Simulation & Visualisierung

Das Herzstück gegen Crashes und Ausschuss.

### 7.1 2D-Vorschau (Phase 1)

- **Top-Down-Ansicht** (von oben)
- Rohmaterial als Rahmen
- DXF-Konturen
- Toolpath als farbige Linien (verschiedene Operationen unterschiedliche Farben)
- Eintauchpunkte als Marker
- Eilbewegungen gestrichelt
- Werkzeug-Nullpunkt klar markiert
- Werkzeug-Radius als Overlay
- Zoom + Pan + Messen

### 7.2 Tiefen-Vorschau

- **Seitenansicht** mit Z-Verlauf
- Mehrere Tiefen-Durchgänge als Linien gestapelt
- Sicherheitshöhe sichtbar

### 7.3 3D-Materialabtrag-Simulation (Phase 2)

**Das wichtigste Feature für deine Anforderung:**

- Rohmaterial wird als 3D-Block dargestellt
- Werkzeug bewegt sich entlang Toolpath
- Material wird "abgetragen" — visueller Abtrag in Echtzeit
- Geschwindigkeit einstellbar (Zeitlupe → Schnellvorlauf)
- Pause / Step-Forward / Springen
- **Mit oder ohne Toolpath-Linien** — auf Wunsch zu/abschaltbar
- **Endergebnis** vergleichbar mit Soll-Modell (Differenz-Anzeige)

**Technologische Optionen:**
- WebGL-basiert (Three.js) — läuft im Browser
- Mesh-basierter Materialabtrag (Boolean Subtraction)
- Alternativ: Voxel-basiert (einfacher, weniger genau, aber schneller)

### 7.4 Werkzeug-Visualisierung

- Aktuelles Werkzeug 3D dargestellt (mit korrektem Durchmesser/Länge)
- Spindel und Halter optional
- Kollisionswarnung wenn Halter ins Material taucht

### 7.5 Statistiken pro Simulation

- Geschätzte Bearbeitungszeit
- Anzahl Werkzeugwechsel
- Gesamter Verfahrweg
- Spanvolumen
- Toolpath-Länge pro Operation

---

## 8. Claude-Integration (MCP)

Wie PBP — Claude soll als Sparringspartner und Bediener funktionieren.

### MCP-Tools (Auswahl)

```
Maschinen / Werkzeuge / Material:
  - maschine_anzeigen(profil_id)
  - werkzeug_hinzufuegen(parameter)
  - werkzeug_suchen(filter)
  - material_hinzufuegen(parameter)

Projekt:
  - projekt_erstellen(name, maschine, material)
  - dxf_importieren(pfad)
  - rohmaterial_definieren(form, masse, position)
  - nullpunkt_setzen(x, y, z)

Operationen:
  - operation_kontur(geometrie, werkzeug, parameter)
  - operation_tasche(geometrie, werkzeug, parameter)
  - operation_bohren(punkte, werkzeug, parameter)
  - operation_gravur(geometrie, werkzeug, parameter)

Berechnung & Export:
  - feeds_speeds_berechnen(material, werkzeug, operation)
  - toolpath_generieren(operation_id)
  - simulation_starten(projekt_id)
  - gcode_exportieren(pfad)

Analyse & Optimierung:
  - projekt_pruefen(projekt_id)  -- Sanity-Check (Arbeitsraum, Werkzeug, Kollision)
  - bearbeitungszeit_schaetzen(projekt_id)
  - vorschlaege_optimierung(projekt_id)
```

### Beispiel-Dialoge (was Markus sagen koennen soll)

> "Importiere die DXF von gestern und mach eine Kontur mit 6mm Tabs."
> 
> "Ich brauche eine Tasche 80x40mm, 8mm tief, in Buche, mit dem 6mm Einschneider."
> 
> "Pruef mal den Toolpath — ist der noch im Arbeitsraum?"
> 
> "Welcher Fraeser passt besser fuer Acryl?"
> 
> "Optimiere die Reihenfolge der Operationen damit weniger Werkzeugwechsel noetig sind."
> 
> "Zeig mir die Simulation in Zeitlupe ab Operation 3."

---

## 9. Architektur

### Technologie-Stack

```
Backend (Python 3.11+)
  Flask                  - REST-API
  ezdxf                  - DXF-Parser
  numpy                  - Geometrie & Matrix
  shapely                - 2D-Geometrie-Operationen (Offset, Boolean)
  numpy-stl / trimesh    - STL-Handling (Phase 2)
  pydantic               - Datenmodelle
  SQLAlchemy + SQLite    - Persistenz

Frontend (React 19 + Vite + Tailwind)
  three.js               - 3D-Visualisierung & Simulation
  konva.js (optional)    - 2D-Canvas-Vorschau
  zustand / redux        - State Management

MCP-Server (Python)
  FastMCP                - MCP-Implementation
  HTTP-Bridge zu Flask   - Tool-Aufrufe an Backend

CLI / Installer
  Cross-Platform (Win/macOS/Linux) - wie PBP
```

### Datenmodell (Kern)

```
Maschine (1) ----< (N) Projekt
Material (1) ----< (N) Projekt
Werkzeug (1) ----< (N) Operation
Projekt (1) ----< (N) Operation
Operation (1) ----< (N) Toolpath-Segment
Projekt (1) -----  (1) Rohmaterial
Projekt (1) -----  (1) DXF/STL-Import
```

### Repository-Struktur

```
CAMWOSA/
├── backend/
│   ├── camwosa/
│   │   ├── dxf/         # DXF-Parser
│   │   ├── stl/         # STL-Parser
│   │   ├── cam/         # Operationen + Toolpath
│   │   ├── gcode/       # G-Code Generator
│   │   ├── feeds/       # Feeds & Speeds
│   │   ├── db/          # SQLAlchemy-Modelle
│   │   └── api/         # Flask Routes
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── viewer2d/
│   │   ├── viewer3d/
│   │   ├── operations/
│   │   └── settings/
│   └── public/
├── mcp_server/
│   └── server.py
├── installer/
├── docs/
└── data/
    ├── machines/        # Vorgefertigte Maschinen-Profile
    ├── tools/           # Werkzeug-Bibliothek (Defaults)
    └── materials/       # Material-DB (Defaults)
```

---

## 10. Workflow von der Zeichnung zum G-Code

Der typische Ablauf in CAMWOSA:

```
1. Projekt anlegen
   └─> Maschine wählen (z.B. ProVerXL 4030 V2)

2. Rohmaterial definieren
   ├─> Form (Quader, Zylinder, Platte, frei)
   ├─> Maße eingeben
   └─> Material auswählen (z.B. Buche)

3. Geometrie laden
   ├─> DXF importieren (aus Solid Edge)
   ├─> ODER: STL importieren (für Relief)
   └─> ODER: Direkt in CAMWOSA zeichnen (einfache Formen)

4. Nullpunkt setzen
   ├─> Auf Geometrie (z.B. Mittelpunkt)
   └─> Rotation/Spiegelung falls noetig

5. Operationen anlegen
   ├─> Kontur, Tasche, Bohren, Gravur, Relief
   ├─> Werkzeug wählen (aus Bibliothek)
   ├─> Feeds & Speeds: auto oder manuell
   └─> Reihenfolge festlegen

6. Toolpaths generieren
   └─> Sofort visueller Preview

7. Simulation
   ├─> 2D-Preview pruefen
   ├─> 3D-Simulation mit Materialabtrag
   └─> Statistiken pruefen (Zeit, Verfahrweg)

8. G-Code exportieren
   ├─> Post-Prozessor wählen (GRBL Standard)
   ├─> Datei speichern (.nc oder .gcode)
   └─> Optional: Direkt in CNCjs öffnen
```

---

## Open Questions

Diese Fragen sind noch nicht entschieden — werden im Lauf des Projekts geklärt:

1. **Browser-UI oder Desktop-App (Electron)?** — Browser ist leichter, Electron erlaubt mehr OS-Integration.
2. **Eigenes Zeichnen mit aufnehmen oder nur Import?** — Markus zeichnet in Solid Edge. Eingebaute Zeichnung später, oder vorerst nur Import?
3. **Wie tief soll die 3D-Simulation gehen?** — Reicht eine optische Simulation oder soll sie auch Kollisions-Warnungen liefern?
4. **Mehrere Sprachen?** — Erstmal nur Deutsch wie PBP, oder direkt EN/DE?
5. **Eigener G-Code-Editor integriert?** — Oder nur Export und externes Tool nutzen?
6. **Wird CNCjs direkt angesprochen?** — Direkter Job-Send wäre möglich, ist aber riskant.

---

> Letztes Update: 15.05.2026
> Autor: Markus Birzite & Claude
> An <b>ELWOSA</b> Project
