# CAMWOSA MCP-Server

Stellt eine zweite Bedienoberflaeche zum CAMWOSA-Backend bereit (siehe MCP-First-Prinzip in [Architektur-Wiki](../docs/wiki/Architektur.md)).

## Setup

```bash
cd mcp_server
pip install -e .
```

## Starten

```bash
# Backend muss laufen auf 127.0.0.1:8765 (Default)
camwosa-mcp
```

## Konfiguration

Umgebungs-Variable `CAMWOSA_BACKEND_URL` setzt die Backend-URL (Default `http://127.0.0.1:8765`).

## Tools

Alle Tools entsprechen 1:1 den UI-Endpoints der Flask-API. Vollstaendige Liste: siehe [MCP-Tools im Wiki](../docs/wiki/MCP-Tools.md).
