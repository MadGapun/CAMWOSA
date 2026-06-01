# Fahrweg-Optimierung (intelligente Fahrwege)

> Cluster **J9/J10/J11**, Issue [#52](https://github.com/MadGapun/CAMWOSA/issues/52) — Markus' Anforderung: „intelligente Fahrwege, möglichst kurze Zeit, Freifahrten knapp über der Geometrie, und der Vorschub soll sich anpassen, wenn nur Teil-Tiefen gefahren werden."

CAMWOSA optimiert die Verfahrwege **nach** der Toolpath-Erzeugung, als eigener
Post-Processing-Schritt (analog zum Arc-Fitting). Das hält die Operations-
Algorithmen einfach und macht die Optimierung **opt-in** und **konservativ**:
greift eine Optimierung bei unerwarteter Struktur nicht, bleibt der Original-
Toolpath unverändert — sie macht den G-Code also nie schlechter.

Modul: `backend/camwosa/gcode/fahrweg.py` · Tests: `tests/gcode/test_fahrweg.py`

---

## J9 — Kurze Wege (Reihenfolge-Optimierung)

Bei mehreren Schnitt-Gruppen (mehrere Konturen, viele Bohrungen, Tasche-Inseln)
bestimmt die **Reihenfolge** der Gruppen, wie weit das Werkzeug im Eilgang
„leer" fährt. CAMWOSA sortiert die Gruppen per **Nearest-Neighbor** um: vom
aktuellen Punkt wird immer die nächstgelegene noch offene Gruppe als nächstes
angefahren.

- **Eingabe:** ein Toolpath, zerlegt in `[Anfahrt-Rapids, Schnitt-Gruppen, Schluss-Rapids]`.
  Eine Schnitt-Gruppe ist ein zusammenhängender Lauf von Nicht-Eilgang-
  Bewegungen (Plunge/Linear/Bogen); die Eilgänge dazwischen sind reine
  Repositionierung und werden neu berechnet.
- **Ergebnis:** dieselben Schnitte, aber in kürzerer Reihenfolge, neu verbunden
  mit Repositionier-Eilgängen auf Sicherheitshöhe.
- **Konservativ:** bei weniger als 2 Gruppen passiert nichts.

Beispiel: drei Bohrungen bei X=0, X=100, X=10. Naiv `0 → 100 → 10` fährt 190 mm
Eilgang in X; optimiert `0 → 10 → 100` nur 100 mm.

```python
from camwosa.gcode.fahrweg import optimiere_reihenfolge, eilgang_weg
tp2 = optimiere_reihenfolge(tp, start=(0, 0))
print(eilgang_weg(tp), "→", eilgang_weg(tp2))  # weniger Eilgang-Weg
```

`eilgang_weg(toolpath)` liefert den gesamten Eilgang-Verfahrweg in mm — die
Metrik, an der die Optimierung gemessen wird.

---

## J10 — Knappe Freifahrten über der Geometrie

Standardmäßig fährt jeder Zwischen-Eilgang auf volle **Sicherheitshöhe** über
dem Rohling hoch. Wenn die schon bearbeitete Geometrie aber viel niedriger ist
als der Rohling, ist das verschenkte Zeit. J10 senkt die **Zwischen**-Eilgänge
auf eine knappe, einstellbare **Freifahrt-Höhe** dicht über der Geometrie.

- Die **erste Anfahrt** und der **letzte Rückzug** bleiben immer auf voller
  Sicherheitshöhe — sicheres Eintauchen ins / Verlassen des Werkstücks.
- Nur Eilgänge **zwischen** dem ersten und letzten Schnitt, die auf/über
  Sicherheitshöhe liegen, werden auf `freifahrt_hoehe` gesenkt.
- Ist `freifahrt_hoehe >= sicherheitshoehe`, passiert nichts.

```python
from camwosa.gcode.fahrweg import senke_freifahrten
tp2 = senke_freifahrten(tp, freifahrt_hoehe=1.0)  # 1 mm über Geometrie
```

> ⚠️ Die Freifahrt-Höhe gilt über der **vorhandenen Geometrie**. Auf einer
> unebenen 3D-Oberfläche sollte sie mit Reserve gewählt werden — CAMWOSA senkt
> hier pauschal auf eine feste Höhe, prüft (noch) nicht pro Position gegen ein
> Höhenmodell.

---

## J11 — Vorschub-Anpassung bei Teil-Tiefe

Der eingestellte Vorschub ist für die **volle Zustellung** (`stepdown`)
kalibriert. Wird ein Pass mit geringerer axialer Tiefe gefahren — z.B. der
letzte Rest-Pass oder bei prozentualen Tiefen — ist das Werkzeug überdimensio-
niert belastet bzw. unterfordert: man kann **schneller** fahren.

CAMWOSA skaliert den Vorschub proportional zum Verhältnis Soll-/Ist-Zustellung,
gedeckelt:

```
vorschub_effektiv = vorschub · min(stepdown / ap, faktor_max)
```

- `ap` = tatsächliche axiale Zustellung dieses Passes
- `faktor_max` = Deckel (Default 2.0, einstellbar 1.0–5.0 über `vorschub_anpassung_max`)
- Bei `ap >= stepdown` bleibt der Vorschub unverändert (kein Über-Boosten).

Aktiviert wird das pro Operation über `vorschub_anpassung = true`. Verdrahtet in
Kontur- und Tasche-Pass-Erzeugung; Helfer: `feeds.rechner.vorschub_fuer_zustellung()`.
Das wirkt sich auch direkt auf die **Bearbeitungszeit-Schätzung** (K5) aus.

Siehe auch: [Feeds & Speeds](Feeds-Speeds.md).

---

## Zusammenspiel & Aktivierung

Im Postprozessor-Aufruf (`POST /api/operations/postprocess`):

```jsonc
{
  "maschine_id": "...",
  "werkzeug_id": "...",
  "toolpaths": [ /* ... */ ],
  "fahrweg_optimierung": true,   // J9: Reihenfolge
  "freifahrt_hoehe": 1.0         // J10: knappe Freifahrt (mm), optional
}
```

Die Convenience-Funktion `optimiere_fahrwege(tp, reihenfolge=True, freifahrt_hoehe=1.0)`
kombiniert J9 + J10. J11 sitzt eine Stufe früher (in der Toolpath-Erzeugung) und
ist über die Operations-Parameter (`vorschub_anpassung`) gesteuert.

Auch über den **MCP-Server** verfügbar: `gcode_erzeugen(..., fahrweg_optimierung=True, freifahrt_hoehe=1.0)`.

---

## Was noch offen ist

- **Positionsgenaue Freifahrt** gegen ein Höhenmodell (statt pauschaler Höhe) —
  relevant für 3D-Reliefs.
- **Reihenfolge über Operationen hinweg** (aktuell pro Toolpath/Operation).
- Travelling-Salesman statt Nearest-Neighbor bei sehr vielen Bohrungen
  (Nearest-Neighbor ist gut genug und schnell; 2-opt als spätere Verbesserung).
