# MCP-Server

> **Status:** ✅ Phase 1 (alle Backend-Funktionen als MCP-Tools verfuegbar).
> **Code:** [mcp_server/camwosa_mcp/server.py](../../mcp_server/camwosa_mcp/server.py)

Der MCP-Server stellt CAMWOSA als **Tool-Sammlung fuer Claude Desktop / Claude Code** bereit. Er ist eine Bridge zur Backend-API — gleiche Funktionen wie die UI.

## MCP-First-Prinzip

Die UI ist **vollwertig stand-alone bedienbar**. Das MCP ist eine **zweite Bedienoberflaeche** zur gleichen Backend-API. Konsequenz: Wenn Claude eine Bearbeitung erstellt, sehen wir die einzelnen Operations ganz normal in der Operations-Liste der UI.

## Setup

```bash
cd mcp_server
pip install -e .

# Backend starten (separates Terminal)
cd ../backend
camwosa-backend

# MCP-Server starten
cd ../mcp_server
camwosa-mcp
```

## Konfiguration in Claude Desktop

`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "camwosa": {
      "command": "camwosa-mcp",
      "env": {
        "CAMWOSA_BACKEND_URL": "http://127.0.0.1:8765"
      }
    }
  }
}
```

## Verfuegbare Tools

### Stammdaten
- `maschinen_anzeigen()` -> Liste
- `maschine_details(maschine_id)`
- `werkzeuge_anzeigen()` / `werkzeug_details(werkzeug_id)`
- `materialien_anzeigen()` / `material_details(material_id)`

### Berechnung
- `feeds_speeds_berechnen(maschine_id, werkzeug_id, material_id, rpm_wunsch?)`

### Postprozessoren
- `postprozessoren_anzeigen()`

### CAM-Operations
- `operation_kontur(werkzeug_id, geometrie, parameter)`
- `operation_tasche(...)`
- `operation_bohren(werkzeug_id, punkte, parameter)`
- `operation_gravur(...)`

### G-Code-Generierung
- `gcode_erzeugen(maschine_id, werkzeug_id, toolpaths, postprozessor_id?)`

### Sicherheit
- `sicherheits_pruefung(maschine_id, werkzeug_id, toolpath, z_oberkante_material)`

### Nesting
- `nesting_starten(teile, platten, abstand_zwischen_teilen)`

### Projekt
- `projekt_neu(name, maschine_id, rohmaterial, autor)`

### Diagnose
- `backend_status()` -> Health-Check

## Beispiel-Dialog

> **User:** "Mach mir aus dem 6mm Schaftfraeser eine 50x50mm Tasche in Buche, 4mm tief."
>
> **Claude:**
> 1. `feeds_speeds_berechnen(maschine_id="genmitsu_proverxl_4030_v2", werkzeug_id="schaft_6mm_2s_hm", material_id="buche_massiv")`
>    -> RPM 18000, Vorschub 2000
> 2. `operation_tasche(werkzeug_id="schaft_6mm_2s_hm", geometrie={typ:"polylinie", punkte:[[0,0],[50,0],[50,50],[0,50]], geschlossen:true}, parameter={spindel_rpm:18000, vorschub:2000, eintauch_vorschub:400, max_tiefe:4, stepdown:2, stepover_prozent:40})`
> 3. `sicherheits_pruefung(...)` -> kein Blocker
> 4. `gcode_erzeugen(maschine_id="...", werkzeug_id="...", toolpaths=[...])`

## Bekannte Einschraenkungen

- DXF-Datei-Upload via MCP noch nicht implementiert (nur via UI). Workaround: User importiert DXF in UI, MCP nutzt die geladene Geometrie.
- Workflow- und STL-Tools kommen mit naechster Iteration.

## Verwandt

- [API](API.md)
- [Architektur](Architektur.md)
- [MCP-Tools](MCP-Tools.md) — vollstaendige Tool-Referenz
