# Hobby-CAM für Menschen ohne Vorkenntnisse — Tiefenanalyse

> **Stand:** 2026-05-21 · Analyse als Opus 4.8 · grounded im echten Code-Stand
> (746 Tests, 17 Views, 24 CAM-Module, Cluster I/J fast komplett).
> **Zweck:** Was braucht eine CAM-Software für den Privatanwender wirklich,
> wie ist die Arbeitsweise, was hat CAMWOSA davon — und vor allem: **was fehlt,
> damit ein Mensch OHNE CNC-Vorwissen vom Idee zum fertig gefrästen Teil kommt.**
> **Ergebnis:** Master-Plan Cluster **K** (Anfänger-Erlebnis) + **L** (Design-Eingabe).

---

## 0. Die zentrale Erkenntnis vorweg

CAMWOSAs **Backend ist auf Industrie-Niveau** — 2.5D + 3D-Strategien (Parallel,
Scallop, Adaptive, Waterline), Rotary, Drechseln, Bild-zu-Relief mit AI,
Auto-Inlay, Thread-Milling, Arc-Fitting, Spanausdünnung, Z-Grid-Diagnose,
Spannmittel-Kollision, Run-Lock. Das ist mehr, als die meisten kommerziellen
Hobby-Tools haben.

**Die Lücke ist fast vollständig die anfänger-zugewandte Bedien-Schicht.**

Anders gesagt: CAMWOSA kann heute Dinge berechnen, die ein Anfänger gar nicht
*anfordern* kann, weil ihm die Sprache, die Führung und die Vertrauenssignale
fehlen. Der wertvollste Hebel ist nicht noch eine Frässtrategie — es ist die
**geführte Schicht, die das mächtige Backend für jemanden ohne Vorwissen
bedienbar macht.**

---

## 1. Wer ist der Anfänger? (Persona „Anna")

Anna hat sich eine günstige CNC gekauft (Genmitsu 3018, SainSmart, oder die
ProVerXL wie Markus). Sie will:

- ein Namensschild gravieren
- eine Holzform ausschneiden
- einen Untersetzer mit Logo machen
- vielleicht ein Relief aus einem Foto

Anna **weiß nicht**:
- was Vorschub, Drehzahl, Zustellung, Stepover bedeuten
- den Unterschied zwischen Gleichlauf- und Gegenlauffräsen
- warum man Haltestege (Tabs) braucht
- was G-Code ist (außer „die Datei, die die Maschine frisst")
- wie man den Werkstück-Nullpunkt setzt
- was Rundlauf, Spannzange, Spanlast heißt
- welcher Fräser wofür ist

Anna **hat**:
- die Maschine (deren genaue Grenzen sie oft nicht kennt)
- einen Beutel Fräser — **meist unbeschriftet**
- ein Stück Holz/Plastik
- eine Design-Idee (Bild, Form, oder Text)

Anna **denkt in Zielen** („ich will dieses Ding"), nicht in Fertigungsschritten
(„Rohteil → Aufspannung → Operationen → Toolpath → Simulation → Post → Run").

---

## 2. Das Kernproblem: Ziel-Modell vs. Fertigungs-Modell

Professionelle CAM (Fusion, Vectric, EstlCAM) setzt voraus, dass du das
**Fertigungs-Modell** verstehst. Eine Anfängerin hat ein **Ziel-Modell**.

| Profi denkt | Anna denkt |
|---|---|
| „2D-Kontur, außen, mit 4 Tabs, climb" | „die Form ausschneiden, ohne dass sie wegfliegt" |
| „Tasche, 40 % Stepover, adaptiv" | „die Mitte aushöhlen" |
| „V-Carve, 60°, flat-bottom-cleanup" | „den Namen schön reingravieren" |
| „Stepdown 2 mm, 6 Pässe" | „wie tief? keine Ahnung — geht das einfach?" |

**Die zentrale Design-Aufgabe von CAMWOSA als Hobby-Tool:**
> Die Brücke vom Ziel-Modell zum Fertigungs-Modell bauen — **ohne den
> Fachjargon vorzeigen zu müssen, bevor der User dafür bereit ist.**

CAMWOSA hat erste Brückenpfeiler (QuickCAM-Templates, Auto-CAM, First-Run-
Wizard, Tooltip-System). Aber es gibt keinen durchgehenden roten Faden, und
die Brücke endet oft mitten im Fluss.

---

## 3. Die kanonische Hobby-CAM-Arbeitsweise (7 Phasen)

Für jede Phase: **wie es funktioniert** → **was CAMWOSA hat (✅)** → **was für
Anfänger fehlt (❌)**.

### Phase 0 — Vorbereitung: Maschine, Werkzeug, Material kennen

**Realität:** Anna packt die CNC aus. Beutel mit Fräsern — unbeschriftet. Ein
Stück Sperrholz. Sie weiß nicht, ob ihr „1/8-Zoll-Bit" 3,175 mm ist.

**✅ CAMWOSA hat:** First-Run-Wizard (kann seit alpha.4 Maschine/Spindel/
Werkzeug/Material *anlegen*, nicht nur wählen), 5 Default-Maschinenprofile,
Werkzeug-Bibliothek mit 12 Typen, Material-DB.

**❌ Anfänger-Lücken:**
- **Mystery-Bit-Helfer** — „Miss deinen Fräser mit dem Messschieber, wir sagen
  dir, welcher Typ das ist." Schaft-Ø + Gesamtlänge + Form-Auswahl per Bild
  (flach / rund / V / spitz) → Werkzeug-Vorschlag. **Das häufigste Anfänger-
  Problem überhaupt** — der Beutel unbeschrifteter Bits.
- **Starter-Set pro Maschine** — „Du hast eine Genmitsu 3018? Hier ist der
  typische Lieferumfang als fertige Werkzeug-Bibliothek." Ein Klick → 6 Bits.
- **Maschinen-Wahl nach Kauf statt nach Spec** — Bildliste gängiger Hobby-CNCs
  statt Arbeitsraum-Zahlen eintippen.
- **Material-Wahl per Bild + Alltagssprache** — „Holz / Plastik / Weichmetall"
  mit Fotos, statt Janka-Härte und Schnittgeschwindigkeit.

### Phase 1 — Design rein bekommen

**Realität:** drei Wege — zeichnen, importieren, aus Bild/Text.

**✅ CAMWOSA hat:** ZeichnenView (Konva, Snap-Grid), CAD-Import (DXF/SVG/STL/
STEP mit Plugins), Bild-zu-Relief (Heightmap + 6 Filter + AI-Tiefe),
Text-zu-Pfad-**Backend** (A37).

**❌ Anfänger-Lücken:**
- **Zeichnen — numerische Eingabe + nachträgliches Editieren (D28, geplant).**
  Anna zeichnet grob, will dann „mach das 50×30 mm". Ohne das ist die Zeichen-
  View für präzise Arbeit unbrauchbar. **Kritisch.**
- **Zeichnen — Undo/Redo (Teil von D28).** Anfänger machen ständig Fehler.
- **Zeichnen — Snap/Ausrichten (D29, geplant).**
- **Text-Werkzeug-UI (D30, geplant).** Backend existiert, UI fehlt.
  „Schreib einen Namen" ist Hobby-Use-Case Nr. 1.
- **Bitmap → Vektor-Trace (NEU, nicht im Plan).** Ein PNG-Logo (schwarz/weiß)
  in eine *Schneid-Kontur* umwandeln. Bild-zu-Relief macht Heightmap (3D-Tiefe);
  ein Logo *ausschneiden oder gravieren* braucht eine 2D-Outline/Centerline —
  ein komplett anderer, sehr häufiger Wunsch. **Fehlt ganz.**
- **Clipart/Form-Bibliothek (NEU).** Herzen, Sterne, Zahnräder, Rahmen,
  Pfeile. Anna will nicht jedes Herz selbst zeichnen.
- **Sichtbare Bemaßung/Lineale (NEU).** „Wie groß ist das jetzt eigentlich?"

### Phase 2 — Sagen, was passieren soll (Operation)

**Profi-Modell:** Operations-Typ wählen (Kontur/Tasche/Bohren/Gravur/Relief),
Geometrie zuweisen, Parameter setzen.

**Anfänger-Problem:** Anna kennt „Kontur vs Tasche vs Gravur" nicht. Sie denkt
„ausschneiden / aushöhlen / eingravieren / 3D-schnitzen / Löcher bohren".

**✅ CAMWOSA hat:** OperationenView mit Override-Form + Live-3D-Preview, D31
Geometrie→Operation-Verknüpfung (Quick-Create-Buttons), QuickCAM (4 Templates),
Auto-CAM (5 Aufgabentypen).

**❌ Anfänger-Lücken:**
- **Intent-basierter Operations-Picker (NEU).** Statt „wähle Operations-Typ" →
  „Was soll mit dieser Form passieren?" mit Bildern: 🔪 ganz durchschneiden ·
  🕳 Vertiefung aushöhlen · ✏️ Linien eingravieren · 🏔 3D-Relief · 🔩 Löcher
  bohren. Übersetzt Absicht → Operations-Typ + sinnvolle Defaults.
- **Innen/Außen-Linie visuell (Teil D31/D28).** „Soll der Fräser INNEN oder
  AUSSEN der Linie laufen?" mit Bild. Häufigster Anfänger-Denkfehler — Teil
  wird zu groß/klein. Heute eine nackte Dropdown-Auswahl „innen/aussen/auf_linie".
- **QuickCAM ist gut, aber Template-Inseln.** Der Sprung von „ich hab gezeichnet"
  zu „QuickCAM-Template" ist nicht verbunden — es sind zwei getrennte Welten.

### Phase 3 — Werkzeug + Feeds & Speeds

**✅ CAMWOSA hat (sehr stark):** Feeds&Speeds-Rechner, Presets pro Material/
Werkzeug, Spindel-aware RPM-Grenzen, Chip-Thinning (J3), Warnungen,
`auto_set_speeds` (A46), Live-Panel beim Editieren (D15).

**❌ Anfänger-Lücken:**
- **„Sicher starten"-Modus + Konfidenz-Ampel (NEU).** Die Zahlen sind korrekt,
  aber Anna braucht „🟢 sicher für deine Kombination" oder „🟡 bewusst
  konservativ — du kannst später schneller werden". Ein **Vertrauenssignal**
  statt nackter mm/min.
- **Akustik-/Feedback-Coach (NEU).** „Wenn es rattert → Vorschub runter. Wenn
  es brennt → RPM runter oder Vorschub hoch." Anfänger haben keine Klang-
  Erfahrung, wann ein Schnitt „gut" klingt.

### Phase 4 — Werkstück platzieren + spannen

**✅ CAMWOSA hat:** Rohmaterial (Form/Position/Nullpunkt), Spannmittel-Modell
(A47, 8 Typen, Sperrzonen, Kollisions-Check), Z-Grid-Diagnose (Ebenheit).

**❌ Anfänger-Lücken:**
- **Nullpunkt-Erklär-Guide (NEU).** „Wo ist dein Nullpunkt?" — die meisten
  Hobby-Maschinen nutzen vorne-links-oben. Anna weiß nicht mal, was das ist.
  Visueller Guide + Standard-Empfehlung + „warum das wichtig ist".
- **Spannmittel-Platzierung im Anfänger-UI (erweitert A47).** Backend prüft
  Kollision — aber gibt es eine einfache View „zeig wo deine Klemmen sind,
  wir prüfen, ob der Fräser sie trifft"?
- **„Hält dein Teil?"-Check (NEU).** Bei Durchschnitt-Konturen: „Dein Teil löst
  sich beim letzten Schnitt — brauchst du Haltestege?" Tabs existieren, aber
  die proaktive Aufklärung fehlt.

### Phase 5 — Vorschau / Verifikation (Vertrauen aufbauen)

**Das ist für Anfänger die kritischste Phase** — sie brauchen Gewissheit, dass
nichts kracht, bevor sie auf Start drücken.

**✅ CAMWOSA hat:** 2D-Toolpath-Preview (tiefer Zoom), 3D-Voxel-Simulation
(Material-Abtrag, zeigt das fertige Werkstück), Sicherheits-Checks, Seiten-
Tiefenansicht.

**❌ Anfänger-Lücken:**
- **Animierte Schnitt-Wiedergabe (D35 — Animation, geplant).** Cutter-Symbol
  fährt den Pfad ab, Speed-Slider. Baut Anfänger-Vertrauen enorm — man *sieht*,
  was die Maschine tun wird. **Hoher Onboarding-Wert.**
- **Zeit-/Aufwand-Schätzung (NEU).** „Das dauert ca. 23 Min." Eine der ersten
  Anfänger-Fragen. Toolpath-Länge + Vorschub → Zeit. **Alle Daten sind da**
  (`gesamtlaenge`, `schnittlaenge`, `feed`), nur nicht aggregiert/angezeigt.
- **Klartext-Sicherheitszusammenfassung (NEU, verschränkt D36).** Die Safety-
  Checks sind technisch. „✓ Fräser trifft keine Klemme · ✓ nichts schneidet in
  den Tisch · ⚠ tiefer Schnitt — geh langsam" in Menschensprache.

### Phase 6 — G-Code raus + Übergabe an die Maschine

**✅ CAMWOSA hat:** G-Code-Generator (GRBL + Rotary), Monaco-Editor, Run-Lock
(„im Zweifel läuft das Programm nicht"), Arbeitsplan-Generator (A21, PDF +
Checkliste).

**❌ Anfänger-Lücken:**
- **„Was jetzt?"-Übergabe-Guide (NEU).** CAMWOSA pusht bewusst nicht zum Sender
  (Markus' Regel). Aber nach dem Speichern weiß Anna nicht weiter. Ein Schritt-
  für-Schritt-Bildschirm: „1. Datei gespeichert ✓ · 2. Öffne CNCjs/Candle ·
  3. Werkstück einlegen + spannen · 4. auf vorne-links fahren, Null setzen ·
  5. Datei laden · 6. Start." Pro Projekt druckbar — erweitert den Arbeitsplan.
- **Sender-Empfehlung nach Controller (NEU).** „Du hast GRBL? Nimm CNCjs, UGS
  oder Candle. So installierst du …" — neutral, ohne Push, ohne Wertung.

### Phase 7 — Es ging schief (die Lern-Schleife)

**✅ CAMWOSA hat:** nichts Spezifisches.

**❌ Anfänger-Lücken:**
- **Troubleshooting-Assistent (NEU).** „Wie sieht dein Ergebnis aus?" (verbrannt
  / ausgefranst / zu tief / verrutscht / Fräser gebrochen) → Diagnose + „neu
  berechnen mit Korrektur". Schließt die Lern-Schleife — Anfänger lernen aus
  Fehlern statt aufzugeben.

---

## 4. Querschnitts-Lücken (phasenübergreifend, anfänger-kritisch)

1. **Die Jargon-Wand.** Jeder Screen nutzt CNC-Begriffe. D21 Tooltip-System +
   12 Fachbegriffe sind ein Start, aber das D36-Audit (200+ Felder mit Hover-
   Hilfe) ist offen. → **Anfänger-Modus**, der Begriffe ergänzt/in Alltags-
   sprache übersetzt und *jedes* Feld mit einer Ein-Satz-Erklärung versieht.
2. **Kein durchgehender geführter Flow.** QuickCAM sind Template-Inseln. Es
   fehlt der „von der Idee zur fertigen Datei, an der Hand"-Assistent, der alle
   7 Phasen als roten Faden verbindet. (D35 nennt „Wizard-Framework", offen.)
3. **Kein Lernen durch Beispiele.** Keine Beispielprojekte (.cwp) mitgeliefert.
   „Öffne dieses fertige Untersetzer-Projekt und schau, wie es gebaut ist" ist
   für Anfänger Gold wert.
4. **Das Mystery-Bit-Problem** (Phase 0) — kein Tool, um den unbeschrifteten
   Beutel-Inhalt zu identifizieren.
5. **Kein Undo/Redo im Zeichnen** (Teil D28).
6. **Keine Zeit-Schätzung** (Phase 5).

---

## 5. Was CAMWOSA schon richtig stark hat (faire Bilanz)

Damit klar ist, dass die Lücke gezielt ist — das Fundament ist exzellent:

- **CAM-Strategien auf Profi-Niveau:** Kontur/Tasche/Bohren/Gravur/Relief +
  3D-Parallel/Scallop/Waterline/Adaptive + Drechseln + Wrap + PCB + Dogbone +
  Auto-Inlay + Thread-Milling + Drag-Engraving + Chamfer.
- **Toolpath-Qualität:** Arc-Fitting (G2/G3), Spanausdünnung, Lead-In/Out,
  Tabs, adaptive Modulation.
- **Sicherheit:** 6+ Checks, Spannmittel-Kollision, Collet-Check, Z-Grid-
  Diagnose, Run-Lock-Dependency-Graph.
- **Onboarding-Anfänge:** First-Run-Wizard (mit Anlegen), QuickCAM (4
  Templates), Auto-CAM (5 Aufgaben), Tooltip-System (3-stufig), 12 Fachbegriffe,
  Design-System mit 3 Density-Stufen + Fokus-Modus.
- **Architektur:** alles UI-editierbar, MCP-Parität, .cwp-Projektformat,
  Varianten, Multi-Setup-Workflow, Arbeitsplan-PDF.

**Die Bausteine sind da — sie sind nur noch nicht zu einem anfänger-sicheren
roten Faden verbunden, und die letzten Brücken (Sprache, Vertrauen, Übergabe)
fehlen.**

---

## 6. Priorisierte Lücken → Master-Plan

Die Lücken werden in zwei neue Cluster einsortiert (Master-Plan-First). Mehrere
bereits geplante D-Items (D28/D29/D30/D33/D34/D35/D36) sind Voraussetzungen und
werden referenziert, nicht dupliziert.

### Cluster K — Anfänger-Erlebnis / Zero-to-Cut

Die geführte Schicht über dem starken Backend. Priorität nach Anfänger-Nutzen:

| ID | Funktion | Phase | Nutzen |
|----|----------|-------|--------|
| K1 | **Geführter End-to-End-Assistent** — der rote Faden „von der Idee zur fertigen Datei" durch alle 7 Phasen. Baut auf QuickCAM + Auto-CAM auf, verbindet sie. | alle | 🔴 sehr hoch |
| K2 | **Intent-basierter Operations-Picker** — „Was soll passieren?" mit Bildern (durchschneiden/aushöhlen/gravieren/Relief/bohren) → Operations-Typ + Defaults. | 2 | 🔴 sehr hoch |
| K3 | **Mystery-Bit-Helfer + Starter-Sets** — Messschieber-Werte + Form-Bild → Werkzeug-Vorschlag; Ein-Klick-Bibliothek pro Hobby-Maschine. | 0 | 🔴 sehr hoch |
| K4 | **Konfidenz-Ampel + Klartext-Sicherheit** — Feeds-Vertrauenssignal (🟢/🟡) + Safety-Checks in Menschensprache. | 3,5 | 🟠 hoch |
| K5 | **Zeit-/Aufwand-Schätzung** — Toolpath-Länge + Vorschub → „~23 Min". Daten existieren, nur aggregieren. | 5 | 🟠 hoch (kleiner Aufwand) |
| K6 | **Animierte Schnitt-Wiedergabe** — Cutter fährt Pfad ab, Speed-Slider (Anteil von D35, hier als Anfänger-Vertrauens-Feature). | 5 | 🟠 hoch |
| K7 | **„Was jetzt?"-Übergabe-Guide** — Datei → Sender → Null → Play, druckbar; + Sender-Empfehlung nach Controller (neutral). | 6 | 🟠 hoch |
| K8 | **Troubleshooting-Assistent** — Ergebnis-Diagnose (verbrannt/ausgefranst/…) → Korrektur + Neuberechnung. | 7 | 🟡 mittel |
| K9 | **Beispielprojekte mitliefern** — 3–5 fertige .cwp (Untersetzer, Namensschild, Box) zum Lernen + Öffnen. | alle | 🟡 mittel |
| K10 | **Anfänger-Modus / Jargon-Brücke** — Begriffe in Alltagssprache + jedes Feld mit Hover-Hilfe (vollendet D36). | alle | 🟠 hoch |
| K11 | **Innen/Außen-Linie + Tabs-Aufklärung visuell** — Bilder statt Dropdown; proaktiver „dein Teil fliegt weg"-Hinweis. | 2,4 | 🟡 mittel |
| K12 | **Nullpunkt-Erklär-Guide** — visuelle Standard-Empfehlung (vorne-links-oben) + „warum". | 4 | 🟡 mittel |

### Cluster L — Design-Eingabe für Hobby

Design leicht reinbekommen (verwandt zu, aber nicht überlappend mit D28–D30):

| ID | Funktion | Nutzen |
|----|----------|--------|
| L1 | **Bitmap → Vektor-Trace** — PNG/JPG-Logo (s/w) → Schneid-Outline + Centerline für Ausschneiden/Gravieren. Der große fehlende Input-Weg. | 🔴 sehr hoch |
| L2 | **Clipart/Form-Bibliothek** — parametrische Standardformen (Herz, Stern, Zahnrad, Rahmen, Pfeil, abgerundetes Rechteck). | 🟠 hoch |
| L3 | **Bemaßung + Lineale im Zeichnen** — sichtbare Maße/Maßketten, „wie groß ist das". | 🟡 mittel |

---

## 7. Strategische Empfehlung

**Der höchste Hebel ist nicht mehr Backend — es ist die Anfänger-Schicht.**

Empfohlene Reihenfolge (jeweils kleine, in sich abgeschlossene, testbare
Schritte — Backend zuerst, dann UI, da UI Markus' Test-Loop braucht):

1. **K5 Zeit-Schätzung** + **K2 Intent-Picker-Backend** — kleine Backend-Wins
   mit sofortiger Anfänger-Wirkung, ohne UI-Test-Loop.
2. **L1 Bitmap-Trace-Backend** — der fehlende Design-Input-Weg (potrace-Ansatz
   oder eigener Marching-Squares-Konturfinder, den es für Waterline schon gibt).
3. **K3 Mystery-Bit + Starter-Sets** — Backend-Heuristik + Default-Bundles.
4. **K1 geführter Assistent** + **K6 Animation** + **K10 Jargon-Brücke** — die
   großen UI-Brocken, in Markus' Test-Sessions.

**Bewusst NICHT übernehmen:** Sender-Integration (Markus' Regel — nur Datei).
Der „Was jetzt?"-Guide (K7) bleibt deshalb rein erklärend, ohne Push.

---

## Anhang — Verweise

- `docs/FUSION-CAM-VERGLEICH.md` — Industrie-Referenz (Strategie-Seite)
- Master-Plan Cluster K + L (aus dieser Analyse)
- Issue #47 (Cluster K) · Issue #48 (Cluster L)
- Verwandte geplante D-Items: D28 (Zeichnen-Properties), D29 (Snap/Align),
  D30 (Text-Tool), D33 (Drehen-Editor), D34 (Werkzeug-SVGs), D35 (Project-Tree
  + Animation + Wizard-Framework), D36 (Hover-Help-Audit).
