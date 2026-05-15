# CAMWOSA — Funktionale Spezifikation

> Stand: 15.05.2026 · Status: Konzept (Architektur entschieden, Workflow-Modul ergänzt)

Dieses Dokument beschreibt was CAMWOSA können soll. Es ist die Grundlage für alle weiteren Issues und die Roadmap. Lebendiges Dokument — wird weiter ausgearbeitet.

## Inhalt

1. [Leitprinzipien](#leitprinzipien)
2. [Architektur-Entscheidungen](#architektur-entscheidungen)
3. [Maschinen-Setup](#1-maschinen-setup)
4. [Werkzeug-Verwaltung](#2-werkzeug-verwaltung)
5. [Bearbeitungsoperationen](#3-bearbeitungsoperationen)
6. [Material-Datenbank](#4-material-datenbank)
7. [Feeds & Speeds Rechner](#5-feeds--speeds-rechner)
8. [Rohmaterial-Definition](#6-rohmaterial-definition)
9. [Integriertes Zeichnen](#7-integriertes-zeichnen)
10. [Workflow-Modul (Multi-Setup)](#8-workflow-modul-multi-setup)
11. [Verschnittoptimierung (Nesting)](#9-verschnittoptimierung-nesting)
12. [Simulation & Visualisierung](#10-simulation--visualisierung)
13. [G-Code Editor](#11-g-code-editor)
14. [Projekt-Management](#12-projekt-management)
15. [Plugin-System für CNC-Steuerungen](#13-plugin-system-für-cnc-steuerungen)
16. [Claude-Integration (MCP)](#14-claude-integration-mcp)
17. [Architektur](#15-architektur)
18. [Workflow von der Zeichnung zum G-Code](#16-workflow-von-der-zeichnung-zum-g-code)

---

## Leitprinzipien

**Pure CAM — keine Maschinen-Steuerung.** CAMWOSA erzeugt G-Code, prüft ihn und speichert ihn. Die tatsächliche Ausführung auf der Maschine ist Sache von CNCjs (oder welcher Steuerungs-Software du nutzt). Keine Jog-Steuerung, kein direkter Job-Send, kein Audio-Feedback während der Bearbeitung. Diese Grenze ist bewusst gezogen.

**MCP-First-Prinzip: UI vollwertig, MCP optional.** Die UI ist komplett stand-alone bedienbar — ohne Claude funktioniert alles. Das MCP ist eine **zweite Bedienoberfläche** für die gleiche Backend-API: jede Funktion ist sowohl per Klick als auch per Chat ansprechbar. Wenn Claude eine komplette CAM-Bearbeitung erstellt, sind die einzelnen Schritte ganz normale Operationen in der Liste — du siehst, editierst und ergänzt sie wie selbst angelegt.

**Sicherheit vor Bequemlichkeit.** Jeder Toolpath ist visualisiert und prüfbar bevor er die Maschine erreicht. Lieber eine Frage zu viel als ein Crash.

**Maker statt Konzern.** CAMWOSA ist für 2.5D-Arbeit auf Hobby- und Semi-Pro-Maschinen optimiert. Keine 5-Achs-Komplexität, kein Engineering-Overhead.

**Lokal & datenschutzfreundlich.** Wie PBP: läuft auf deinem Rechner, deine Daten bleiben bei dir, keine Cloud-Abhängigkeit.

**Wenig Klicks, gute Defaults.** Wenn du nichts änderst, kommt ein vernünftiges Ergebnis raus. Profis können trotzdem alles anpassen.

**Offene Architektur.** GRBL ist der erste Fokus — aber das System ist so gebaut, dass weitere Controller (Marlin, LinuxCNC, Mach3, …) als Plugin nachrüstbar sind.

---

## Architektur-Entscheidungen

Die Grundentscheidungen die alle weiteren Themen prägen:

| Entscheidung | Begründung |
|---|---|
| **Pure CAM, keine Steuerung** | G-Code erzeugen und speichern. CNCjs übernimmt die Ausführung |
| **MCP-First-Prinzip** | UI komplett bedienbar ohne Claude. MCP ist zweite Bedienoberfläche zur gleichen Backend-API |
| **Desktop-App (Electron)** | Native Datei-Integration, Drag&Drop, OS-Tray. Browser-UI später möglich (gleiches Backend) |
| **Integriertes Zeichnen** | LightBurn-inspiriert — schnelle Formen direkt erzeugen, kein Tool-Wechsel |
| **Workflow-Modul** | Multi-Setup-Jobs mit Pausen für Umspannen/Werkzeugwechsel + druckbare Checklisten |
| **Verschnittoptimierung** | Nesting für mehrere Teile auf einer Platte — Standard-Feature, nicht "später" |
| **Werkzeugwechsel** | Bestätigung durch Nutzer (kein automatisches Durchlaufen) |
| **Simulation: stufenweise** | Phase 1: 2D + Sicherheits-Checks. Phase 2: 3D-Materialabtrag. Phase 3: Kollisionsanalyse |
| **Sprachen: DE-zuerst, dann EN** | Entwicklung auf Deutsch (präziser), Übersetzung danach. i18n-fähig von Anfang an |
| **G-Code Editor: vollintegriert** | Editor + Befehlsbibliothek + zeilenweise Simulation + Such-/Ersetzen-Funktionen |
| **G-Code speichern, kein Job-Send** | Save-As genügt — CNCjs übernimmt das Ausführen |
| **Plugin-System für Controller** | GRBL zuerst, andere Controller erweiterbar (Endnutzer-fähig) |

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
| Achsen-Konfiguration | XYZ (Rotary-Modus separat siehe ROTARY.md) |
| Tischtyp | T-Nutenplatte / Wachstisch |
| Nullpunkt-Konvention | Material Top oder Tisch Top |
| Sicherheitshöhe (Clearance) | 5 mm über Werkstückoberkante |
| Werkzeugwechsel-Position | Park-Position (X/Y/Z) |
| Post-Prozessor | GRBL Standard / Genmitsu / LinuxCNC |

### Anforderungen

- Mehrere Maschinen-Profile parallel speichern
- Profil aktiv setzen — alle Operationen folgen den Limits des aktiven Profils
- Warnung wenn Toolpath Arbeitsraum verlässt
- Import/Export von Profilen als JSON (Community-Sharing)

### Voreingestellte Profile (mitgeliefert)

- Genmitsu ProVerXL 4030 V2 (primäres Testgerät)
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

### 3.6 Schlichten (Finishing)

Letzter Durchgang für saubere Oberfläche.

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
  Schnittgeschwindigkeit (Vc): 300-600 m/min
  Empfohlene Zahnvorschuebe (fz) je Werkzeug-Durchmesser
  Empfohlene Spindeldrehzahl-Range
  Empfohlener Werkzeugtyp
  Risiken / Hinweise
  Spaeneabsaugung: empfohlen
```

### Vorgehaltene Material-Familien (Start)

**Hölzer (nach Janka-Härte sortiert)**
- Weichhölzer: Kiefer, Fichte, Tanne, Pappel, Lärche
- Mittel: Buche, Birke, Kirsche, Walnuss, Eiche
- Harthölzer: Esche, Robinie, Hickory, Ebenholz

**Holzwerkstoffe**
- MDF, Spanplatte, Sperrholz/Multiplex, OSB, HDF, Kork

**Kunststoffe**
- Acryl (PMMA), POM, HDPE/PE, PVC, ABS, PC, Nylon, GFK/CFK

**NE-Metalle**
- Aluminium (6061, 7075, AlMg3), Messing CuZn37, Kupfer, Bronze

**Stähle** (eher unrealistisch auf ProVerXL — als Warnung verfügbar)

**Sonstiges**
- Wachs, Carbon, HPL, Renshape

### Import / Export

- Material als JSON exportierbar
- Community-Materialien importieren

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

### Positionierung

- **Nullpunkt setzen** — Klick auf Ecke / Mitte / beliebige Stelle
- **Ausrichtung** — Modell vs. Material rotieren
- **Z-Nullpunkt** — Oberseite Material / Unterseite / Tisch
- Versatz X/Y/Z zum Material-Ursprung

### Material-Slot (Halterung)

Optional — wo sind Klemmen, Schraubzwingen, Schraubstock?

- Klemmen-Positionen einzeichnen → Toolpath weicht aus
- Tab-Höhe automatisch über Klemmen

---

## 7. Integriertes Zeichnen

CAMWOSA bringt einen **eingebauten 2D-Zeichner** mit — LightBurn-inspiriert, für schnelle Formen ohne den Umweg über ein externes CAD-Tool.

### Warum integriert?

Solid Edge ist für komplexe Bauteile super, aber für eine schnelle Tasche, eine Beschriftung oder einen einfachen Ausschnitt ist der Toolwechsel zu langsam.

### Zeichnen-Funktionen (Phase 1)

**Primitive:**
- Linie (zwei Punkte, oder Punkt + Winkel + Länge)
- Rechteck (Eckpunkte oder Mitte + Maße, mit/ohne abgerundete Ecken)
- Kreis (Mittelpunkt + Radius/Durchmesser)
- Ellipse
- Polygon (Anzahl Ecken, Mittelpunkt, Größe — innen/außen)
- Polylinie / Freihand
- Spline / Bezier-Kurve
- Bogen (drei Punkte, oder Mitte/Radius/Winkel)
- Text (mit Font-Auswahl — für Gravuren und Beschriftungen)

**Operationen auf Objekten:**
- Verschieben, Drehen, Skalieren, Spiegeln
- Vervielfältigen (lineares Array, Polar-Array, Raster)
- Verbinden / Trennen
- Offset (Parallel-Kurve in Abstand X)
- Boolean: Vereinigung, Differenz, Schnitt
- Trimmen / Verlängern
- Fillet (Verrundung) / Chamfer (Fase)

**Hilfsmittel:**
- Snap to Grid / Snap to Object (Endpunkt, Mittelpunkt, Schnittpunkt, Tangent)
- Bemaßungen (nur zur Information beim Zeichnen, nicht im G-Code)
- Layer / Ebenen
- Maßstab + Einheiten (mm)
- Bezugspunkt (Origin) verschieben

### Verbindung Zeichnen → CAM

- Jedes Zeichnungsobjekt kann **direkt einer Operation zugewiesen** werden — Rechtsklick → "als Tasche fräsen"
- Layer können Operationen zugeordnet werden
- Import von DXF (aus Solid Edge) wird automatisch ins Zeichnen-Modul übernommen und kann dort weiterbearbeitet werden

### Was NICHT eingebaut wird

- 3D-Modellierung (dafür gibt es Solid Edge / Blender)
- Komplexe Bemaßungstools für technische Zeichnungen
- Parametrische Constraints
- DWG-Editor

---

## 8. Workflow-Modul (Multi-Setup)

Echte CNC-Werkstuecke brauchen oft **mehrere Aufspannungen**: 2D-Rohling fraesen, dann umspannen auf Rotary, dann nochmal werkzeugwechseln. CAMWOSA unterstuetzt das nativ.

### 8.1 Setup-Konzept

Ein Projekt besteht aus einer Folge von **Setups**. Jedes Setup ist ein in sich abgeschlossener Job mit eigenem G-Code-File:

```
Projekt: "Lotus-Schale Variante 3"
├── Setup 1: Rohling 2D vorbereiten
├── 🔧 SETUP-PAUSE — Umspannen auf Rotary
├── Setup 2: Rotary-Schruppen
├── 🔧 SETUP-PAUSE — Werkzeug wechseln
└── Setup 3: Rotary-Schlichten
```

Pro Setup wird **eine separate G-Code-Datei** generiert. Das ist sauberer als ein langer File mit M0-Pausen — und die Maschinen-Steuerung (CNCjs) laedt einfach das naechste File wenn du soweit bist.

### 8.2 Setup-Eigenschaften

Pro Setup wird festgehalten:

| Aspekt | Beschreibung |
|---|---|
| Maschinen-Modus | 3-Achs / Rotary |
| Spannmittel | Schraubzwingen, Schraubstock, Backen, Reitstock |
| Werkstueck-Position | Wie eingespannt (Foto-Slot fuer Vergleich) |
| Nullpunkt | X/Y/Z neu setzen oder uebernehmen aus vorherigem Setup |
| Werkzeug | Aktives Werkzeug (kann mehrfach zwischen Setups gewechselt werden) |
| Operationen | Welche Bearbeitungen in diesem Setup |
| Geschaetzte Zeit | Pro Setup |

### 8.3 Setup-Pausen

Zwischen zwei Setups gibt es eine **Pause** mit klaren Aktions-Anweisungen:

**Werkzeugwechsel-Pause:**
- Welches Werkzeug wechseln (von T1 auf T2)
- Z-Hoehe neu setzen
- **Bestaetigung im UI erforderlich:** "Werkzeug T2 eingewechselt? [Ja]"

**Umspann-Pause:**
- Werkstueck wie umspannen (mit Foto-Anleitung)
- Maschinen-Modus umstellen (z.B. ROTARY EIN in CNCjs)
- Nullpunkt neu setzen — X/Y/Z je nach Bedarf
- Bestaetigung im UI

**Optionale Stop-Pause:**
- Zwischen-Inspektion ("Tiefe pruefen, dann Continue")
- Schleifen/Reinigen vor dem naechsten Schritt

### 8.4 Foto-Dokumentation

Pro Setup ein optionaler Foto-Slot:
- Beim ersten Lauf machst du ein Foto vom Setup
- Beim Wiederholungs-Lauf hast du Vergleichsbild
- Hilft besonders bei Jobs ueber mehrere Tage

### 8.5 Arbeitsplan / Checkliste

CAMWOSA generiert aus dem Projekt einen **druckbaren Arbeitsplan**:

```
─────────────────────────────────────────
CAMWOSA Arbeitsplan
Projekt: Lotus-Schale Variante 3
Datum: 15.05.2026 · Geschaetzt: 2h 45min

[ ] Setup 1: Rohling vorbereiten
    Maschine: 3-Achs ($101=400 pruefen)
    Spannmittel: Schraubzwingen x 4
    Material: Buche-Rundling Ø 130mm, H 30mm
    Nullpunkt: Ecke vorne links, OK
    G-Code: lotus_setup1_rohling.nc
    Werkzeug T1: 6mm Schaftfraeser
    Geschaetzte Zeit: 25min

[ ] Setup-Pause: Umspannen auf Rotary
    Rotary-Achse einbauen
    CNCjs: Macro "ROTARY EIN" ausfuehren
    Werkstueck: zwischen Backen + Reitstock
    Nullpunkt neu: X=0 Backen-Mitte, Z=0 Achse

[ ] Setup 2: Rotary-Schruppen
    Maschine: Rotary-Modus ($101=88.889 pruefen)
    G-Code: lotus_setup2_schruppen.nc
    Werkzeug T1: 6mm Schaftfraeser (unveraendert)
    Geschaetzte Zeit: 45min

[ ] Setup-Pause: Werkzeug wechseln auf T2
    Werkzeug T2: 3mm Kugelfraeser
    Z-Hoehe neu setzen mit Z-Probe

[ ] Setup 3: Rotary-Schlichten
    G-Code: lotus_setup3_finish.nc
    Geschaetzte Zeit: 95min

[ ] Fertig
─────────────────────────────────────────
```

**Zwei Darstellungsformen:**
- **PDF zum Ausdrucken** — Liste neben CNC liegen lassen, mit Stift abhaken
- **Im UI als Checkliste** — klickbar abhakbar, Status synchronisiert mit Projekt

### 8.6 Multi-Setup-Sicherheits-Checks

Beim Generieren der G-Code-Dateien wird geprueft:

- Stimmt der Maschinen-Modus zwischen Setups? (3-Achs → Rotary uebergang sichtbar)
- Wurden Nullpunkte zwischen Setups dokumentiert?
- Sind die Aktions-Anweisungen klar formuliert?
- Werkzeuge in der richtigen Reihenfolge (T1, T2, T3 statt durcheinander)?

---

## 9. Verschnittoptimierung (Nesting)

Wenn du mehrere Teile aus einer Platte fraest, ordnet CAMWOSA sie **automatisch verlustarm** an.

### 9.1 Eingaben

- Plattenmaterial: Laenge x Breite x Hoehe (Vorrat-Liste oder Eingabe)
- Teile: was wird gefertigt, in welcher Stueckzahl
- Optional: Faserrichtung pro Teil (fuer Holz)
- Optional: Sperrzonen (Spannfutter, Risse im Material)

### 9.2 Ausgaben

- **Anordnungs-Vorschlag** mit Vorschau (welches Teil wo)
- **Verschnitt-Statistik** (genutzte Flaeche / Gesamtflaeche)
- **G-Code mit allen Teilen** in einem Setup (oder verteilt auf mehrere Platten)

### 9.3 Strategie

Mehrere Algorithmen waehlbar:

- **Bin Packing** — schnell, gute Ergebnisse fuer einfache Formen
- **No-Fit-Polygon** — fuer komplexe Konturen
- **Manuell-erweiterbar** — du kannst die automatische Anordnung per Drag&Drop anpassen

### 9.4 Faserrichtungs-Beruecksichtigung (Holz)

- Pro Teil definierbar: "Faser parallel zu Y" / "egal"
- Optimierung respektiert die Vorgabe

### 9.5 Aussparungen / Sperrzonen

- Wenn das Plattenmaterial Astloch oder Riss hat: Bereich als no-go markieren
- Optimierung weicht aus

### 9.6 Beispiel-Workflow

```
1. "Ich brauche 4 Rohlinge fuer Lotus-Schalen aus Buche 600x400x18"
2. Verschnitt-Modul oeffnen
3. Teile-Vorlage: Rundscheibe Ø 130mm, 4 Stueck
4. Platte: 600x400x18 mm
5. Anordnen klicken
   → Vorschlag: alle 4 nebeneinander mit 5mm Abstand
   → Verschnitt: 38% (Rest 248x400 nutzbar)
6. Mit "G-Code generieren" wird ein Setup erzeugt
   das alle 4 Rohlinge in einem Job fraest
```

---

## 10. Simulation & Visualisierung

Das Herzstück gegen Crashes und Ausschuss. Stufenweise umgesetzt:

### 10.1 Phase 1 — 2D-Vorschau + Sicherheits-Checks

**2D-Vorschau (Top-Down):**
- Rohmaterial als Rahmen
- DXF-Konturen
- Toolpath als farbige Linien (verschiedene Operationen unterschiedliche Farben)
- Eintauchpunkte als Marker
- Eilbewegungen gestrichelt
- Werkzeug-Nullpunkt klar markiert
- Werkzeug-Radius als Overlay
- Zoom + Pan + Messen

**Tiefen-Vorschau (Seitenansicht):**
- Z-Verlauf
- Mehrere Tiefen-Durchgänge als Linien gestapelt
- Sicherheitshöhe sichtbar

**Sicherheits-Checks (automatisch beim Generieren):**
- Toolpath verlässt Arbeitsraum? → Warnung mit Markierung
- Eilbewegung (G0) unterhalb Sicherheitshöhe? → **kritische Warnung** (klassische Crash-Ursache!)
- Eilbewegung im Material? → kritische Warnung
- Werkzeug zu kurz für Schnitttiefe? → Warnung
- Plunge ohne Rampe bei nicht-Bohrer? → Hinweis

### 10.2 Phase 2 — 3D-Materialabtrag-Simulation

- Rohmaterial als 3D-Block dargestellt
- Werkzeug bewegt sich entlang Toolpath
- Material wird "abgetragen" — visueller Abtrag in Echtzeit
- Geschwindigkeit einstellbar (Zeitlupe → Schnellvorlauf)
- Pause / Step-Forward / Springen
- Toolpath-Linien zu/abschaltbar
- Endergebnis vergleichbar mit Soll-Modell (Differenz-Anzeige)

**Technologie:** Three.js, Voxel-basiert für Performance, optional Mesh-basiert für Genauigkeit.

### 10.3 Phase 3 — Kollisionsanalyse

- Werkzeughalter + Spindel als 3D-Geometrie
- Kollisionswarnung wenn Halter ins Material taucht
- Visualisierung der "no-go zones"

### 10.4 Statistiken pro Simulation

- Geschätzte Bearbeitungszeit
- Anzahl Werkzeugwechsel
- Gesamter Verfahrweg
- Spanvolumen
- Toolpath-Länge pro Operation

---

## 11. G-Code Editor

Ein **vollwertiger G-Code Editor** ist integriert — nicht nur ein passiver Viewer.

### 11.1 Basis-Funktionen

- Syntax-Highlighting (G/M-Codes farblich, Parameter, Kommentare)
- Zeilennummern
- Suchen & Ersetzen (mit Regex-Option)
- Undo / Redo
- Zeilen markieren / Blöcke verschieben
- Speichern / Speichern als
- Auto-Format (Spaltenausrichtung)
- Mehrere Tabs (verschiedene G-Code-Dateien parallel)

### 11.2 Befehlsbibliothek

Klick auf einen G-Code-Befehl → **kontextbezogene Erklärung im Seitenpanel:**

| Befehl | Was er macht |
|---|---|
| G0 X100 Y50 | Eilbewegung zu Position X=100, Y=50 (kein Materialabtrag) |
| G1 X100 Y50 F1000 | Lineare Schnittbewegung mit 1000 mm/min |
| G2 / G3 | Kreisbogen-Bewegung (im/gegen Uhrzeigersinn) |
| G17/G18/G19 | Arbeitsebene wählen (XY/XZ/YZ) |
| G20/G21 | Einheiten setzen (Zoll/mm) |
| G54-G59 | Werkstück-Koordinatensystem |
| G90/G91 | Absolute/relative Koordinaten |
| M3 Sxxx | Spindel ein (im Uhrzeigersinn) mit Drehzahl |
| M5 | Spindel aus |
| M30 | Programm-Ende |

**Plus:** Suchfunktion in der Bibliothek — "Wie heißt der Befehl für Spanbrechen?" → G73 / G83.

### 11.3 Zeilenweise Simulation

- Klick in eine Zeile → Markierung in 2D/3D-Vorschau (wo das Werkzeug grade ist)
- Toggle "Live-Sync" — automatische Aktualisierung beim Bewegen des Cursors
- **Performance-Schalter** — bei großen G-Code-Dateien Live-Sync deaktivierbar
- Schritt-für-Schritt durchgehen (wie Debugger)

### 11.4 Massen-Editor (Find & Modify)

Beispiel: "Setze alle Vorschübe von 2000 auf 1500"
- Such-Pattern: `F2000`
- Ersetzen mit: `F1500`
- Vorschau der betroffenen Zeilen vor Anwendung
- **Operations-spezifisches Editieren:** "In allen Operationen vom Typ Tasche, reduziere Plunge-Rate um 20%"

### 11.5 Strukturansicht (Code-Outline)

Linke Spalte zeigt die G-Code-Struktur:
- Header (Maschinen-Setup)
- Werkzeug T1
  - Operation: Aussenkontur
  - Operation: Tasche 1
- Werkzeug T2
  - Operation: Bohrungen
- Footer (Spindel aus, zurück zur Park-Position)

Klick auf Eintrag → Springt zur entsprechenden Stelle.

### 11.6 Backplot-Annotation

Im G-Code-Editor werden auf Wunsch Kommentare automatisch ergänzt:
```
; Operation: Aussenkontur Stepdown 1/3
G1 Z-2.0 F300
...
; Operation: Aussenkontur Stepdown 2/3
G1 Z-4.0 F300
```

So bleibt nachvollziehbar **was wann passiert** — wichtig für späteres Editing.

---

## 12. Projekt-Management

### 12.1 Projekt-Konzept

Ein **CAMWOSA-Projekt** enthält alles was zum Werkstück gehört:
- Maschinen-Wahl
- Material + Rohmaterial-Definition
- Geometrie (Zeichnung / Import)
- **Setups + Setup-Pausen** (Multi-Setup-Workflow)
- Operationen
- Werkzeug-Zuordnungen
- Generierter Toolpath
- Generierter G-Code (pro Setup eine Datei)
- Notizen / Metadaten
- Foto-Slots fuer Setup-Dokumentation

**Dateiformat:** `.cwp` (CAMWOSA Project) — ein ZIP mit JSON + eingebetteten Geometrie-Dateien.

### 12.2 Speichern

- **Speichern** — bestehende Projektdatei überschreiben
- **Speichern als …** — neue Projektdatei (für Varianten)
- **Auto-Save** — alle X Minuten in temporären Snapshot (wiederherstellbar nach Crash)

### 12.3 Varianten / Versionen

Ein Projekt kann **mehrere Varianten** enthalten — z.B.:
- "Buche, 12mm — Standardversion"
- "MDF, 18mm — billig zum Testen"
- "Acryl, 5mm — als Vorlage"

Jede Variante hat eigene Material/Maschinen/Operationen-Einstellungen. **Wechsel zwischen Varianten per Dropdown.**

### 12.4 Projekt-Historie

- Wer hat wann was geändert? (Lokales Log)
- "Revert to last G-Code generation"
- Diff zwischen zwei Varianten

### 12.5 Projekt-Export / Import

- Komplettes Projekt als ZIP exportieren (für Backup / Sharing)
- Projekt importieren (mit Konflikt-Behandlung bei fehlenden Werkzeugen/Materialien)

---

## 13. Plugin-System für CNC-Steuerungen

GRBL ist Start — das System ist aber **offen für andere Controller**.

### 13.1 Post-Prozessor-Architektur

Jeder Controller hat seinen eigenen Post-Prozessor — definiert in einer einzelnen Python-Datei oder JSON-Konfiguration:

```
postprocessor/
├── grbl_standard.py       # GRBL 1.1 Standard (Default)
├── grbl_genmitsu.py       # Genmitsu-Spezialitäten
├── grbl_genmitsu_rotary_y.py  # Genmitsu Rotary (siehe ROTARY.md)
├── marlin.py              # 3D-Drucker mit CNC-Erweiterung
├── linuxcnc.py            # LinuxCNC / Mach3
├── duet.py                # Duet3D Controller
└── custom/                # User-eigene Post-Prozessoren
```

### 13.2 Was ein Post-Prozessor definiert

- Datei-Header (Maschinen-Init, Einheiten, etc.)
- Wie ein Werkzeugwechsel aussieht
- Wie Spindel ein/aus geschrieben wird
- Wie Eilbewegungen aussehen (G0 vs. spezielle Codes)
- Bohrzyklen (G81/G82/G83 oder simuliert)
- Datei-Footer
- Datei-Extension (.nc, .gcode, .ngc)

### 13.3 Endnutzer-Erweiterbarkeit

- Post-Prozessor in **dokumentierter Python-Klasse** definieren
- Beispiele und Templates mitgeliefert
- "User Postprocessor"-Verzeichnis das Updates überlebt
- Validierung beim Laden (Syntax-Check)

### 13.4 Controller-Profile

Über den Post-Prozessor hinaus: Maschinen-Eigenheiten (Soft-Limits, Probing-Befehle, Drehzahl-Mapping) liegen im Maschinen-Profil — separat vom Post-Prozessor.

---

## 14. Claude-Integration (MCP)

Wie PBP — Claude soll als Sparringspartner und Bediener funktionieren. **WICHTIG:** Die UI ist vollwertig stand-alone bedienbar. Das MCP ist die optionale zweite Bedienoberflaeche, die die gleiche Backend-API anspricht wie die UI.

### MCP-Tools (Auswahl)

```
Maschinen / Werkzeuge / Material:
  - maschine_anzeigen(profil_id)
  - werkzeug_hinzufuegen(parameter)
  - werkzeug_suchen(filter)
  - material_hinzufuegen(parameter)

Projekt:
  - projekt_erstellen(name, maschine, material)
  - projekt_speichern_als(pfad)
  - dxf_importieren(pfad)
  - rohmaterial_definieren(form, masse, position)
  - nullpunkt_setzen(x, y, z)

Setup-Workflow:
  - setup_erstellen(name, maschine_modus)
  - setup_pause_einfuegen(typ, anleitung)
  - arbeitsplan_generieren(format)

Zeichnen:
  - zeichnen_rechteck(masse, position)
  - zeichnen_kreis(durchmesser, position)
  - zeichnen_text(text, font, position)
  - boolean_operation(typ, objekte)

Operationen:
  - operation_kontur(geometrie, werkzeug, parameter)
  - operation_tasche(geometrie, werkzeug, parameter)
  - operation_bohren(punkte, werkzeug, parameter)
  - operation_gravur(geometrie, werkzeug, parameter)

Verschnittoptimierung:
  - nesting_starten(teile_liste, platte)

Berechnung & Export:
  - feeds_speeds_berechnen(material, werkzeug, operation)
  - toolpath_generieren(operation_id)
  - simulation_starten(projekt_id)
  - gcode_exportieren(pfad)
  - auto_cam_erstellen(geometrie, material, ziel)

G-Code-Manipulation:
  - gcode_lesen(pfad)
  - gcode_suchen_ersetzen(suchen, ersetzen)
  - gcode_befehl_erklaeren(befehl)

Analyse & Optimierung:
  - projekt_pruefen(projekt_id)
  - bearbeitungszeit_schaetzen(projekt_id)
  - vorschlaege_optimierung(projekt_id)
```

### Beispiel-Dialoge

> "Importiere die DXF von gestern und mach eine Kontur mit 6mm Tabs."
> 
> "Leg mir einen 6mm Einschneider aus Hartmetall mit 2 Schneiden an."
> 
> "Ermittle die optimale Bearbeitung für dieses Teil aus diesem Rohmaterial."
> 
> "Erstell die komplette CAM-Bearbeitung — ich editier dann manuell nach."
> 
> "Ich brauche 4 Rohlinge aus dieser Buche-Platte — ordne die optimal an."
> 
> "Bau einen Multi-Setup-Workflow: erst 2D-Rohling, dann auf Rotary."
> 
> "Pruef mal den Toolpath — ist der noch im Arbeitsraum?"
> 
> "Setze alle Vorschuebe in der Datei von 2000 auf 1500 mm/min."

---

## 15. Architektur

### Technologie-Stack

```
Desktop-App (Electron)
  Renderer: React 19 + Vite + Tailwind CSS
  Main Process: Node.js (Dateisystem, OS-Integration)
  Bridge: IPC zwischen Renderer und Main

Backend (Python 3.11+)
  Lokal als Subprozess der Electron-App gestartet
  Flask                  - REST-API (localhost only)
  ezdxf                  - DXF-Parser
  numpy                  - Geometrie & Matrix
  shapely                - 2D-Geometrie-Operationen (Offset, Boolean)
  numpy-stl / trimesh    - STL-Handling (Phase 2)
  pydantic               - Datenmodelle
  SQLAlchemy + SQLite    - Persistenz
  rectpack / nest2D      - Verschnittoptimierung

Frontend-Bibliotheken
  three.js               - 3D-Visualisierung & Simulation
  konva.js               - 2D-Canvas (Zeichnen + Vorschau)
  monaco-editor          - G-Code Editor (gleiche Engine wie VS Code)
  zustand                - State Management
  i18next                - Internationalisierung (DE/EN)

MCP-Server (Python)
  FastMCP                - MCP-Implementation
  HTTP-Bridge zu Flask   - Tool-Aufrufe an Backend (gleiche API wie UI)
```

### Internationalisierung

- **DE-zuerst** — Entwicklung in Deutsch (präziser für technische Begriffe)
- **i18next** mit Translation-Keys von Anfang an
- **EN-Übersetzung** als zweite Sprache nach Stabilisierung
- Weitere Sprachen Community-basiert (wie EstlCAM)

### Datenmodell (Kern)

```
Maschine (1) ----< (N) Projekt
Material (1) ----< (N) Projekt
Werkzeug (1) ----< (N) Operation
Projekt (1) ----< (N) Variante
Variante (1) ----< (N) Setup
Setup     (1) ----< (N) Operation
Setup     (1) ----< (N) Setup-Pause (vor diesem Setup)
Operation (1) ----< (N) Toolpath-Segment
Projekt   (1) -----  (1) Rohmaterial
Projekt   (1) -----  (N) GeometrieObjekt
```

### Repository-Struktur

```
CAMWOSA/
├── electron/             # Electron Main Process
│   ├── main.js
│   ├── preload.js
│   └── backend_runner.js # startet Python-Backend
├── frontend/             # React-Renderer
│   ├── src/
│   │   ├── viewer2d/
│   │   ├── viewer3d/
│   │   ├── editor/       # G-Code Editor (Monaco)
│   │   ├── drawing/      # Zeichnen-Modul
│   │   ├── operations/
│   │   ├── workflow/     # Multi-Setup + Arbeitsplan
│   │   ├── nesting/      # Verschnittoptimierung
│   │   ├── settings/
│   │   └── locales/      # i18n DE/EN
│   └── public/
├── backend/
│   ├── camwosa/
│   │   ├── dxf/
│   │   ├── stl/
│   │   ├── cam/
│   │   ├── gcode/
│   │   ├── feeds/
│   │   ├── nesting/      # Verschnitt-Algorithmen
│   │   ├── workflow/     # Setup-Management
│   │   ├── postprocessor/
│   │   ├── db/
│   │   └── api/
│   └── tests/
├── mcp_server/
│   └── server.py
├── installer/            # Cross-Platform Installer
├── docs/
│   ├── SPECIFICATION.md  # dieses Dokument
│   └── ROTARY.md         # Rotary-Achse Spec
└── data/
    ├── machines/
    ├── tools/
    ├── materials/
    └── postprocessors/
```

---

## 16. Workflow von der Zeichnung zum G-Code

Der typische Ablauf in CAMWOSA:

```
1. Projekt anlegen oder oeffnen
   └─> Maschine waehlen (z.B. ProVerXL 4030 V2)

2. Rohmaterial definieren
   ├─> Form (Quader, Zylinder, Platte, frei)
   ├─> Masse eingeben
   └─> Material auswaehlen (z.B. Buche)

3. Geometrie erstellen
   ├─> DXF importieren (aus Solid Edge)
   ├─> ODER: STL importieren (fuer Relief)
   └─> ODER: Direkt in CAMWOSA zeichnen

4. (Optional bei mehreren Teilen) Verschnittoptimierung
   └─> Teile + Platte → automatische Anordnung

5. Multi-Setup-Workflow (falls noetig)
   ├─> Setup 1 anlegen
   ├─> Setup-Pause (Umspannen / Werkzeug)
   └─> Setup 2 anlegen ...

6. Nullpunkt setzen (pro Setup)
   ├─> Auf Geometrie (z.B. Mittelpunkt)
   └─> Rotation/Spiegelung falls noetig

7. Operationen anlegen (pro Setup)
   ├─> Kontur, Tasche, Bohren, Gravur, Relief
   ├─> Werkzeug waehlen (aus Bibliothek)
   ├─> Feeds & Speeds: auto oder manuell
   └─> Reihenfolge festlegen

8. Toolpaths generieren
   └─> Sofort visueller Preview + Sicherheits-Checks

9. Simulation
   ├─> 2D-Preview pruefen
   ├─> 3D-Simulation mit Materialabtrag (Phase 2)
   └─> Statistiken pruefen (Zeit, Verfahrweg)

10. G-Code pruefen und anpassen
    ├─> Editor oeffnen
    ├─> Auf Wunsch: Vorschuebe anpassen, Tiefen aendern
    └─> Zeilenweise simulieren

11. G-Code exportieren
    ├─> Post-Prozessor waehlen (GRBL Standard)
    ├─> Eine Datei pro Setup (.nc / .gcode)
    └─> Manuell in CNCjs laden

12. Arbeitsplan ausdrucken (bei Multi-Setup)
    └─> Checkliste neben CNC, Schritt fuer Schritt

13. Projekt speichern
    ├─> Als Variante speichern (fuer aehnliche Werkstuecke)
    └─> Backup als ZIP
```

---

## Roadmap (ueberarbeitet)

| Phase | Inhalt | Status |
|-------|--------|--------|
| **Konzept** | Vision, Architektur, Repository | ✅ |
| **Phase 1 — MVP** | Electron-Setup, DXF-Import, Zeichnen, Kontur+Tasche+Bohren, Feeds&Speeds, 2D-Preview, Sicherheits-Checks, GRBL-Output, G-Code-Editor, Projekt-Mgmt, **Multi-Setup-Workflow + Arbeitsplan**, **Verschnittoptimierung**, DE-UI | 🔜 |
| **Phase 2 — Tiefe** | STL-Relief, 3D-Simulation Materialabtrag, EN-Übersetzung, Plugin-System Post-Prozessoren | ⏳ |
| **Phase 3 — Rotary** | Rotary-Modus, 4-Achs-Indexing, Wrapping (siehe ROTARY.md) | ⏳ |
| **Phase 4 — Drechseln** | Drechsel-Operationen, Spirale/Helix (siehe ROTARY.md) | ⏳ |
| **Phase 5 — Pro** | Werkzeug-Standzeit, Kollisionsanalyse, Adaptive Clearing, Community-Sharing | ⏳ |

---

## Offene Themen (zu klären während der Umsetzung)

- Performance-Schwelle für Live-Sync im G-Code Editor (ab wie vielen Zeilen abschalten?)
- Welche Schriftarten werden für Text-Gravur unterstützt? (System-Fonts? Eigene?)
- Wie sieht das Update-System aus? (Eigener Updater wie PBP?)
- Soll Material- und Werkzeug-DB optional Cloud-syncbar sein? (oder nur lokal/JSON-Export)
- Welche Nesting-Bibliothek? (rectpack reicht für rechteckige Bins, nest2D fuer No-Fit-Polygon)

---

> Letztes Update: 15.05.2026
> Autor: Markus Birzite & Claude
> An <b>ELWOSA</b> Project
