# Maschine: Genmitsu ProVerXL 4030 V2

> **Status:** ✅ Primaere Test- und Referenzmaschine.
> **Profil:** [data/machines/genmitsu_proverxl_4030_v2.json](../../data/machines/genmitsu_proverxl_4030_v2.json)
> **Maschinen-ID:** `genmitsu_proverxl_4030_v2`

CAMWOSA wird auf der Genmitsu ProVerXL 4030 V2 entwickelt und getestet. Alle G-Code-Outputs, Sicherheits-Checks und Postprozessor-Defaults sind gegen dieses Geraet validiert.

## Technische Daten

| Aspekt | Wert |
|--------|------|
| Hersteller / Modell | Genmitsu / ProVerXL 4030 V2 |
| Arbeitsraum | 400 × 400 × 110 mm |
| Controller | GRBL 1.1 (auf USB-Modul) |
| Max. Vorschub | 3000 mm/min |
| Sicherer Vorschub | 2000 mm/min (empfohlen fuer Standard-Holz) |
| Eilgang | 5000 mm/min |
| Modi | `standard_xyz`, `rotary_y` (3,5-Achs) |
| Postprozessor | `grbl_genmitsu` (Default) / `grbl_genmitsu_rotary_y` |
| Werkzeugwechsel-Park | X=0, Y=0, Z=100 |

## Verfuegbare Spindeln in diesem Profil

Das mitgelieferte Profil enthaelt **zwei** Spindeln — die OEM-Spindel + die haeufigste Upgrade-Wahl:

| Spindel | Typ | RPM | Leistung | Anmerkung |
|---------|-----|-----|----------|-----------|
| **Genmitsu Router 710W** (`genmitsu_router_710w`) | manuell | 10000–30000 | 710 W | OEM, kommt mit der Maschine |
| **Makita RT0700C** (`makita_rt0700`) | manuell | 10000–30000 | 710 W | klassisches Upgrade (Markus' aktive Wahl) |

Beide sind manuell — d.h. Drehzahl wird am Geraet eingestellt, der Postprozessor schreibt nur `M3 S<rpm>` als Plausibilitaets-Marker.

**Eigene Spindel hinzufuegen:**
1. Spindel in `data/spindles/` anlegen (siehe [Spindel](Spindel))
2. In Maschinen-Profil unter `spindel_ids` ergaenzen
3. Ggf. `aktive_spindel_id` aendern

## Rotary-Setup (3,5-Achs)

Die ProVerXL kann mit einem Rotary-Aufsatz (Genmitsu Original oder DIY) zur 3,5-Achse umgebaut werden. Dabei:

- Y-Achse wird **durch** die Drehachse ersetzt (keine echte 4. Achse)
- GRBL-Settings: `$101=88.889` (steps/grad), `$131=9999` (Y-Limit deaktivieren)
- Werkzeug-Macros `ROTARY EIN` / `ROTARY AUS` in CNCjs zum Umschalten
- CAMWOSA-Postprozessor `grbl_genmitsu_rotary_y` schreibt entsprechende Header-Hinweise und Y-Werte in Grad

Details: [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary).

## Profil ueber MaschinenView nutzen

1. Bei App-Start ist die ProVerXL als Default verfuegbar
2. In **ProjektView** waehlen → Spindel-Dropdown listet beide Spindeln (Makita default)
3. Operationen rechnen automatisch gegen die aktive Spindel-RPM-Range

## Sharing mit anderen ProVerXL-Usern

Das Profil ist als JSON-Bundle exportierbar (Button **📦 Bundle** in MaschinenView). Du bekommst eine portable Datei mit Maschine + beiden Spindeln in einem Stueck.

Wenn du das Profil anpasst (z.B. nur eine bestimmte Spindel oder Custom-Settings), kannst du das modifizierte Bundle teilen — andere User importieren es einfach.

Empfohlen: Community-Beitraege als PR in `data/machines/community/` und `data/spindles/community/`.

## Bekannte Eigenheiten

- **GRBL kennt kein M6**: Werkzeugwechsel wird als `M5` + `G0 Z<safe>` + `G0 X0 Y0` + Kommentar + `M0` (Pause) realisiert.
- **GRBL kennt kein G81/G83**: Bohrzyklen werden als Folge G0/G1 ausgegeben (siehe [Operation-Bohren](Operation-Bohren)).
- **Soft-Limits aktiv**: bei Toolpath-Verletzung schaltet GRBL den Motor ab — der Sicherheits-Check warnt **vor** dem Export.
- **CNCjs als Steuerungs-Software**: CAMWOSA macht **Pure CAM**, kein Job-Send. Erzeugte `.nc`-Datei in CNCjs laden.

## Fotos / Setup

(Folgt — siehe [Living Wiki-Issue #15](https://github.com/MadGapun/CAMWOSA/issues/15).)

## Verwandt

- [Maschinenprofil-Format](Maschinenprofil-Format)
- [Spindel](Spindel)
- [Postprozessor-GRBL-Genmitsu](Postprozessor-GRBL-Genmitsu)
- [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary)
- [docs/ROTARY.md](../ROTARY.md)
