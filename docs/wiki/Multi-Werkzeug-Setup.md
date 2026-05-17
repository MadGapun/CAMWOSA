# Multi-Werkzeug-Setup (Schruppen + Schlichten)

> **Status:** ✅ Backend (Schritt-Liste + G-Code-Bloecke + WW-Strategien) + Frontend-Editor.
> **Code:** [project/schritte.py](../../backend/camwosa/project/schritte.py), [workflow/gcode_schritte.py](../../backend/camwosa/workflow/gcode_schritte.py), [frontend/src/editor/SchrittListeEditor.tsx](../../frontend/src/editor/SchrittListeEditor.tsx)
> **Tests:** [test_gcode_schritte.py](../../backend/tests/workflow/test_gcode_schritte.py)

Der haeufigste reale Workflow auf einer Hobby-CNC ist: **Schruppen mit groesserem Werkzeug, dann Schlichten mit kleinerem Werkzeug — alles in derselben Aufspannung**. Das Werkstueck bleibt eingespannt, nur das Werkzeug wechselt.

## Drei G-Code-Strategien fuer den Werkzeugwechsel

Pro Werkzeugwechsel-Schritt waehlbar:

| Strategie | Verhalten | Wann nutzen |
|-----------|-----------|-------------|
| `separate_datei` (Default) | An der Stelle wird der bisherige G-Code-Job beendet. Es entsteht eine zweite (dritte ...) Datei. CNCjs laedt sie nacheinander. | Sicher fuer GRBL ohne ATC. Typisch fuer Schruppen+Schlichten. |
| `inline_m6` | Alles bleibt ein G-Code mit ``M6 T<n>`` + ``M0`` an der Stelle — User wechselt, drueckt Resume. | Wenn der Sender (CNCjs) das verarbeiten kann und man nicht zwei Files laden will. |
| `inline_makro` | Ruft ein CNCjs-Makro auf (z.B. `TOOLCHANGE_PROBE`). | Wenn nach dem Wechsel automatisch Z-Probe gemacht werden soll. |

Zusaetzlich gibt es `z_probe_nach_wechsel: bool` — falls aktiv, wird bei `inline_m6` direkt nach M6 ein `G38.2` eingefuegt.

## Schritt-Liste — Beispiel

```
1. ⚙ Operation: Tasche Schruppen      (Werkzeug: 6mm Schaftfraeser)
2. 🔧 Werkzeugwechsel (separate_datei) → 2mm Schaftfraeser
3. ⚙ Operation: Tasche Schlichten     (Werkzeug: 2mm)
```

Beim Export entstehen 2 Dateien:
- `setup_01_b01_6mm-fraeser.nc` (Schruppen)
- `setup_01_b02_2mm-fraeser.nc` (Schlichten)

Beide nutzen denselben Nullpunkt. Der User laedt nacheinander.

## Frontend-Editor

Der SchrittListeEditor zeigt die Schritte als sortierbare Liste mit:
- Drag/Verschieben (▲▼)
- Aktiviert-Checkbox (deaktivierte Schritte werden ignoriert)
- Aufklappbare Detailansicht je Schritt
- „Aktives Werkzeug danach" pro Schritt — damit man immer sieht, mit welchem Werkzeug der naechste Schritt laeuft

## ManualNC mitten in der Sequenz

Beispiel mit Vakuum + Spindel-Warmlauf:

```
1. {} Manual G-Code: M62 P0 ; Vakuum AN
2. {} Manual G-Code: M3 S18000 \n G4 P30 ; 30s warmlaufen
3. ⚙ Operation: Tasche
4. {} Manual G-Code: M63 P0 ; Vakuum AUS
```

ManualNC-Bloecke werden 1:1 in den G-Code geschrieben. Mit `sicher_anfahren=true` faehrt der Postprozessor erst auf Sicherheitshoehe, bevor er die Zeilen schreibt.

## Verwandt

- [ArbeitsSchritt](ArbeitsSchritt)
- [Workflow-Modul](Workflow-Modul)
- [Postprozessor-GRBL](Postprozessor-GRBL)
