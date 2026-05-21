# Fusion 360 CAM — Vergleich + Erkenntnisse fuer CAMWOSA

> **Stand:** 2026-05-21 · Analyse auf Basis der Fusion-360-MCP-Tools
> (`mcp__fusion360__cam_*`) + Fusion-CAM-Domaenenwissen.
> **Zweck:** Industrie-Referenz pruefen → GAPs zu CAMWOSA finden → Master-Plan
> mit den lohnenswerten Punkten anreichern (Master-Plan-First).
>
> ⚠ Fusion lief beim Erstellen nicht live — Analyse aus den Tool-Schemas
> (verlaesslich, da die Enums die Faehigkeiten direkt benennen) + bekanntem
> Fusion-CAM-Funktionsumfang. Eine Live-Verifikation (echte Operation in
> Fusion anlegen + Toolpath ansehen) steht noch aus.

---

## 1. Was die Fusion-MCP exponiert

Die MCP gibt **7 High-Level-CAM-Tools** frei:

| Tool | Zweck |
|---|---|
| `cam_create_setup` | Setup mit Stock + Koordinatensystem + Operation-Typ |
| `cam_create_operation` | Operation mit Strategie + Werkzeug + Feeds |
| `cam_generate_toolpath` | Toolpath rechnen (einzeln oder ganzes Setup) |
| `cam_list_setups` / `cam_list_operations` | Auflisten |
| `cam_get_operation_info` | Detail einer Operation |
| `cam_post_process` | NC-Code erzeugen (post-processor-Auswahl) |

Das ist nur ein **Bruchteil** der echten Fusion-CAM-API, aber die Enums
verraten den Kern des Modells.

### Setup-Modell

```
operation_type: milling | turning | cutting
stock_mode:     relative_box | fixed_box | from_body
stock_offset:   top / bottom / sides (cm)
body_name:      welcher CAD-Body gefraest wird
```

**Kern-Erkenntnis:** Fusion macht CAM **immer aus einem 3D-Body** heraus.
Das Stock (Rohmaterial) wird relativ zum Body definiert — `relative_box`
(Body + Offsets), `fixed_box` (absolute Maße) oder `from_body` (Stock = ein
anderer Koerper, z.B. das Ergebnis eines vorherigen Setups → **Rest-Material**).

### Operation-Strategien (16)

| Fusion-Strategie | Klasse | CAMWOSA-Pendant |
|---|---|---|
| `face` | 2.5D | ❌ kein dediziertes Planfraesen |
| `2d_contour` | 2.5D | ✅ `kontur` |
| `2d_pocket` | 2.5D | ✅ `tasche` (parallel/spiral/offset) |
| `2d_adaptive` | 2.5D | ✅ `tasche` strategie=adaptive |
| `slot` | 2.5D | ⚠ via `kontur` machbar, keine eigene Op |
| `trace` | 2.5D | ⚠ ~`gravur` konstante_tiefe |
| `engrave` | 2.5D | ✅ `gravur` (inkl. v_carving — MCP zeigt v_carving nicht!) |
| `drilling` | Loch | ✅ `bohren` (standard/peck/tief_peck/reib) |
| `bore` | Loch | ✅ `bohren` strategie=helix |
| `thread_milling` | Loch | ✅ `thread_milling` (alpha.5!) |
| `3d_adaptive` | **3D** | ❌ nur 2D-adaptive |
| `3d_pocket` | **3D** | ❌ |
| `3d_contour` | **3D** | ✅ `waterline` (alpha.3) |
| `3d_parallel` | **3D** | ⚠ teilweise via `relief` (Heightmap-Parallel) |
| `3d_scallop` | **3D** | ❌ |

### Operation-Parameter

```
tool_number (aus Library) | tool_diameter
spindle_speed (RPM), feed_rate (cm/min)
stepdown (axial), stepover (radial)
coolant: disabled | flood | mist | through_tool
```

### Post-Prozessoren

`fanuc | grbl | haas | linuxcnc | mach3` + mm/in.
CAMWOSA: GRBL + GRBL-Rotary (bewusst GRBL-fokussiert, Plugin-System vorhanden).

---

## 2. GAP-Analyse — was CAMWOSA fehlt

Sortiert nach **Praxis-Nutzen fuer Markus' Hobby-CNC-Workflow** (Holz, Alu,
ProVerXL 4030 V2, 2.5D + Relief + Rotary).

### 🔴 GROSS — echte 3D-Strategien-Familie

Fusions Kernstaerke. CAMWOSA hat aktuell nur `waterline` (≈ 3d_contour) +
`relief` (Heightmap-Z-Map). Was fehlt:

| Strategie | Was sie macht | Nutzen fuer Markus |
|---|---|---|
| **3d_adaptive** | 3D-Schruppen mit konstantem Werkzeug-Eingriff (trochoidal, lastkonstant) | hoch — schnelles, werkzeugschonendes Vorraeumen von 3D-Teilen (Schalen, Reliefs, Figuren) |
| **3d_parallel** | parallele Linien auf 3D-Flaeche projiziert | hoch — Standard-Schlichtstrategie fuer flache-bis-mittlere Flaechen |
| **3d_scallop** | konstante Riefenhoehe (Cusp/Scallop-Height) entlang Kontur-Offset | mittel-hoch — gleichmaessige Oberflaeche auf steilen+flachen Bereichen |
| **3d_pocket** | Z-Level-Schruppen einer 3D-Tasche | mittel |
| **pencil/3d_pencil** | Kehlnaht-Nachbearbeitung in Ecken (in MCP nicht exponiert, aber Fusion kann's) | mittel |

**Einordnung:** CAMWOSA ist laut CLAUDE.md ein **2.5D-Tool**. Aber `relief` +
`waterline` sind bereits 3D-Einstiege. Der Schritt zu 3d_parallel + 3d_scallop
auf STL-Bodies wuerde CAMWOSA von „2.5D + Relief" zu „echtes 3D-Schlichten"
heben — der groesste qualitative Sprung. Das deckt sich mit **Master-Plan A40**
(3D-Drehen-Pipeline) + waere ein neuer Cluster „3D-Frasstrategien".

### 🟠 MITTEL — Planfräsen (`face`)

Eigene Strategie zum Ebnen des Rohmaterials (Spoilboard-Surfacing, Stock-Top
planen). CAMWOSA hat das nicht — man muesste eine Tasche ueber die ganze
Flaeche missbrauchen.

**Synergie:** Passt perfekt zur **Z-Grid-Diagnose** (alpha.5)! Wenn die
Diagnose „unebene Oberflaeche → Werkstueck planen" empfiehlt, sollte es genau
diese `face`-Op zum Anlegen geben. Kleiner Aufwand, hoher Praxisnutzen.

### 🟠 MITTEL — Stock-Modell vereinheitlichen (`from_body` / Rest-Material)

Fusion: Stock kann das **Ergebnis eines vorherigen Setups** sein → Operationen
raeumen nur weg, was wirklich noch da ist (Rest-Material-Tracking). CAMWOSA
hat `Rohmaterial` (quader/zylinder/platte/frei), aber kein „Stock = vorheriger
Zustand". **Master-Plan A49** (Multi-Setup mit Werkstueck-Transformation)
nennt „optional Rest-Material-Tracking via Voxel zwischen Setups" — genau das.
Die Voxel-Simulation (`cam/simulation.py`) ist die Basis dafuer schon da.

### 🟡 KLEIN — dedizierte `slot` + `trace` Ops

- **slot**: Nut entlang einer offenen Linie mit definierter Breite. CAMWOSA
  macht das ueber `kontur` mit Werkzeug-Versatz, aber eine eigene Op waere
  klarer (gerade fuer Holzverbindungen).
- **trace**: einer Kurve in konstanter Tiefe folgen (Stichel/Drag). CAMWOSA
  hat `gravur` konstante_tiefe + `drag_engraving` (alpha.5) — weitgehend
  abgedeckt.

### 🟡 KLEIN — `coolant` / Absaugung als strukturiertes Feld

Fusion: coolant-Modus pro Op (flood/mist/through_tool). Markus' Welt: keine
Flutkuehlung, aber **Spaeneabsaugung**. `Material.spaeneabsaugung_empfohlen`
existiert schon — koennte als Op-Header-Kommentar in den G-Code (`M7`/`M8`/`M9`
optional, oder nur Klartext-Hinweis).

### 🟢 TECH-DEBT — deterministische Werkzeug-Nummer

Fusion: `tool_number` aus Library. CAMWOSA: `_tool_nummer` per Hash
(STATUS.md Tech-Debt). Ein deterministisches Mapping pro Werkzeug-Name/Slot
waere nutzerfreundlicher beim manuellen Werkzeugwechsel (M6 Txx).

---

## 3. Was CAMWOSA hat, das diese Fusion-MCP NICHT zeigt

Damit klar ist, dass CAMWOSA kein reiner Nachbau ist:

- **v_carving** (Gravur mit variabler Tiefe entlang Medialachse) — Fusion kann's,
  die MCP exponiert es aber nicht.
- **Rotary-Wrap** (2D-Design auf Zylinder, Y→A°) + **Drechseln** (Continuous-Lathe
  mit Fraeser von oben) — CAMWOSAs Rotary-Ansatz ist spezifisch fuer Markus'
  Hardware.
- **Auto-Inlay, Dogbone-Slots, Drag-Engraving** (alpha.4/5) — Hobby/Holz-Spezialitaeten.
- **Bild-zu-Relief-Pipeline** (Heightmap + 6 Filter + optional AI-Tiefe).
- **Z-Grid-Diagnose** (alpha.5) — Pre-Run-Ebenheitscheck.
- **QuickCAM-Templates**, **ArbeitsSchritt-Workflow**, **3-Density-Responsive-UI**.

---

## 4. Empfohlene Master-Plan-Kandidaten

Reihenfolge nach Aufwand/Nutzen. **Noch nichts implementiert — das ist die
Einordnung, Umsetzung nach Absprache (Master-Plan-First).**

| # | Kandidat | Cluster | Aufwand | Nutzen | Synergie |
|---|---|---|---|---|---|
| 1 | **Planfräsen (`face`)** als eigene Op | Vector-Ops | klein (1 Tag) | hoch | Z-Grid-Diagnose-Empfehlung |
| 2 | **3D-Parallel-Schlichten** auf STL/Heightmap | NEU: 3D-Strategien | mittel (2-3 T) | hoch | baut auf `relief` + `waterline` auf |
| 3 | **3D-Adaptive-Schruppen** | NEU: 3D-Strategien | gross (3-4 T) | hoch | erweitert 2D-Adaptive |
| 4 | **3D-Scallop-Schlichten** (Cusp-Height) | NEU: 3D-Strategien | gross (3-4 T) | mittel-hoch | nach 3D-Parallel |
| 5 | **Rest-Material-Stock** (`from_body`) zwischen Setups | A49 | mittel (2 T) | mittel | Voxel-Sim existiert |
| 6 | **slot** als dedizierte Op | Vector-Ops | klein (1 T) | mittel | — |
| 7 | deterministische **Werkzeug-Nummer** | Tech-Debt | klein (0.5 T) | mittel | Multi-WW-Workflow |
| 8 | **coolant/Absaugung** als Op-Feld + G-Code-M7/8/9 | klein (0.5 T) | gering | Material-Flag da |

### Strategische Empfehlung

**Kurzfristig (alpha.6, geringes Risiko):** #1 Planfräsen + #6 slot + #7 Tool-Nr.
Alles Backend mit Tests, kleine in sich geschlossene Wins, decken echte
2.5D-Luecken.

**Mittelfristig (eigener Meilenstein „3D-Frasstrategien"):** #2 → #3 → #4.
Das ist der grosse Hebel, der CAMWOSA von 2.5D+Relief zu echtem 3D bringt.
Braucht Architektur-Entscheidung: arbeiten wir weiter auf Heightmaps
(begrenzt, aber einfach) oder auf echten Mesh/STL-Oberflaechen mit
Surface-Normalen (maechtiger, aber mehr Geometrie-Mathe — ggf. trimesh nutzen,
ist schon Dependency)?

**Bewusst NICHT uebernehmen:**
- `operation_type: turning` (echtes Drehen) — Markus' Hardware kann's nicht
  (Fraeser haengt vertikal). Rotary-Wrap bleibt CAMWOSAs Weg.
- Multi-Post-Prozessoren (fanuc/haas/...) — GRBL-Fokus ist Absicht, Plugin-
  System steht fuer den Bedarfsfall bereit.

---

## 5. Offene Fragen an Markus

1. **3D-Strategien ja/nein?** Das ist der grosse Richtungsentscheid. CAMWOSA
   ist als 2.5D-Tool positioniert — willst du es Richtung echtes 3D-Schlichten
   ausbauen (Figuren, organische Formen, Reliefs in hoher Qualitaet), oder
   bleibt der Fokus auf 2.5D + Relief-as-is?
2. **Heightmap vs. Mesh-Oberflaeche** fuer 3D-Strategien — falls ja zu #1:
   reicht der Heightmap-Ansatz (du arbeitest viel mit Bild-zu-Relief), oder
   brauchst du echtes STL-Surface-Following (Hinterschnitte ausgenommen)?
3. **Planfräsen** zuerst? Das ist der schnellste Win mit klarer Synergie zur
   Z-Grid-Diagnose — gutes Kandidat fuer den naechsten konkreten Schritt.

---

## Anhang — Live-Verifikation (erledigt 2026-05-21)

Gegen die echte Fusion-CAM-API verifiziert (Test-Body + Setup + Operationen
via `execute_code` angelegt, Parameter ausgelesen, danach aufgeraeumt).

**Erkenntnis 1 — die MCP-CAM-Wrapper sind fragil:** `cam_list_setups` /
`cam_create_setup` brechen wenn das aktive Produkt nach einem Workspace-Wechsel
auf CAM steht (`'CAM' object has no attribute 'rootComponent'`). Das CAM-Produkt
muss zudem erst durch einmaligen Wechsel in den Manufacture-Workspace
initialisiert werden (`ui.workspaces.itemById('CAMEnvironment').activate()`).
Fuer robuste Automation ist `execute_code` mit direkter `adsk.cam`-API
zuverlaessiger als die High-Level-cam_*-Tools.

**Erkenntnis 2 — Strategie-IDs:** `parallel_new`, `scallop_new`, `face`,
`contour2d`, `pocket2d`, `bore`, `thread` sind gueltig. `adaptive3d` ist es
NICHT (Fehler „Unknown strategy") — die echte 3D-Adaptive-ID heisst anders
(vermutlich `adaptive` mit 3D-Flag oder `pocket3d`); fuer CAMWOSA irrelevant,
da wir eigene Strategien bauen.

**Erkenntnis 3 — Fusion exponiert ~250-400 Parameter pro Operation.** Die
allermeisten sind Clearance/Retract-Area-Modi, View-Orientation, Multi-Axis-
Tilt, Holder-Clearance — fuer ein GRBL-3-Achs-Hobby-Tool irrelevant. Der
fraesrelevante Kern (gefiltert):

| Fusion-Parameter | gilt fuer | CAMWOSA-Uebernahme |
|---|---|---|
| `tolerance`, `contourTolerance` | alle 3D | ✅ I2 — Bahn-Approximationsfehler |
| `stepover` | parallel/scallop/face | ✅ vorhanden |
| `cuspHeightStepover` | parallel | ✅ I2 — Stepover aus Riefenhoehe |
| `stepover` (= Scallop-Hoehe) | scallop | ✅ I4 |
| `stockToLeave`, `verticalStockToLeave` | alle | ✅ I2 — Aufmass radial+vertikal |
| `passAngle`, `totalPassAngle`, `passReference` | parallel/face | ✅ I2 — Bahn-Winkel |
| `direction`, `upDownMilling` | alle | ✅ vorhanden (fraes_richtung) |
| `machineSteepAreas`, `steepStepdown`, `slopeAngleFrom/To` | parallel | ✅ I3 — Steilheits-Maske |
| `maximumStepdown`, `doMultipleDepths`, `numberOfStepdowns` | face/parallel | ✅ vorhanden (stepdown) |
| `useRestMachining`, `restMaterialPrevious`, `restMaterialStockToLeave` | parallel/scallop | ✅ I6 |
| `boundaryMode`, `machiningBoundarySel`, `boundaryOffset` | parallel/scallop | mid-term — Bearbeitungsgrenze |
| `filletsEnabled`, `smoothingFilter*` | parallel/scallop | mid-term — Bahn-Glaettung |
| `leadInRadius`, `leadOutRadius`, `transitionType` | alle | ✅ vorhanden bei Kontur |
| `stockOffset`, `passExtension`, `bothSides` | face | ✅ I1 — Planfraesen |
| `collapseBisector`, `minimumProfileDiameter` | scallop | I4 — Detail |

**Erkenntnis 4 — Werkzeug-Modell:** Fusion hat ~60 `tool_*`-Parameter inkl.
`tool_segmentHeight/DiameterLower/Upper` (Multi-Diameter-Cutter — hat CAMWOSA
via `segmente`!), `tool_coolant`, `tool_numberOfFlutes`, `tool_cornerRadius`.
CAMWOSAs Werkzeug-Modell deckt den relevanten Teil ab.

**Noch offen (wenn gewuenscht):** `cam_post_process post_processor=grbl` —
Fusions GRBL-Output mit CAMWOSAs Postprozessor vergleichen (Format, Arc-Modus,
Werkzeugwechsel-Syntax).
