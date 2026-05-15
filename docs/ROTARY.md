# CAMWOSA — Rotary-Achse (4. Achse)

> Stand: 15.05.2026 · Status: Konzept · Geplant für Phase 3+

Detail-Spezifikation für die Rotary-Achs-Unterstützung. Mittelfristiges Ziel: DeskProto vollständig durch CAMWOSA ersetzen.

---

## Ausgangslage (Markus' Setup)

Die Genmitsu ProVerXL 4030 V2 kann zwischen 3-Achs- und Rotary-Modus umgeschaltet werden:

| Aspekt | 3-Achs-Modus | Rotary-Modus |
|---|---|---|
| Y-Achse Steuerung | Linear (40 steps/mm) | Drehachse via Y-Pin |
| GRBL-Setting `$101` | 400 (steps/mm Y) | 88.889 (steps/deg Y) |
| GRBL-Setting `$131` | 300 (max Y) | 9999 (kein Limit) |
| Werkstückform | Quader/Platte | Zylinder |
| Umschaltung | CNCjs-Macros ROTARY EIN / ROTARY AUS | (bereits vorhanden) |

### Implikation für CAMWOSA

Der Mode-Wechsel ist eine **GRBL-Konfiguration**, nicht Software-seitig. CAMWOSA muss diesen Umstand abbilden indem es zwei Modi unterscheidet und der Nutzer den passenden auswählt **bevor** er Operationen anlegt.

---

## Architektur-Ansatz

### Maschinen-Profil mit Modi

Statt zwei getrennter Profile gibt es **ein Profil mit Modi**:

```yaml
Maschine: Genmitsu ProVerXL 4030 V2
Modi:
  - Standard (XYZ)
      Arbeitsraum: 400 x 400 x 110 mm
      Post-Prozessor: grbl_genmitsu_xyz
  - Rotary (XZ + A via Y)
      Werkstueck-Geometrie: Zylinder
      Max Durchmesser: 110 mm (Z-Hoehe ergibt Werkzeug-Reichweite)
      Max Laenge: 400 mm (X-Achse)
      Achsen-Mapping: A-Achse -> Y-Pin
      $101: 88.889 steps/deg
      Post-Prozessor: grbl_genmitsu_rotary_y
```

Der Nutzer **wählt den Modus pro Projekt**. Die Auswahl bestimmt:
- Welche Operationen verfügbar sind
- Welcher Post-Prozessor verwendet wird
- Wie das Rohmaterial definiert wird
- Welche Sicherheits-Checks greifen

### Visueller Hinweis

Wenn ein Projekt im Rotary-Modus ist, zeigt die UI eine deutliche **rote Banner-Markierung**: "ROTARY-MODUS — Maschine muss umgeschaltet sein". So vergisst niemand den Modus-Wechsel an der Maschine.

---

## Rohmaterial im Rotary-Modus

Statt Quader/Platte: **Zylinder** als Rohmaterial.

**Eingaben:**
- Durchmesser (mm) — bestimmt initial Material-Außenradius
- Länge (mm, X-Richtung) — Material-Länge auf der Drehachse
- Spannmittel-Position links/rechts (Futter, Reitstock, beides)
- Welcher Bereich darf nicht bearbeitet werden (Spannfutter-Zone)

**Ausrichtung:**
- X-Achse = Längsachse des Werkstücks
- Z-Achse = radial nach außen
- A-Achse (auf Y gemappt) = Rotation um X

---

## Bearbeitungsoperationen für Rotary

### 4-Achs Indexing (einfacher, Phase 3)

Das Werkstück wird in **diskrete Winkelpositionen** gedreht, dann wird wie bei 2.5D bearbeitet. Klassisches "Multi-Side-Machining".

**Use Case:** Säule mit 8 Gravuren rundum
- Operation 1: 0° drehen, Gravur ausführen
- Operation 2: 45° drehen, Gravur ausführen
- ... usw.

**Operationen verfügbar:** Kontur, Tasche, Bohren, Gravur — jeweils auf einer "abgewickelten" 2D-Fläche.

### Wrapping (Phase 3)

Eine flache 2D-Zeichnung wird auf die Zylinder-Oberfläche **gewickelt**. Klassisch: Schrift rundherum.

**Eingaben:**
- 2D-Geometrie (DXF oder gezeichnet)
- Auf welchen Durchmesser wird gewickelt
- Start-Winkel

**Output:** A-Achs-Bewegungen statt Y-Bewegungen — der Toolpath dreht das Material, statt das Werkzeug zu verschieben.

### Drechseln (Phase 4)

Klassische Dreh-Operationen — Werkstück dreht kontinuierlich, Werkzeug fährt X/Z.

**Operationen:**
- Plandrehen (Stirnseite)
- Längsdrehen (Außenkontur)
- Eintauchen / Einstechen
- Konturen mit Form-Stahl

**Use Case:** Lotusschalen, Vasen, Kerzenständer, Schalen.

### Spirale / Helix (Phase 4)

Werkstück dreht, X-Achse fährt synchron — erzeugt Schraubenlinien.

**Use Case:** Schraubgewinde, dekorative Spiralen.

---

## Post-Prozessor: GRBL Rotary

Eigener Post-Prozessor `grbl_genmitsu_rotary_y.py`:

### Besonderheiten

- A-Achs-Bewegungen werden als Y-Bewegungen ausgegeben (weil GRBL keine echte A-Achse hat, sondern Y umgemappt ist)
- Drehrichtung beachten (CW/CCW analog zum DeskProto-Postprocessor)
- Vorschub-Berechnung bei Rotary: Vorschub am Werkstück-Radius umrechnen
- Header informiert: "; ROTARY-MODUS — bitte GRBL-Setting prüfen ($101=88.889)"

### Vorschub-Korrektur

Bei Linear-Vorschub (mm/min) am Werkstück-Radius gilt:
```
A_Vorschub_deg/min = Linear_Vorschub_mm/min × 360 / (2 × π × Radius)
```

Beispiel: 1000 mm/min Schnittgeschwindigkeit am Radius 30 mm =
```
1000 × 360 / (2 × 3.14159 × 30) = 1909 deg/min
```

Der Postprozessor rechnet das pro Bewegung um.

---

## Sicherheits-Checks für Rotary-Modus

Zusätzlich zu den Standard-Checks:

- **Werkstück-Durchmesser-Check:** Toolpath geht nicht in Bereiche unterhalb des Werkstück-Durchmessers (Werkzeugbruch)
- **Spannfutter-Check:** Toolpath fährt nicht in die definierte Spannfutter-Zone
- **A-Achs-Grenzen:** Bei Profilen mit A-Achs-Limit (hier: kein Limit dank $131=9999)
- **Modus-Hinweis:** Beim Export prominenter Hinweis: "GRBL im Rotary-Modus? ($101 prüfen)"

---

## Workflow im Rotary-Modus

```
1. Projekt anlegen
   └─> Maschine: ProVerXL 4030 V2
   └─> Modus: ROTARY (Banner-Warnung erscheint)

2. Rohmaterial definieren
   ├─> Zylinder: Durchmesser 60mm, Länge 200mm
   ├─> Spannfutter links: 30mm Zone
   └─> Material: Buche

3. Geometrie erstellen
   ├─> 2D-Geometrie wickeln (für Gravur)
   ├─> ODER: Indexing-Positionen anlegen (für Multi-Side)
   └─> ODER: Drechsel-Kontur zeichnen (Phase 4)

4. Operationen wie gehabt
   └─> Postprozessor automatisch grbl_genmitsu_rotary_y

5. Sicherheits-Check
   └─> Bestätigen dass GRBL im Rotary-Modus läuft

6. G-Code exportieren
   └─> Header mit Warnung
   └─> CNCjs öffnen, ROTARY EIN ausführen falls noch nicht aktiv
   └─> Job starten
```

---

## DeskProto-Ablösung — Migrations-Strategie

DeskProto liefert heute den Rotary-G-Code für die ProVerXL. Damit CAMWOSA es ersetzen kann:

| DeskProto-Feature | CAMWOSA-Aequivalent | Phase |
|---|---|---|
| STL auf Zylinder wickeln | Wrapping + STL-Import | Phase 3 |
| Schichtweises Abdrehen | Drechsel-Roughing | Phase 4 |
| Schlicht-Strategien | Drechsel-Finishing | Phase 4 |
| GRBL-Rotary-Postprocessor | grbl_genmitsu_rotary_y | Phase 3 |
| Y-Mapping zur A-Achse | im Postprozessor | Phase 3 |
| Stepover in Grad | Operations-Parameter | Phase 3 |

**Hilfreich für Migration:** Vorhandene DeskProto-Projekte als Referenz nutzen — gleiche Werkstücke einmal mit DeskProto, einmal mit CAMWOSA fräsen und Ergebnisse vergleichen.

---

## Offene Themen

- Wie wird der Modus-Wechsel an der Maschine validiert? (Manuell vom Nutzer bestätigt, automatische Erkennung wäre besser, aber GRBL bietet das nicht)
- Wie sieht die Visualisierung im Rotary-Modus aus? (Material als 3D-Zylinder, Werkzeug rotiert um es)
- Soll CAMWOSA die CNCjs-Macros ROTARY EIN/AUS automatisiert auslösen? (Über CNCjs-API möglich, aber Komplexitäts-Erhöhung)

---

> Letztes Update: 15.05.2026
> Autor: Markus Birzite & Claude
> An <b>ELWOSA</b> Project
