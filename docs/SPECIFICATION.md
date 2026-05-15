# CAMWOSA — Funktionale Spezifikation

> Stand: 15.05.2026 · Status: Konzept (Architektur entschieden)

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
10. [Simulation & Visualisierung](#8-simulation--visualisierung)
11. [G-Code Editor](#9-g-code-editor)
12. [Projekt-Management](#10-projekt-management)
13. [Plugin-System für CNC-Steuerungen](#11-plugin-system-für-cnc-steuerungen)
14. [Claude-Integration (MCP)](#12-claude-integration-mcp)
15. [Architektur](#13-architektur)
16. [Workflow von der Zeichnung zum G-Code](#14-workflow-von-der-zeichnung-zum-g-code)

---

## Leitprinzipien

**Sicherheit vor Bequemlichkeit.** Jeder Toolpath ist visualisiert und prüfbar bevor er die Maschine erreicht. Lieber eine Frage zu viel als ein Crash.

**Maker statt Konzern.** CAMWOSA ist für 2.5D-Arbeit auf Hobby- und Semi-Pro-Maschinen optimiert. Keine 5-Achs-Komplexität, kein Engineering-Overhead.

**Claude als Sparringspartner.** Jede Funktion ist auch über Sprache/Chat zugänglich. Du kannst eine Operation per Klick anlegen ODER Claude bitten sie zu erzeugen — beide Wege funktionieren.

**Lokal & datenschutzfreundlich.** Wie PBP: läuft auf deinem Rechner, deine Daten bleiben bei dir, keine Cloud-Abhängigkeit.

**Wenig Klicks, gute Defaults.** Wenn du nichts änderst, kommt ein vernünftiges Ergebnis raus. Profis können trotzdem alles anpassen.

**Offene Architektur.** GRBL ist der erste Fokus — aber das System ist so gebaut, dass weitere Controller (Marlin, LinuxCNC, Mach3, …) als Plugin nachrüstbar sind.

---

## Architektur-Entscheidungen

Die Grundentscheidungen die alle weiteren Themen prägen:

| Entscheidung | Begründung |
|---|---|
| **Desktop-App (Electron)** | Native Datei-Integration, Drag&Drop, OS-Tray. Browser-UI später möglich (gleiches Backend) |
| **Integriertes Zeichnen** | LightBurn-inspiriert — schnelle Formen direkt erzeugen, kein Tool-Wechsel |
| **Simulation: stufenweise** | Phase 1: 2D + Sicherheits-Checks (Eilbewegung im Material, Bounding-Box). Phase 2: 3D-Materialabtrag. Phase 3: Kollisionsanalyse Werkzeughalter |
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
| Achsen-Konfiguration | XYZ (Rotary optional via DeskProto) |
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
**Workflow-Vergleich:**

| Klassisch (4 Tools) | CAMWOSA (1 Tool) |
|---|---|
| CAD öffnen | CAMWOSA öffnen |
| Zeichnen | Zeichnen |
| Als DXF exportieren | Operation anlegen |
| CAM öffnen | G-Code speichern |
| DXF importieren | |
| Operation anlegen | |
| G-Code exportieren | |

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
- Layer können Operationen zugeordnet werden (alle Objekte auf Layer "Tasche-3mm" werden gemeinsam mit denselben Parametern bearbeitet)
- Import von DXF (aus Solid Edge) wird automatisch ins Zeichnen-Modul übernommen und kann dort weiterbearbeitet werden

### Was NICHT eingebaut wird

- 3D-Modellierung (dafür gibt es Solid Edge / Blender)
- Komplexe Bemaßungstools für technische Zeichnungen
- Parametrische Constraints
- DWG-Editor

---

## 8. Simulation & Visualisierung

Das Herzstück gegen Crashes und Ausschuss. Stufenweise umgesetzt:

### 8.1 Phase 1 — 2D-Vorschau + Sicherheits-Checks

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

### 8.2 Phase 2 — 3D-Materialabtrag-Simulation

- Rohmaterial als 3D-Block dargestellt
- Werkzeug bewegt sich entlang Toolpath
- Material wird "abgetragen" — visueller Abtrag in Echtzeit
- Geschwindigkeit einstellbar (Zeitlupe → Schnellvorlauf)
- Pause / Step-Forward / Springen
- Toolpath-Linien zu/abschaltbar
- Endergebnis vergleichbar mit Soll-Modell (Differenz-Anzeige)

**Technologie:** Three.js, Voxel-basiert für Performance, optional Mesh-basiert für Genauigkeit.

### 8.3 Phase 3 — Kollisionsanalyse

- Werkzeughalter + Spindel als 3D-Geometrie
- Kollisionswarnung wenn Halter ins Material taucht
- Visualisierung der "no-go zones"

### 8.4 Statistiken pro Simulation

- Geschätzte Bearbeitungszeit
- Anzahl Werkzeugwechsel
- Gesamter Verfahrweg
- Spanvolumen
- Toolpath-Länge pro Operation

---

## 9. G-Code Editor

Ein **vollwertiger G-Code Editor** ist integriert — nicht nur ein passiver Viewer.

### 9.1 Basis-Funktionen

- Syntax-Highlighting (G/M-Codes farblich, Parameter, Kommentare)
- Zeilennummern
- Suchen & Ersetzen (mit Regex-Option)
- Undo / Redo
- Zeilen markieren / Blöcke verschieben
- Speichern / Speichern als
- Auto-Format (Spaltenausrichtung)
- Mehrere Tabs (verschiedene G-Code-Dateien parallel)

### 9.2 Befehlsbibliothek

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

### 9.3 Zeilenweise Simulation

- Klick in eine Zeile → Markierung in 2D/3D-Vorschau (wo das Werkzeug grade ist)
- Toggle "Live-Sync" — automatische Aktualisierung beim Bewegen des Cursors
- **Performance-Schalter** — bei großen G-Code-Dateien Live-Sync deaktivierbar
- Schritt-für-Schritt durchgehen (wie Debugger)

### 9.4 Massen-Editor (Find & Modify)

Beispiel: "Setze alle Vorschübe von 2000 auf 1500"
- Such-Pattern: `F2000`
- Ersetzen mit: `F1500`
- Vorschau der betroffenen Zeilen vor Anwendung
- **Operations-spezifisches Editieren:** "In allen Operationen vom Typ Tasche, reduziere Plunge-Rate um 20%"

### 9.5 Strukturansicht (Code-Outline)

Linke Spalte zeigt die G-Code-Struktur:
- Header (Maschinen-Setup)
- Werkzeug T1
  - Operation: Aussenkontur
  - Operation: Tasche 1
- Werkzeug T2
  - Operation: Bohrungen
- Footer (Spindel aus, zurück zur Park-Position)

Klick auf Eintrag → Springt zur entsprechenden Stelle.

### 9.6 Backplot-Annotation

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

## 10. Projekt-Management

### 10.1 Projekt-Konzept

Ein **CAMWOSA-Projekt** enthält alles was zum Werkstück gehört:
- Maschinen-Wahl
- Material + Rohmaterial-Definition
- Geometrie (Zeichnung / Import)
- Operationen
- Werkzeug-Zuordnungen
- Generierter Toolpath
- Generierter G-Code
- Notizen / Metadaten

**Dateiformat:** `.cwp` (CAMWOSA Project) — ein ZIP mit JSON + eingebetteten Geometrie-Dateien.

### 10.2 Speichern

- **Speichern** — bestehende Projektdatei überschreiben
- **Speichern als …** — neue Projektdatei (für Varianten)
- **Auto-Save** — alle X Minuten in temporären Snapshot (wiederherstellbar nach Crash)

### 10.3 Varianten / Versionen

Ein Projekt kann **mehrere Varianten** enthalten — z.B.:
- "Buche, 12mm — Standardversion"
- "MDF, 18mm — billig zum Testen"
- "Acryl, 5mm — als Vorlage"

Jede Variante hat eigene Material/Maschinen/Operationen-Einstellungen. **Wechsel zwischen Varianten per Dropdown.**

### 10.4 Projekt-Historie

- Wer hat wann was geändert? (Lokales Log)
- "Revert to last G-Code generation"
- Diff zwischen zwei Varianten

### 10.5 Projekt-Export / Import

- Komplettes Projekt als ZIP exportieren (für Backup / Sharing)
- Projekt importieren (mit Konflikt-Behandlung bei fehlenden Werkzeugen/Materialien)

---

## 11. Plugin-System für CNC-Steuerungen

GRBL ist Start — das System ist aber **offen für andere Controller**.

### 11.1 Post-Prozessor-Architektur

Jeder Controller hat seinen eigenen Post-Prozessor — definiert in einer einzelnen Python-Datei oder JSON-Konfiguration:

```
postprocessor/
├── grbl_standard.py       # GRBL 1.1 Standard (Default)
├── grbl_genmitsu.py       # Genmitsu-Spezialitäten
├── marlin.py              # 3D-Drucker mit CNC-Erweiterung
├── linuxcnc.py            # LinuxCNC / Mach3
├── duet.py                # Duet3D Controller
└── custom/                # User-eigene Post-Prozessoren
```

### 11.2 Was ein Post-Prozessor definiert

- Datei-Header (Maschinen-Init, Einheiten, etc.)
- Wie ein Werkzeugwechsel aussieht
- Wie Spindel ein/aus geschrieben wird
- Wie Eilbewegungen aussehen (G0 vs. spezielle Codes)
- Bohrzyklen (G81/G82/G83 oder simuliert)
- Datei-Footer
- Datei-Extension (.nc, .gcode, .ngc)

### 11.3 Endnutzer-Erweiterbarkeit

- Post-Prozessor in **dokumentierter Python-Klasse** definieren
- Beispiele und Templates mitgeliefert
- "User Postprocessor"-Verzeichnis das Updates überlebt
- Validierung beim Laden (Syntax-Check)

### 11.4 Controller-Profile

Über den Post-Prozessor hinaus: Maschinen-Eigenheiten (Soft-Limits, Probing-Befehle, Drehzahl-Mapping) liegen im Maschinen-Profil — separat vom Post-Prozessor.

---

## 12. Claude-Integration (MCP)

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
  - projekt_speichern_als(pfad)
  - dxf_importieren(pfad)
  - rohmaterial_definieren(form, masse, position)
  - nullpunkt_setzen(x, y, z)

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

Berechnung & Export:
  - feeds_speeds_berechnen(material, werkzeug, operation)
  - toolpath_generieren(operation_id)
  - simulation_starten(projekt_id)
  - gcode_exportieren(pfad)

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
> "Zeichne mir ein Rechteck 100x60 und gravier 'Werkstatt' darauf."
> 
> "Ich brauche eine Tasche 80x40mm, 8mm tief, in Buche, mit dem 6mm Einschneider."
> 
> "Pruef mal den Toolpath — ist der noch im Arbeitsraum?"
> 
> "Welcher Fraeser passt besser fuer Acryl?"
> 
> "Optimiere die Reihenfolge der Operationen damit weniger Werkzeugwechsel noetig sind."
> 
> "Setze alle Vorschuebe in der Datei von 2000 auf 1500 mm/min."
> 
> "Zeig mir die Simulation in Zeitlupe ab Operation 3."

---

## 13. Architektur

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

Frontend-Bibliotheken
  three.js               - 3D-Visualisierung & Simulation
  konva.js               - 2D-Canvas (Zeichnen + Vorschau)
  monaco-editor          - G-Code Editor (gleiche Engine wie VS Code)
  zustand                - State Management
  i18next                - Internationalisierung (DE/EN)

MCP-Server (Python)
  FastMCP                - MCP-Implementation
  HTTP-Bridge zu Flask   - Tool-Aufrufe an Backend
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
Variante (1) ----< (N) Operation
Operation (1) ----< (N) Toolpath-Segment
Projekt (1) -----  (1) Rohmaterial
Projekt (1) -----  (N) GeometrieObjekt
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
│   │   ├── postprocessor/
│   │   ├── db/
│   │   └── api/
│   └── tests/
├── mcp_server/
│   └── server.py
├── installer/            # Cross-Platform Installer
├── docs/
└── data/
    ├── machines/
    ├── tools/
    ├── materials/
    └── postprocessors/
```

---

## 14. Workflow von der Zeichnung zum G-Code

Der typische Ablauf in CAMWOSA:

```
1. Projekt anlegen oder öffnen
   └─> Maschine wählen (z.B. ProVerXL 4030 V2)

2. Rohmaterial definieren
   ├─> Form (Quader, Zylinder, Platte, frei)
   ├─> Maße eingeben
   └─> Material auswählen (z.B. Buche)

3. Geometrie erstellen
   ├─> DXF importieren (aus Solid Edge)
   ├─> ODER: STL importieren (für Relief)
   └─> ODER: Direkt in CAMWOSA zeichnen (Phase 1!)

4. Nullpunkt setzen
   ├─> Auf Geometrie (z.B. Mittelpunkt)
   └─> Rotation/Spiegelung falls noetig

5. Operationen anlegen
   ├─> Kontur, Tasche, Bohren, Gravur, Relief
   ├─> Werkzeug wählen (aus Bibliothek)
   ├─> Feeds & Speeds: auto oder manuell
   └─> Reihenfolge festlegen

6. Toolpaths generieren
   └─> Sofort visueller Preview + Sicherheits-Checks

7. Simulation
   ├─> 2D-Preview pruefen
   ├─> 3D-Simulation mit Materialabtrag (Phase 2)
   └─> Statistiken pruefen (Zeit, Verfahrweg)

8. G-Code prüfen und anpassen
   ├─> Editor öffnen
   ├─> Auf Wunsch: Vorschübe anpassen, Tiefen ändern
   └─> Zeilenweise simulieren

9. G-Code exportieren
   ├─> Post-Prozessor wählen (GRBL Standard)
   ├─> Datei speichern (.nc oder .gcode)
   └─> Manuell in CNCjs laden

10. Projekt speichern
    ├─> Als Variante speichern (für ähnliche Werkstücke)
    └─> Backup als ZIP
```

---

## Roadmap (überarbeitet)

| Phase | Inhalt | Status |
|-------|--------|--------|
| **Konzept** | Vision, Architektur, Repository | ✅ |
| **Phase 1 — MVP** | Electron-Setup, DXF-Import, Zeichnen, Kontur+Tasche+Bohren, Feeds&Speeds, 2D-Preview, GRBL-Output, G-Code-Editor, Projekt-Speichern, DE-UI | 🔜 |
| **Phase 2 — Tiefe** | STL-Relief, 3D-Simulation Materialabtrag, EN-Übersetzung, Plugin-System Post-Prozessoren | ⏳ |
| **Phase 3 — Pro** | Werkzeug-Standzeit, Kollisionsanalyse, Adaptive Clearing, Community-Sharing | ⏳ |

---

## Offene Themen (zu klären während der Umsetzung)

- Performance-Schwelle für Live-Sync im G-Code Editor (ab wie vielen Zeilen abschalten?)
- Welche Schriftarten werden für Text-Gravur unterstützt? (System-Fonts? Eigene?)
- Wie sieht das Update-System aus? (Eigener Updater wie PBP?)
- Soll Material- und Werkzeug-DB optional Cloud-syncbar sein? (oder nur lokal/JSON-Export)

---

> Letztes Update: 15.05.2026
> Autor: Markus Birzite & Claude
> An <b>ELWOSA</b> Project
