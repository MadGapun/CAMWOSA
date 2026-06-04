# CAMWOSA — Tiefen-Analyse 2026-06 (G-code-Qualität, CAM-Lücken, Steuerung)

> Auftrag Markus (2026-06-04): „CAMWOSA in allen Details und den Master-Plan in
> allen Tiefen analysieren, erweitern, optimieren, maximieren, testen, verbessern
> — das Maximum für eine CAM-Software vor allem für meine CNC herausholen, um
> G-code zu erzeugen, und später ggf. eine Steuerung liefern, die den G-code an
> den CNC-Controller schickt (ggf. zwei Apps: CAMWOSA als Server, Steuerung als
> Client)."

Dieses Dokument ist die **Bestandsaufnahme + Priorisierung**. Konkrete neue
Plan-Positionen landen im [Master-Plan](wiki/Master-Plan.md) (Cluster P, Teil G).
Die Steuerung hat ein eigenes Detail-Dokument: [SENDER-ARCHITEKTUR](SENDER-ARCHITEKTUR.md).

---

## 0. Executive Summary

CAMWOSA ist breit (Phasen 1–5 weitgehend fertig, 842 Backend-Tests). Die größten
Hebel liegen **nicht** in „mehr Features", sondern in drei Bereichen:

1. **G-code-Output-Qualität (Cluster P, neu).** Der erzeugte G-code ist
   funktional, aber nicht maschinen-optimal: kein Spindel-Hochlauf-Dwell,
   nicht-modaler Output (jede Zeile wiederholt `F` und alle Achsworte),
   potentiell diagonale Eilgänge. **Das betrifft jede einzelne Datei, die auf
   deiner Genmitsu läuft** → höchster ROI.
2. **Toolpath-Linking & Eintauchen (J4/J5, offen).** Stay-Down statt
   Luft-Hüpfen, Rampen/Bogen-Eintauchen statt senkrechtem Plunge — Standzeit +
   Oberfläche + Zeit.
3. **Steuerung als separate App (Teil G, neu).** Entkoppelt vom CAM, respektiert
   den „Pure-CAM"-Grundsatz (CAMWOSA schiebt nichts selbst).

Der Rest (Anfänger-Schicht Cluster K, Zeichnen D28–D30, Multi-Setup A49) bleibt
wertvoll, ist aber bekannt und im Plan.

---

## 1. G-code-Output-Audit (was real auf der Maschine landet)

Geprüfter Pfad: `gcode/toolpath.py` → `postprocessor/base.py` →
`postprocessor/grbl_standard.py` → `grbl_genmitsu.py`.

### 1.1 Befund-Tabelle

| # | Befund | Schwere | Wirkung |
|---|--------|---------|---------|
| P1 | **Kein Spindel-Hochlauf-Dwell.** `spindle_on()` gibt `M3 S<rpm>` ohne folgendes `G4 P<t>`. | 🔴 hoch | Erster Plunge passiert, bevor die Makita RT0700 (~1–2 s Hochlauf) auf Drehzahl ist → schlechter Erstschnitt, Werkzeug-/Spindel-Last, Stall-Risiko. |
| P2 | **Nicht-modaler Output.** Jede `G1`-Zeile wiederholt `F<feed>` (grbl_standard.py:75) und **alle** Achsworte `X Y Z`, auch wenn unverändert. | 🟠 mittel | Datei 2–3× größer; Z wird auf reinen XY-Zügen wieder gesetzt → Mikro-Jitter durch `:.3f`-Rundung; unübersichtlicher G-code. |
| P3 | **Diagonale Eilgänge möglich.** `rapid_move()` gibt `G0 X Y Z` in **einer** Zeile (base/standard). Wenn eine Eilgang-Bewegung gleichzeitig XY ändert und Z bewegt, fährt die Maschine schräg. | 🟠 mittel | Beim Rückzug: Werkzeug zieht schräg → kann durch Material/Steg schleifen. Bei Anfahrt mit Z-ab: schräger Tauchgang. Abhängig vom Generator. |
| P4 | **Kein explizites `G54`, kein garantierter Start-Sicherheits-Z.** Header setzt G21/G90/G17/G94, aber kein Arbeits-KS und keinen ersten Z-Rückzug. | 🟡 niedrig | Verlässt sich auf GRBL-Default G54 + darauf, dass jeder Toolpath mit Eilgang auf Safe-Z startet. Robustheit. |
| P5 | **Werkzeugwechsel nutzt Stub-Werkzeug.** `post_alle()` ruft `tool_change(ctx, ctx.werkzeug)` mit dem alten Werkzeug (base.py:118, Kommentar gibt das selbst zu). | 🟡 niedrig | Wechsel-Kommentar/RPM beziehen sich aufs falsche Werkzeug. Toolpath trägt RPM aber selbst → Schnitt korrekt, nur Kommentar/Park irreführend. |
| P6 | **`spindle_on` pro Toolpath.** Bei N Operationen mit gleichem Werkzeug N× `M3`. | 🟢 kosmetisch | Redundanz, harmlos. Mit P1-Dwell aber N× Dwell-Zeit verschenkt. |

### 1.2 Beispiel — heute vs. optimiert

**Heute** (Tasche, 4 Linienzüge auf konstantem Z, konstantem Feed):
```
M3 S18000
G0 X10.000 Y10.000 Z5.000
G1 X10.000 Y10.000 Z-1.000 F300
G1 X50.000 Y10.000 Z-1.000 F800
G1 X50.000 Y40.000 Z-1.000 F800
G1 X10.000 Y40.000 Z-1.000 F800
G1 X10.000 Y10.000 Z-1.000 F800
```

**Optimiert** (P1 Dwell + P2 modal):
```
M3 S18000
G4 P2.0            ; Spindel-Hochlauf
G0 X10.000 Y10.000
G0 Z5.000
G1 Z-1.000 F300    ; Plunge mit Plunge-Feed
F800               ; Schnitt-Feed (modal)
X50.000
Y40.000
X10.000
Y10.000
```
Kleiner, sicherer, kein Z-Jitter, Spindel auf Drehzahl vor Erstschnitt.

### 1.3 Maßnahmen → Cluster P (Master-Plan)

- **P1 Spindel-Hochlauf-Dwell** — Feld `hochlauf_sekunden` an Spindel/Maschine (Default 0 = rückwärtskompatibel), `spindle_on()` hängt `G4 P<t>` an.
- **P2 Modal-Kompression** — `gcode/modal.py`: Post-Pass, der redundante Achsworte + Feed + Motion-Wort entfernt (opt-in, dann Default im Export). Endpunkt-treu, kommentar-erhaltend.
- **P3 Rapid-Safety** — `gcode/fahrweg.py`: multi-achsige Eilgänge in sichere Reihenfolge splitten (Z-hoch zuerst beim Rückzug, XY zuerst beim Anfahren). Opt-in.
- **P4 Start-Preamble** — `G54` + erster `G0 Z<safe>` garantiert in `post_alle()` (konfigurierbar).

---

## 2. CAM-Capability-Lücken (priorisiert für GRBL-Hobby/Prosumer)

Was am meisten **G-code-Qualität** bringt (nicht Feature-Zählen):

| Prio | Item | Plan | Warum |
|------|------|------|-------|
| ★★★ | **J5 Lead-in/out + Rampen-Eintauchen** | J5 ⬜ | Senkrechter Plunge ist hart für Fräser in Holz/Alu. Bogen/Rampe = Standzeit + Oberfläche. Gilt für Kontur/Tasche/3D. |
| ★★★ | **J4 Stay-Down / Linking** | J4 ⬜ | Werkzeug unten lassen wenn Weg frei+kurz → weniger Luftzeit, weniger Plunges. |
| ★★☆ | **J8 Trochoidales Nutenfräsen** | J8 ⬜ | Slots in Alu/Hartholz mit Schaftfräser-Ø = klemmen. Trochoidal = konstante Last. |
| ★★☆ | **A42 Vector-Ops vervollständigen** | A42 ⬜ | Cutting-Direction-Feinheiten, Allowance/Skin pro Op, Finishing-Pass-Profile. Teilw. in alpha.11 erledigt. |
| ★★☆ | **A49/M5 Multi-Setup mit Umspannung** | A49 ⬜ | Markus' **häufigster** realer Workflow (Schruppen+Schlichten in einer, dann Umspannen). |
| ★☆☆ | **I5 3D-Adaptive-Schruppen** | I5 ⬜ | Konstanter Eingriff in 3D. Großer Brocken. |
| ★☆☆ | **J6/J7 Flat-Area + Pencil** | J6/J7 ⬜ | 3D-Finish-Qualität. |

### 2.1 GRBL/Genmitsu-spezifische Feinheiten (oft übersehen)

- **Arc-Toleranz `$12`** — GRBL zerlegt G2/G3 in Segmente; sehr kleine Bögen ok. Arc-Fitting (J1 ✅) reduziert Zeilen — gut.
- **Soft-Limits `$20`/`$21`** — wenn aktiv, killt ein Out-of-Range-Move den Job mit Alarm. CAMWOSA prüft Arbeitsraum (Safety ✅), aber sollte die **echten `$130-$132` Achslimits** kennen (Maschinen-Profil hat Arbeitsraum — passt).
- **`$32` Laser-Mode** — bei Laser-Crossover (LightBurn-Zielgruppe!) relevant: M3 vs M4 dynamisch. Für Fräsen aus.
- **Werkzeugwechsel ohne M6** — korrekt als M0-Pause gelöst. Ergänzen: Hinweis „Z neu antasten" im Kommentar (manueller Wechsel verschiebt Z-Null nicht automatisch).
- **Rotary `$101` Remap** — Genmitsu-Header weist schon darauf hin. Gut.

---

## 3. Steuerung / Sender — warum separate App

Der Master-Plan listet (Zeile 273–282) **bewusst** „Direkte Maschinen-Steuerung
→ CNCjs" als *out-of-scope*, und das Memory hält „CAMWOSA schiebt G-code nur als
Datei". Markus' Sender-Wunsch **kippt das nicht**, sondern löst es per Trennung:

- **CAMWOSA bleibt Pure-CAM** (Server): erzeugt G-code, kennt Werkzeuge/Material/
  Strategien. Schiebt **nichts** selbst an einen Controller.
- **Neue, separate App** (Client/Sender): spricht GRBL über USB-Serial, streamt
  G-code, jog/home/probe, Status/Override. Kann auf einem **anderen Rechner**
  (z.B. Pi/Tablet an der Maschine) laufen.
- Kopplung nur **lose**: der Sender lädt `.nc`-Dateien (oder holt sie über eine
  schmale CAMWOSA-HTTP-Schnittstelle). Keine harte Abhängigkeit in CAMWOSA.

So bleibt der alte Grundsatz intakt („CAMWOSA selbst steuert nicht") und der
neue Wunsch erfüllt. Details + Protokoll: [SENDER-ARCHITEKTUR](SENDER-ARCHITEKTUR.md).
Plan: **Teil G** im Master-Plan.

---

## 4. Umsetzungs-Reihenfolge dieser Session

1. **Cluster P** (Postprozessor-Härtung) — P1, P2, P4 sicher, P3 falls Budget. Tests. → größter Sofort-ROI für deine Maschine.
2. **Teil G Doku** — Sender-Architektur als Design-Dokument (Bauen folgt als eigenes Projekt-Inkrement).
3. **J5 Lead-in/out + Rampe**, dann **J4 Stay-Down** — falls Budget.
4. Test + Release alpha.13 + Wiki.

Bewusst **nicht** in dieser Session (zu groß / UI-lastig, separat planen): A49
Multi-Setup-Umspannung-Wizard, Cluster-K-Anfänger-Schicht, D35 UI-Konzepte.
