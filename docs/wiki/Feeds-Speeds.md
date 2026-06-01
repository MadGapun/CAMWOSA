# Feeds & Speeds Rechner

> **Status:** ✅ Implementiert.
> **Issue:** [#3](https://github.com/MadGapun/CAMWOSA/issues/3)
> **Code:** [backend/camwosa/feeds/rechner.py](../../backend/camwosa/feeds/rechner.py) · **Tests:** [backend/tests/feeds/test_rechner.py](../../backend/tests/feeds/test_rechner.py)

Berechnet aus Material + Werkzeug + Maschine die optimalen Schnittparameter.

## Verwendung

```python
from camwosa.feeds import berechne_feeds_speeds

ergebnis = berechne_feeds_speeds(maschine, werkzeug, material)
print(ergebnis.rpm, ergebnis.vorschub, ergebnis.eintauch_vorschub)
print(ergebnis.schnittgeschwindigkeit_vc, ergebnis.spanvolumen_q)
for w in ergebnis.warnungen:
    print(w.stufe, w.text)
```

## Berechnungs-Reihenfolge

1. **Preset suchen:** Wenn fuer das Werkzeug ein Preset im Material hinterlegt ist, wird dieses verwendet.
2. **Heuristik:** Sonst aus interner fz-Tabelle (Zahnvorschub) berechnen.
3. **Maschinen-Limits:** RPM und Vorschub werden auf Maschinen-Min/Max gedeckelt.
4. **Material-Range-Check:** Wenn berechnete Vc ausserhalb der Material-Empfehlung liegt -> Warnung.
5. **Werkzeug-Sicherheit:** Sehr kleine Werkzeuge bei hohem Vorschub -> kritische Warnung.

## Formeln

```
Vc = pi * D * n / 1000           # Schnittgeschwindigkeit (m/min)
Vf = fz * z * n                  # Vorschub (mm/min)
Q  = ap * ae * Vf / 1000         # Spanvolumen (cm3/min)

D  = Werkzeug-Durchmesser (mm)
n  = Spindeldrehzahl (RPM)
fz = Zahnvorschub (mm/Zahn)
z  = Anzahl Schneiden
ap = Schnitttiefe (mm)
ae = seitliche Zustellung (mm)
```

## Heuristik-Tabelle (fz)

Wenn fuer eine Material-Werkzeug-Kombination kein Preset existiert, greift folgende Default-Tabelle:

| Material | Werkzeug | fz @ D=3 | fz @ D=6 | fz @ D=8 |
|----------|----------|----------|----------|----------|
| Holz | Schaftfraeser | 0.04 | 0.06 | 0.08 |
| Holz | Kugelfraeser | 0.03 | 0.05 | — |
| Holzwerkstoff | Schaftfraeser | 0.05 | 0.07 | 0.09 |
| Kunststoff | Schaftfraeser | 0.05 | 0.07 | 0.08 |
| Kunststoff | Einschneider | 0.10 | 0.12 | — |
| NE-Metall | Schaftfraeser | 0.025 | 0.04 | 0.05 |
| NE-Metall | Einschneider | 0.04 | 0.06 | — |

## Warnungen

| ID (implizit) | Stufe | Bedingung |
|---------------|-------|-----------|
| Maschinen-Vorschub-Limit | WARNUNG | Vorschub > Maschinen-Max |
| Sicherer-Vorschub | INFO | Vorschub > sicherer_vorschub |
| RPM ueber Max | WARNUNG | RPM > Maschinen-Max (begrenzt) |
| RPM unter Min | WARNUNG | RPM < Maschinen-Min (angehoben) |
| Vc ueber Material-Max | WARNUNG | Werkzeug ueberhitzt evtl. |
| Vc unter Material-Min | INFO | Werkzeug rubbelt evtl. |
| Werkzeug-Bruch-Risiko | KRITISCH | D<1.5 + Vorschub>1500 |

## MCP-Aufruf

```
mcp.call("feeds_speeds_berechnen", maschine_id="genmitsu_proverxl_4030_v2",
         werkzeug_id="schaft_6mm_2s_hm", material_id="buche_massiv")
```

## Vorschub-Anpassung bei Teil-Tiefe (J11)

Der berechnete Vorschub gilt für die **volle Zustellung** (`stepdown`). Pässe
mit geringerer axialer Tiefe (letzter Rest-Pass, prozentuale Tiefen) können
schneller gefahren werden. Helfer:

```python
from camwosa.feeds.rechner import vorschub_fuer_zustellung
# Vorschub für vollen Stepdown 3 mm, aktueller Pass nur 1 mm tief:
vorschub_fuer_zustellung(800, ap_aktuell_mm=1.0, stepdown_nominal_mm=3.0)  # → 1600 (gedeckelt)
```

`vorschub_eff = vorschub · min(stepdown/ap, faktor_max)`, Default-Deckel 2.0.
Pro Operation über `vorschub_anpassung=true` / `vorschub_anpassung_max`.
Details: [Fahrweg-Optimierung](Fahrweg-Optimierung.md).

## Verwandt

- [Material-Datenbank](Material-Datenbank.md)
- [Werkzeug-Bibliothek](Werkzeug-Bibliothek.md)
- [Fahrweg-Optimierung](Fahrweg-Optimierung.md) (J9/J10/J11)
- [Datenmodell](Datenmodell.md) (SchnittParameterPreset)
