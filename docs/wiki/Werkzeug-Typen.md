# Werkzeug-Typen

> **Status:** ✅ Wiki + Modell-Audit (A41).
> **Code:** [backend/camwosa/db/models.py](../../backend/camwosa/db/models.py)
> **Master-Plan:** A41

Ueberblick aller 12 Werkzeug-Typen die CAMWOSA unterstuetzt — mit
ASCII-Skizze, Anwendungsfall, Pflicht-Parametern und Verwandte.

## Schnellnavigation

| Typ | Form | Hauptanwendung |
|-----|------|---------------|
| [SCHAFTFRAESER](#schaftfraeser) | Zylinder flach | Standard fuer Kontur/Tasche |
| [KUGELFRAESER](#kugelfraeser) | Halbkugel-Spitze | 3D-Reliefs, glatte Oberflaechen |
| [TORUSFRAESER](#torusfraeser) | Flach + Eckenradius | Schruppen + Schlichten |
| [V_BIT](#v_bit) | Konisch spitz | V-Carving, Schrift |
| [BALLNOSE_V_BIT](#ballnose_v_bit) | Konisch mit Mini-Kugel | Robuste Reliefs |
| [GRAVIERSTICHEL](#gravierstichel) | Sehr fein konisch | Beschriftung |
| [BOHRER](#bohrer) | Spiral mit Spitzenwinkel | Loch-Bohren |
| [EINSCHNEIDER](#einschneider) | Zylinder mit 1 Schneide | Sauberer Schnitt in Holz |
| [FISCHSCHWANZ](#fischschwanz) | Zylinder mit Plunge-Spitze | Plunge ohne Vorbohren |
| [SCHRUPPFRAESER](#schruppfraeser) | Zylinder mit Rauh-Profil | Schnelles Material-Wegnehmen |
| [DIAMANTGRAVIERER](#diamantgravierer) | Sehr feine Diamant-Spitze | Edelstahl-Gravur |
| [DRAG_GRAVIERER](#drag_gravierer) | Feder-Diamant (M5) | Drag-Engraving Aluminium |

---

## SCHAFTFRAESER

Standard-Endmill. Zylinder-Schneide, flacher Boden.

```
    │   │     ← Schaft (im Collet)
    │   │
   ┌┴───┴┐
   │     │   ← Flute (Schneide)
   │     │
   │  ━━━│   ← Schneidlaenge
   │     │
   └─────┘   ← flacher Boden (Stirnschneide)
   ↑     ↑
   └─Ø──┘    Durchmesser
```

**Pflichtfelder:** durchmesser, schaft_durchmesser, schneidlaenge, gesamtlaenge, schneiden

**Anwendung:** 
- Kontur-Fraesen (Innen/Aussen)
- Taschen (Pocketing)
- 2.5D Hauptarbeit
- Begrenzt: kein direktes Plunge (toter Mittelpunkt), braucht Helix-Eintauch

**Empfehlungen:** Holz mit 2 Schneiden, NE-Metall 1-2 Schneiden, Acryl 1 Schneide (sonst schmilzt).

---

## KUGELFRAESER

Halbkugel-Spitze. Auch „Ball nose" oder „Ballnose End Mill".

```
    │   │
   ┌┴───┴┐
   │     │
   │     │
   │     │
   └─╲ ╱─┘   ← Halbkugel
      ●
```

**Pflichtfelder:** durchmesser, schaft_durchmesser, schneidlaenge, gesamtlaenge, schneiden

**Anwendung:**
- 3D-Reliefs (glatte Oberflaechen)
- Schlichten von gekruemmten Flaechen
- Verrundete Innen-Ecken

**Empfehlungen:** Stepover 5-15% fuer Schlichten, sonst sichtbare „Cusps" (Riefen).

---

## TORUSFRAESER

Flach mit abgerundetem Eckenradius. Auch „Bull nose cutter".

```
    │   │
   ┌┴───┴┐
   │     │
   │     │
   │     │
   └╮___╭┘   ← flacher Boden mit Eckenradien
    ↑   ↑
    Eckenradius
```

**Pflichtfelder:** durchmesser, schaft_durchmesser, schneidlaenge, gesamtlaenge, schneiden, **spitzenradius** (Eckenradius)

**Anwendung:**
- Schruppen mit weniger Vibration (Eckenradien sind stabiler als scharfe Ecken)
- Fasen + 3D-Oberflaechen
- Kompromiss zwischen Schaftfraeser (flach) und Kugelfraeser (rund)

**Empfehlungen:** Eckenradius 0.5-2 mm typisch, bei groesseren Werkzeugen ueber 6 mm Eckenradius bis 3 mm.

---

## V_BIT

Konisch zugespitzt, Punkt am Ende. Klassischer V-Carve-Bit.

```
    │   │
   ┌┴───┴┐
   │     │
    ╲   ╱   ← Konische Schneide
     ╲ ╱
      ●     ← Spitze (Winkel)
```

**Pflichtfelder:** durchmesser, schaft_durchmesser, schneidlaenge, gesamtlaenge, schneiden, **spitzenwinkel** (1-179°)

**Anwendung:**
- V-Carving (Schrift mit V-Querschnitt)
- Fasen entlang Konturen
- Reliefs (sehr spitze V-Bits: 4°/8°/10°/15°/20° fuer feinste Details)

**Empfehlungen:**
- 60°/90° fuer Standard-Schrift
- 30°/45° fuer schaerfere Linien
- 10° und kleiner fuer Detail-Reliefs (sehr fragil!)

---

## BALLNOSE_V_BIT

V-Bit mit Mini-Kugel an der Spitze statt scharfer Spitze. Robuster als
reines V-Bit, weicheres Relief-Ergebnis.

```
    │   │
   ┌┴───┴┐
   │     │
    ╲   ╱
     ╲_╱     ← Mini-Kugel
      ◔      Spitzendurchmesser z.B. 0.25 mm
```

**Pflichtfelder:** durchmesser, schaft_durchmesser, schneidlaenge, gesamtlaenge, schneiden, **spitzenwinkel** + **spitzendurchmesser**

**Anwendung:**
- Robustere Reliefs (Spitze bricht nicht so schnell ab)
- Weiche Z-Stops in Reliefs (keine scharfe Tiefenkante)
- Schrift-Carving mit weichen Boden-Konturen

**Empfehlungen:** Spitzendurchmesser 0.25-1 mm, Spitzenwinkel 15-60°.

---

## GRAVIERSTICHEL

Sehr feine, sehr lange konische Spitze. Auch „Engraving bit".

```
    │   │
   ┌┴───┴┐
   │     │
    ╲   ╱
     ╲ ╱     ← sehr feine, lange Konus
      ●
```

**Pflichtfelder:** durchmesser, schaft_durchmesser, schneidlaenge, gesamtlaenge, schneiden, **spitzenwinkel** (typisch 10-30°)

**Anwendung:**
- Feinste Gravur in Holz/Metall
- Schrift-Gravur mit konstanter Tiefe
- Logo-Gravur

**Empfehlungen:** Sehr geringe Schnitt-Tiefe (0.1-0.3 mm), hoher Vorschub, vor allem nicht plungen — immer schraege Anfahrt.

**Unterschied zu V-Bit:** Gravierstichel ist viel laenger + duenner, fuer flache Linien. V-Bit ist breiter und macht V-Querschnitt.

---

## BOHRER

Spiral-Bohrer mit Spitzenwinkel.

```
    │   │
   ┌┴───┴┐
   │ \\/ │   ← Spiral-Schneide
   │ /\\ │
    ╲╲╱╱
     ╲╱      ← Bohrer-Spitze (typisch 118° oder 135°)
      ●
```

**Pflichtfelder:** durchmesser, schaft_durchmesser, schneidlaenge, gesamtlaenge, schneiden=2 (typisch), **spitzenwinkel** (118° HSS, 135° HM)

**Anwendung:**
- Standard-Bohrloecher
- Mit Peck-Strategie fuer tiefe Loecher

**Empfehlungen:** Spitzenwinkel 118° fuer Holz/Kunststoff, 135° fuer NE-Metalle. Stets mit Peck-Zyklus arbeiten (G83) bei Tiefen > 3x Durchmesser.

---

## EINSCHNEIDER

Schaftfraeser mit nur EINER Schneide.

```
    │   │
   ┌┴───┴┐
   │  ●  │   ← nur 1 Schneide
   │  ●  │
   │  ●  │
   └─────┘
```

**Pflichtfelder:** wie Schaftfraeser, **schneiden=1**

**Anwendung:**
- Sehr sauberer Schnitt in Holz (kein Ausriss)
- Hohe Vorschuebe in Weichholz
- Acryl/PVC (keine Schmelz-Probleme)

**Empfehlungen:** Vorschub mindestens **doppelt** so hoch wie bei 2-Flute, damit Spaene gross genug. Tendenz zu Schwingungen — kurz einspannen.

---

## FISCHSCHWANZ

Schaftfraeser dessen Endschneiden ueber die Werkzeug-Mitte hinausragen.
Eine Schneide schneidet exakt durch die Mitte — **plunge-faehig** wie ein
Bohrer.

```
    │   │
   ┌┴───┴┐
   │     │
   │     │
   └╲▲╱─┘   ← Fischschwanz-Form, eine Schneide bis Mitte
      ●     ← schneidende Mitte = direktes Plunge moeglich
```

**Pflichtfelder:** wie Schaftfraeser (schneiden=2 typisch)

**Anwendung:**
- Direktes Plunge in Material (kein Vorbohren noetig)
- Taschen in Sperrholz/Massivholz ohne Helix-Eintauch
- Bohrungen mit nicht-Standard-Durchmesser ohne Werkzeug-Wechsel zum Bohrer

**Unterschied zu Standard-Schaftfraeser:** Standard-Schaftfraeser hat in der Mitte einen toten Punkt — kann nicht gerade nach unten plungen, braucht Helix oder Rampe. Fischschwanz kann beides.

**Empfehlungen:** Etwas weniger aggressiv als reiner Bohrer (Spitzenform bricht schneller), aber viel produktiver als Standard + Helix-Eintauch.

---

## SCHRUPPFRAESER

Schaftfraeser mit rauem Schneiden-Profil. Auch „Rougher" oder „Corncob".

```
    │   │
   ┌┴───┴┐
   │ ▶◀  │   ← Rippen / Zaehne entlang Schneide
   │ ▶◀  │
   │ ▶◀  │
   │ ▶◀  │
   └─────┘
```

**Pflichtfelder:** wie Schaftfraeser

**Anwendung:**
- Schnelles Material-Wegnehmen (Roughing)
- Vibrations-arm durch Schneiden-Aufteilung
- NICHT fuer Schlicht (raues Oberflaechen-Ergebnis)

**Empfehlungen:** Mit normalem Schaftfraeser fuer Schlichten kombinieren. Hoher Vorschub, grosser Stepdown moeglich.

---

## DIAMANTGRAVIERER

Diamant-Spitze (gebondet), nicht aus HM/HSS. Auch „CVD diamond bit".

```
    │   │
   ┌┴───┴┐
   │     │
    ╲   ╱
     ╲ ╱
      ◆     ← Diamant-Spitze (sehr klein)
```

**Pflichtfelder:** wie V_BIT/GRAVIERSTICHEL, plus **material=DIAMANT**

**Anwendung:**
- Edelstahl-Gravur
- Glas / Keramik (sehr vorsichtig)
- Saphir / Stein

**Empfehlungen:** Sehr geringe Tiefen (0.05 mm), hoher Vorschub, Spindle nicht zu schnell drehen lassen (Diamant haelt nur begrenzten Druck/Temperatur aus).

---

## DRAG_GRAVIERER

Federbelasteter Diamant. **Spindle dreht NICHT** (M5).

```
    │   │
   ┌┴───┴┐
   │ ─┼─ │   ← Feder im Werkzeug
   │  │  │
   │  ◆  │   ← Diamant-Spitze unter Eigengewicht/Feder
```

**Pflichtfelder:** wie GRAVIERSTICHEL, **typ=DRAG_GRAVIERER**

**Anwendung:**
- Aluminium-Gravur (sehr fein)
- Beschriftung auf eloxiertem Alu
- Sehr feine Linien ohne Spaene

**Besonderheit:** Im G-Code wird **M5** (Spindle aus) gesetzt. Toolpath laeuft sehr langsam (200-400 mm/min) und mit minimaler Tiefe (0.05-0.1 mm). Werkzeug folgt der Kontur unter Eigengewicht.

---

## Modell-Audit (A41)

| Typ | spitzenwinkel | spitzendurchmesser | spitzenradius | Audit |
|-----|--------------|--------------------|---------------| ----- |
| SCHAFTFRAESER | nicht noetig | nicht noetig | nicht noetig | ✅ |
| KUGELFRAESER | nicht noetig | nicht noetig | optional (= durchmesser/2) | ✅ |
| TORUSFRAESER | nicht noetig | nicht noetig | **Pflicht** (Eckenradius) | ⚠ Validator fehlt noch |
| V_BIT | **Pflicht** (1-179°) | nicht noetig | nicht noetig | ✅ |
| BALLNOSE_V_BIT | **Pflicht** | **Pflicht (>0)** | nicht noetig | ✅ Validator vorhanden |
| GRAVIERSTICHEL | optional | optional | nicht noetig | ⚠ Validator-Empfehlung |
| BOHRER | optional (typisch 118°) | nicht noetig | nicht noetig | ⚠ Validator-Empfehlung |
| EINSCHNEIDER | nicht noetig | nicht noetig | nicht noetig | ✅ (= Schaftfraeser schneiden=1) |
| FISCHSCHWANZ | nicht noetig | nicht noetig | nicht noetig | ✅ (= Schaftfraeser plunge-fähig — semantisch markiert) |
| SCHRUPPFRAESER | nicht noetig | nicht noetig | nicht noetig | ✅ (= Schaftfraeser mit rauem Profil) |
| DIAMANTGRAVIERER | optional | optional | nicht noetig | ⚠ Validator-Empfehlung |
| DRAG_GRAVIERER | optional | optional | nicht noetig | ⚠ Validator-Empfehlung |

**Audit-TODO:**
- TORUSFRAESER: Validator dass `spitzenradius > 0` und `< durchmesser/2`
- BOHRER: Default `spitzenwinkel = 118` wenn nicht gesetzt
- Auto-Mapping `schneiden=1` -> `typ=EINSCHNEIDER` als Hint

## Verwandt

- [Werkzeug-Bibliothek](Werkzeug-Bibliothek.md) — Verwaltung
- [Werkzeug-Format](Werkzeug-Format.md) — JSON-Schema
- [Glossar](Glossar.md) — alle CNC-Begriffe
