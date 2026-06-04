# CAMWOSA-Sender — Architektur (Teil G)

> **Status:** Design-Dokument. Noch nicht gebaut. Markus' Wunsch (2026-06-04):
> „später ggf. eine Steuerung, die den G-code an den CNC-Controller liefert
> (ggf. zwei Apps: CAMWOSA als Server, das andere als Client, ggf. mit
> rudimentären Steuerungsfunktionen auf einem anderen Rechner)."
>
> **Grundsatz-Reconcile:** Der Master-Plan führt „Direkte Maschinen-Steuerung"
> bewusst als out-of-scope für **CAMWOSA** (Pure-CAM). Dieses Dokument bricht
> das nicht — die Steuerung ist eine **eigenständige, lose gekoppelte App**.
> CAMWOSA selbst streamt weiterhin nichts an einen Controller.

---

## 1. Ziele / Nicht-Ziele

**Ziele**
- G-code (`.nc`) zuverlässig an einen **GRBL-1.1**-Controller streamen (USB-Serial).
- Sichere Grund-Steuerung: Jog, Homing, Nullen, Probing, Feed-Hold/Resume,
  E-Stop, Overrides, Status-DRO, Konsole.
- Läuft **eigenständig** und kann auf einem **anderen Rechner** an der Maschine
  laufen (Mini-PC / Raspberry Pi / Tablet-Browser).
- Wiederverwendung der CAMWOSA-Muster (Electron+React+Python, FastMCP, i18n,
  Installer, Update).

**Nicht-Ziele (bewusst)**
- Kein CAM im Sender (keine Toolpaths erzeugen — das ist CAMWOSA).
- Kein 5-Achs, keine Nicht-GRBL-Controller in Stufe 1 (Plugin später).
- Keine Cloud. LAN/localhost first.

---

## 2. Topologie — „CAMWOSA als Server, Sender als Client"

```
┌─────────────────────────┐         (optional, LAN/HTTP)        ┌───────────────────────────┐
│  CAMWOSA (CAM, Server)  │  ── GET /api/jobs, /api/jobs/{id} ─▶ │  CAMWOSA-Sender (Client)  │
│  - erzeugt .nc          │      (G-code abholen)               │  - lädt .nc (lokal o. HTTP)│
│  - Job-Export-Endpoint  │ ◀── optional Status-Callback ────── │  - Streaming-Engine        │
└─────────────────────────┘                                     │  - Serial → GRBL           │
        (Rechner A)                                             └──────────────┬────────────┘
                                                                    USB-Serial │
                                                                ┌──────────────▼────────────┐
                                                                │  GRBL 1.1 (Genmitsu)       │
                                                                └────────────────────────────┘
                                                                        (Rechner B, an Maschine)
```

Drei Betriebsarten, alle vom selben Sender-Build:
1. **Solo:** Sender öffnet eine lokale `.nc`-Datei und streamt. CAMWOSA gar nicht nötig.
2. **Gekoppelt-lokal:** Sender + CAMWOSA auf demselben Rechner; „In Sender öffnen" reicht den Pfad rüber.
3. **Gekoppelt-LAN:** CAMWOSA läuft am Schreibtisch (Rechner A), Sender am Maschinen-PC (Rechner B), holt Jobs über HTTP.

Die einzige CAMWOSA-Erweiterung dafür: ein **schmaler, optionaler** Job-Export
(read-only) — verletzt Pure-CAM nicht (CAMWOSA bietet Dateien an, schiebt nicht).

---

## 3. GRBL-1.1-Protokoll (das Herz des Senders)

### 3.1 Streaming — Character-Counting

Zwei Verfahren: *send-response* (einfach, langsam: eine Zeile, auf `ok` warten,
nächste) und *character-counting* (Standard für flüssige Bewegung). Wir nutzen
**character-counting**:

- GRBL hat einen RX-Puffer von **128 Byte** (`RX_BUFFER_SIZE`).
- Der Host hält Buch über die Summe der Zeichen aller **noch nicht quittierten**
  Zeilen. Solange `summe + len(naechste_zeile) < 128`, wird gesendet.
- Pro `ok`/`error` von GRBL wird die Länge der ältesten offenen Zeile abgezogen.
- So ist der Puffer immer gefüllt → kein Verhungern der Bewegungs-Planung → keine
  Ruckler bei vielen kurzen Segmenten (3D!).

```python
# Pseudocode der Streaming-Schleife
offen = collections.deque()   # (zeilen_text, laenge)
belegt = 0
while zeilen_übrig or offen:
    while zeilen_übrig and belegt + len(naechste)+1 <= 127:
        seriell.write(naechste + "\n"); offen.append((naechste, len(naechste)+1)); belegt += len(naechste)+1
    antwort = seriell.readline()           # 'ok' | 'error:x' | '<...>' | '[...]'
    if antwort == 'ok' or antwort.startswith('error'):
        _, l = offen.popleft(); belegt -= l
        if antwort.startswith('error'): hard_stop_und_alarm(antwort)
```

### 3.2 Real-Time-Kommandos (1 Byte, nie gepuffert)

Werden **sofort** verarbeitet, gehen **nicht** in den RX-Puffer, zählen nicht im
Streaming. Aus GRBL 1.1 `config.h`:

| Funktion | Byte | ASCII |
|----------|------|-------|
| Status-Report | `0x3F` | `?` |
| Cycle-Start / Resume | `0x7E` | `~` |
| Feed-Hold | `0x21` | `!` |
| **Soft-Reset (E-Stop)** | `0x18` | Ctrl-X |
| Safety-Door | `0x84` | — |
| Jog-Cancel | `0x85` | — |
| Feed-Override 100 % | `0x90` | — |
| Feed-Override +10 % / −10 % | `0x91` / `0x92` | — |
| Feed-Override +1 % / −1 % | `0x93` / `0x94` | — |
| Rapid-Override 100 % / 50 % / 25 % | `0x95` / `0x96` / `0x97` | — |
| Spindle-Override 100 % | `0x99` | — |
| Spindle-Override +10 % / −10 % | `0x9A` / `0x9B` | — |
| Spindle-Override +1 % / −1 % | `0x9C` / `0x9D` | — |
| Spindle-Stop-Toggle | `0x9E` | — |
| Flood-Coolant-Toggle | `0xA0` | — |
| Mist-Coolant-Toggle | `0xA1` | — |

### 3.3 Status-Report (`?` → `<...>`)

Format: `< >` umschlossen, Felder per `|` getrennt.
```
<Idle|MPos:0.000,0.000,0.000|FS:0,0|WCO:0.000,0.000,0.000>
<Run|MPos:12.500,4.000,-1.000|FS:800,18000|Ov:100,100,100|Pn:P>
```
- **State (Pflicht, 1. Feld):** `Idle Run Hold Jog Alarm Door Check Home Sleep`
- **MPos/WPos (Pflicht, 2. Feld):** Maschinen- bzw. Werkstück-Koordinaten.
- **WCO:** Work-Coordinate-Offset (MPos − WCO = WPos). GRBL schickt WCO nur
  periodisch → Client muss WCO cachen und WPos selbst rechnen.
- **Bf:** freie Planner-Blocks, freie RX-Bytes.
- **FS:** aktueller Feed, aktuelle Spindel-RPM (`F:` wenn keine Spindel-Readback).
- **Ov:** Override-% (Feed, Rapid, Spindle).
- **Pn:** aktive Eingangspins (`X Y Z P(probe) D(door) H(hold) R(reset) S(start)`).
- **A:** Accessory (S=Spindle CW, C=CCW, F=Flood, M=Mist).
- **Ln:** aktuelle Zeilennummer (wenn `$10` gesetzt).

Polling-Takt: **5 Hz** (alle 200 ms `?`), GRBL antwortet in ~5–20 ms.

### 3.4 System-Kommandos (gepuffert, mit `ok`)

`$$` Settings · `$#` Work-Offsets/G28/G30/TLO · `$G` Parser-State ·
`$I` Build-Info · `$N` Startup-Blocks · `$C` Check-Mode · `$X` Alarm-Lock lösen ·
`$H` Homing · `$J=…` Jog · `$RST=…` Reset · `$SLP` Sleep.

**Jog:** `$J=G91 G21 X10 F1000` (relativ, mm, 10 mm in X bei 1000 mm/min).
Modal-Worte nur für diesen Jog: `G20/G21`, `G90/G91`, `G53`. Abbruch per
Jog-Cancel-Byte `0x85` (verwirft gepufferte Jogs sofort, sauberer Stopp).

### 3.5 Fehler & Alarme

- `error:x` — Zeile abgelehnt (Syntax/Soft-Limit). Beim Streaming = **harter
  Stopp** + Anzeige des Codes im Klartext (Code-Tabelle mappen).
- `ALARM:x` — kritisch (Hard-Limit, Probe-Fail, Homing-Fail). GRBL geht in
  `Alarm`-State, ignoriert Bewegung bis `$X` (Lock lösen) oder `$H` (Homing).
  **Regel: nie automatisch resumen.** User muss bewusst entscheiden.

---

## 4. Sicherheit (oberste Priorität)

- **E-Stop = Soft-Reset (`0x18`)** als großer, immer sichtbarer Button + Hotkey.
- **Feed-Hold/Resume** prominent; Resume nur manuell.
- **Alarm-Handling:** roter Vollbild-Banner, Klartext-Ursache, kein Auto-Resume.
- **Connection-Loss:** Serial weg → sofort als Not-Zustand behandeln (GRBL fährt
  zwar weiter bis Pufferende, aber UI muss warnen + Reconnect anbieten).
- **Soft-Limits/Hard-Limits** aus `$20/$21` lesen + anzeigen; vor Stream warnen
  wenn Job außerhalb `$130-$132`.
- **Probing-Schutz:** G38.2 nur über geführten Dialog; Z-Probe-Plattendicke
  abfragen; nach Probe Z-Null setzen mit Bestätigung.
- **Tür/Deckel (`Pn:D`)** respektieren falls verdrahtet.
- **Kein Blind-Resume nach Hold mitten im Schnitt** ohne Hinweis (Spindel-Last).

---

## 5. Tech-Stack & Wiederverwendung aus CAMWOSA

| Schicht | Technologie | Reuse |
|---------|-------------|-------|
| Backend | Python + **pyserial** + asyncio/threads; **FastAPI/Flask + WebSocket** | FastMCP-Muster, Logging, Settings, Installer-Skripte aus CAMWOSA |
| Streaming-Engine | eigenes Modul `grbl_stream.py` (char-counting + RT-Bytes + Status-Parser) | — neu — |
| Frontend | React + Vite + Tailwind + zustand | Design-System, i18n, Komponenten aus CAMWOSA |
| Desktop | Electron-Wrapper (wie CAMWOSA) **oder** reine Web-UI (Pi/Tablet) | Electron-Bootstrap aus CAMWOSA |
| MCP | FastMCP-Server (Jog/Stream/Status als Tools) — Parität | MCP-Muster aus CAMWOSA |

**WebSocket-API (Sender-intern, Client↔Sender-Backend):**
- `→ connect {port, baud}` / `disconnect`
- `→ stream_start {gcode|path}` / `stream_pause` / `stream_resume` / `stream_stop`
- `→ jog {axis, dist, feed}` / `jog_cancel` / `home` / `unlock` / `zero {axes}`
- `→ probe {axis, dist, feed, plate}` / `realtime {byte}` (Override/Hold)
- `← status {state, mpos, wpos, fs, ov, pn}` (5 Hz Push)
- `← progress {line, total, percent, elapsed, eta}`
- `← console {tx|rx, text}` / `← alarm {code, text}` / `← error {code, text}`

**Reine Web-UI-Variante** (für Pi/Tablet an der Maschine): Sender-Backend serviert
die statische React-App + WebSocket — kein Electron nötig, im Browser aufrufbar.

---

## 6. Funktions-Stufen (Master-Plan Teil G)

| Nr | Funktion | Beschreibung |
|----|----------|--------------|
| G1 | **Serial + Verbindung** | Port-Scan, Connect/Disconnect, Baud (115200), Welcome-Parse (`Grbl 1.1…`), `$$`/`$I` lesen. |
| G2 | **Status-DRO** | 5-Hz-Polling, Status-Parser, MPos/WPos/State/FS/Ov/Pn-Anzeige, WCO-Cache. |
| G3 | **Jog + Nullen + Homing** | Jog-Pad (Schrittweiten + kontinuierlich), `$H`, `$X`, Achsen nullen (G10 L20). Jog-Cancel. |
| G4 | **Streaming-Engine** | Char-Counting, Pause/Resume/Stop, Fortschritt + ETA, Konsole, Zeilen-Highlight. |
| G5 | **Real-Time-Overrides** | Feed/Rapid/Spindle-Override-Buttons, Feed-Hold, **E-Stop**, Spindle-Stop-Toggle. |
| G6 | **Probing** | Z-Probe-Wizard (G38.2 + Plattendicke), optional XYZ-Touchplate. |
| G7 | **Sicherheits-Layer** | Alarm/Error-Klartext (Code-Tabellen), Limit-Warnung, Connection-Loss-Handling, kein Auto-Resume. |
| G8 | **CAMWOSA-Kopplung** | CAMWOSA-Job-Export (read-only HTTP) + „In Sender öffnen"; LAN-Discovery optional. |
| G9 | **MCP + i18n + Packaging** | FastMCP-Tools (Parität), DE/EN, Installer/Portable, optional reine Web-UI für Pi. |
| G10 | **Controller-Plugins** | Abstraktion für grblHAL / FluidNC / Marlin-CNC später (Protokoll-Adapter). |

**Reihenfolge:** G1→G2→G3 ergeben schon ein nützliches Jog/Setup-Tool. G4/G5/G7
machen es zum echten Sender. G6/G8 sind Komfort. G10 ist Zukunft.

---

## 7. Abgrenzung CAMWOSA ↔ Sender (Single Source of Truth)

| Verantwortung | CAMWOSA | Sender |
|---------------|:------:|:------:|
| Toolpaths/Strategien erzeugen | ✅ | ❌ |
| Postprozessor / G-code schreiben | ✅ | ❌ |
| Werkzeug-/Material-/Maschinen-DB | ✅ | ❌ (liest nur Maschinen-Limits optional) |
| Serial-Verbindung zum Controller | ❌ | ✅ |
| Jog/Home/Probe/Stream/Override | ❌ | ✅ |
| Live-Status/DRO | ❌ | ✅ |
| Job-Datei bereitstellen (read-only) | ✅ (optional) | — |
| Job-Datei abholen/öffnen | — | ✅ |

So bleibt jede Fähigkeit an **genau einem** Ort. CAMWOSA kann weiter ohne Sender
existieren; der Sender kann ohne CAMWOSA jede `.nc` fahren.

---

## 8. Offene Entscheidungen (für Markus)

1. **Eigenes Repo** (`CAMWOSA-Sender`) oder Monorepo-Unterordner? (Empfehlung: eigenes Repo, da eigener Release-Zyklus + Pi-Build.)
2. **Electron + Web** oder nur Web-UI? (Empfehlung: Sender-Backend serviert Web-UI → läuft im Browser auf dem Maschinen-Pi; Electron optional fürs Desktop-Gefühl.)
3. Baud fix 115200 (Genmitsu-Default) oder konfigurierbar? (Empfehlung: konfigurierbar, Default 115200.)
4. Soll der Sender auch **Laser** (`$32`, M4 dynamisch) können? (Markus nutzt Laser via LightBurn — evtl. bewusst auslassen.)
