# CAMWOSA — Wettbewerb, Einstellbarkeit, Workflow-Logik & Piktogramme (2026-06-05)

> Markus' Auftrag: „Hast du alle Workflows analysiert? Was kann/muss man
> einstellen? (CNC vergrößern, Vorschub pro Weg, variable Eintauchgeschwindigkeit
> …) Vergleiche mit anderen Tools (OPUS CAM, GRBL design-tools, Easel …) und
> such weitere. Hat jeder Arbeitsschritt/Workflow eine logische, leicht
> verständliche, **dokumentierte** Abfolge? Sind alle Piktogramme/Grafiken da?"

Dieses Dokument beantwortet diese Fragen ehrlich, mit Quellen, und leitet eine
priorisierte Lücken-Liste ab (→ Master-Plan Cluster Q).

---

## 1. Wettbewerbs-Vergleich (recherchiert)

Quellen u.a.: grbl.org/design-tools, inventables.com Easel, opus-cam.de,
all3dp Estlcam-Guide, Carbide-3D-Community, cncsourced/minimillr/makera-Vergleiche.

| Tool | Klasse | Stärke | Einstellbarkeit | Workflow-Führung | Visuell |
|---|---|---|---|---|---|
| **Easel** (Inventables) | Anfänger, Web, all-in-one (CAD+CAM+Sim+Control) | „in Minuten schnitzen", Material-/Bit-Bibliothek mit Empfehlungen, Maschinen-Profile+Parking | **bewusst grob** (pro Op, kein per-Pfad-Feed) | sehr stark (geführt) | hoch (visuell, Vorschau) |
| **Carbide Create** | Anfänger/Mittel, 2D(+3D Pro), offline, gratis | pro Toolpath: Ø, Schneiden, Tiefe/Pass, Stepover, RPM, **Feed + Plunge** | pro Toolpath | mittel | mittel |
| **Estlcam** | Hobby-Power, CAM **+ Steuerung** | **per-Element** Feed/Tiefe/Tabs/Lead-in, Auto-Strategien + manuell, V-Carve gratis | **fein (per-Kontur)** ← Goldstandard | mittel (auto + manuell) | hoch (Toolpath-Vorschau) |
| **OpenBuilds CAM** | Hobby, Web, gratis | DXF/SVG, einfach | pro Op | mittel | mittel |
| **VCarve (Vectric)** | Prosumer, bezahlt | V-Carve/3D, sehr ausgereift | pro Toolpath + Vektor-Auswahl | stark | hoch |
| **OPUS CAM** | **Industrie** (Bosch/Trumpf), 5-Achs, Drehen, Sim, DNC | Tiefe Werkzeug-/Postproz-Verwaltung, Kollision | sehr fein, aber komplex | aufgabenorientiert | CAD-eng |
| **Fusion 360 CAM** | Profi/Hobby | volle 2.5D/3D, adaptive | sehr fein (pro Op, Lead/Ramp-Feeds) | mittel | hoch |

**Einordnung für CAMWOSA (Dual-Audience):**
- Gegen **Easel/Carbide** (Anfänger): CAMWOSA hat mehr Tiefe, muss aber die
  *Führung* + *visuelle Erklärung* nachziehen (Cluster K + Piktogramme).
- Gegen **Estlcam** (Power): CAMWOSA fehlt **per-Pfad/per-Element-Kontrolle**
  (Feed/Tiefe/Tabs pro Kontur) — Estlcams Kern-Stärke. ← größte funktionale Lücke.
- **Carbide-Insight:** Plunge-Rate darf höher sein, wenn gerampt wird → koppelt
  an unser J5-Rampen-Eintauchen (Plunge-Feed vs. Rampen-Feed trennen).

---

## 2. Einstellbarkeits-Matrix CAMWOSA (Frage „was kann/muss man einstellen?")

### 2.1 Entitäten — alle jetzt UI-editierbar (Stand alpha.15)
| Entität | Editor | Status |
|---|---|---|
| Maschine (Arbeitsraum „CNC vergrößern", Vorschub, Eilgang, Controller, Sicherheitshöhe, WW-Pos, Postproz, Spindel-Zuordnung, Modi) | MaschinenEditor | ✅ |
| Spindel (RPM, VFD-Hochlauf, Spannzange, PWM …) | SpindelEditor | ✅ |
| Werkzeug · Material · Feeds&Speeds-Preset · Rohmaterial · Rotary-Profil | je eigener Editor | ✅ |

### 2.2 Operations-Parameter — pro Operation editierbar (Per-Feature-Override A14b)
`OperationParameter`: `vorschub` (Schnitt-Feed), `eintauch_vorschub` (Plunge-Feed),
`spindel_rpm`, `max_tiefe`, `stepdown`, `sicherheitshoehe`, `freifahrt_hoehe`,
`vorschub_anpassung(+max)`. Pro Op-Typ zusätzlich: Seite, Fräsrichtung,
Eintauchstrategie (senkrecht/rampe/helix), Rampenwinkel, Tabs, Aufmaß,
Schlichtgang, Lead-in/out, Stepover, Adaptive-Parameter, Bohr-Strategien, V-Carve.

→ **Jeder Wert ist pro Operation überschreibbar** (OverrideOperationForm).

### 2.3 LÜCKEN (das, was Markus konkret anspricht)
| Lücke | heute | gewünscht | Aufwand |
|---|---|---|---|
| **Vorschub pro Weg/Geometrie** | Feed gilt für die ganze Operation; mehrere Konturen in einer Op teilen einen Feed | per-Geometrie-Override (Feed/Tiefe/Plunge je Kontur) — Estlcam-Stil | groß (Datenmodell + Generatoren + UI) |
| **Variable Eintauchgeschwindigkeit** | ein `eintauch_vorschub` je Op | getrennter **Plunge-Feed** vs. **Rampen-Feed** (Carbide-Insight); optional tiefen-abhängig | mittel |
| **Override-UI-Abdeckung** | prüfen: sind ALLE Modell-Felder in der Override-Form? (z.B. `rampe_winkel_grad`, `freifahrt_hoehe`, `eintauch_strategie`, Lead-in/out) | jedes Feld erreichbar | klein–mittel (Audit + ergänzen) |
| **Per-Werkzeugwechsel-Strategie pro Schritt** | global | pro Schritt wählbar (Datei/M6/Makro) | klein (teilw. da) |

**Antwort auf „was muss man einstellen können":** Maschine (✅), Spindel (✅),
Werkzeug/Material/Feeds (✅), pro Operation alles (✅). **Offen:** Feinkörnigkeit
*unterhalb* der Operation (pro Pfad) + getrennte Plunge/Rampen-Feeds.

---

## 3. Workflow-Logik-Audit (Frage „hast du alle Workflows analysiert?")

CAMWOSA-Workflows (Code vorhanden):
| Workflow | Modul | Logische Abfolge? | Im System dokumentiert? |
|---|---|---|---|
| **Multi-Setup / ArbeitsSchritt** (Operation/Werkzeugwechsel/Umspann/Achswechsel) | `project/schritte.py`, `workflow/manager.py`, WorkflowView | ✅ klar typisiert, 4 Schritt-Typen | teilw. (Wiki ArbeitsSchritt) — **Ablauf-Diagramm fehlt** |
| **QuickCAM-Templates** (<60 s zum Projekt) | `quickcam/templates.py`, QuickStartView | ✅ | teilw. — **Schritt-für-Schritt-Doku dünn**, Issue #50 (Dead-End) offen |
| **Auto-CAM** (Claude erzeugt Bearbeitung) | `workflow/auto_cam.py`, MCP | ✅ 3 Aufgaben-Typen | Wiki MCP-AutoCAM ✅ |
| **Arbeitsplan-Generator** (Checkliste/PDF) | `workflow/arbeitsplan.py` | ✅ | Wiki Arbeitsplan ✅ |
| **Run-Lock / Dirty-Tracking** („im Zweifel läuft nichts") | `workflow/run_lock.py` | ✅ NEU/OK/DIRTY/BROKEN | Wiki ✅ |
| **G-Code-Schritte / Werkzeugwechsel-Strategie** | `workflow/gcode_schritte.py` | ✅ (Datei/inline M6/Makro) | teilw. |
| **7-Phasen-Anfänger-Reise** (Idee→Datei) | — (K1 ⬜) | **fehlt als durchgehender Faden** | nur Analyse (HOBBY-CAM) |

**Befund:** Die Workflow-*Bausteine* sind logisch + getestet. Was fehlt:
1. **K1 — ein durchgehender geführter Faden** (Idee→Design→Werkzeug→Operation→Sicherheit→G-Code→Maschine), der QuickCAM + Auto-CAM verbindet statt Insel-Templates. ⬜
2. **Sichtbare Ablauf-Diagramme** je Workflow (was kommt nach was, warum) — „leicht verständlich + dokumentiert" ist noch nicht visuell.
3. **Issue #50** (QuickStart-Dead-End: Projekt wird serverseitig erzeugt, lädt aber nicht in die UI-Stores) — bremst den wichtigsten Anfänger-Pfad.

---

## 4. Piktogramm-/Grafik-Audit (Frage „sind alle Piktogramme erzeugt?")

| Bereich | Status |
|---|---|
| **Werkzeug-Grafiken** (12 Typen, bemaßt + Piktogramm) | ✅ `WerkzeugGrafik.tsx` |
| **Operations-Piktogramme** (Kontur=durchschneiden / Tasche=aushöhlen / Bohren / Gravur / Relief) | ❌ fehlen (K2/D37) |
| **Strategie-Icons** (Tasche: parallel/spiral/offset/adaptive · Eintauchen: senkrecht/rampe/helix · Bohren: peck/helix/…) | ❌ fehlen |
| **Innen/Außen/Auf-Linie + Tabs** visuell (statt Dropdown) | ❌ fehlen (K11) |
| **Workflow-/Phasen-Diagramme** | ❌ fehlen |
| **V-Carve / Relief-Illustration** | ❌ fehlen |
| **Sicherheits-/Nullpunkt-Grafik** (K12) | ❌ fehlen |

**Ehrliche Antwort:** Nein — nur die **Werkzeug-Grafiken** sind fertig. Der
große Rest erklärender Grafiken (Operationen, Strategien, Innen/Außen, Tabs,
Workflow-Diagramme) fehlt noch. D37 steht zu Recht auf 🔶.

---

## 5. Priorisierte Lücken → Master-Plan Cluster Q

| Nr | Lücke | Wert | Aufwand |
|---|---|---|---|
| Q1 | **Override-UI-Vollständigkeits-Audit** — jedes Modell-Feld in der Form erreichbar (inkl. eintauch_strategie, rampe_winkel, freifahrt_hoehe, lead-in/out) | hoch | klein |
| Q2 | **Plunge-Feed vs. Rampen-Feed trennen** (variable Eintauchgeschwindigkeit) | hoch | mittel |
| Q3 | **Per-Geometrie-Override** (Feed/Tiefe/Plunge pro Kontur innerhalb einer Op) — Estlcam-Stil | sehr hoch | groß |
| Q4 | **Operations- + Strategie-Piktogramme** (parametrisch wie WerkzeugGrafik) | hoch | mittel |
| Q5 | **Innen/Außen/Tabs visuell** (K11) | mittel | mittel |
| Q6 | **Workflow-Ablauf-Diagramme + K1 geführter Faden** | hoch | groß |
| Q7 | **Issue #50** QuickStart-Dead-End fixen | hoch | mittel |

**Reihenfolge-Empfehlung:** Q1 (schneller Vollständigkeits-Gewinn) → Q4
(Operations-/Strategie-Piktogramme, parametrisch) → Q2 (Plunge/Rampen-Feed) →
Q7 (#50) → Q5 → Q3 (groß) → Q6 (groß).

---

## Quellen
- grbl.org/design-tools · inventables.com/pages/easel · opus-cam.de
- all3dp.com Estlcam Beginner's Guide · community.carbide3d.com (feeds/plunge)
- cncsourced.com / minimillr.com / makera.com / xmake.com CAM-Vergleiche
