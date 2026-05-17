"""OpenAPI-3.1-Spec-Generator (Master-Plan B3).

Wandelt die registrierten Flask-Routen + Docstrings in eine OpenAPI-Spec.
Bewusst minimal-invasiv: kein decorator-Zoo, keine pydantic-Schema-Pflicht.
Wer mehr Schema-Detail will, kann pro Endpoint die ``openapi_extra``-Funktion
benutzen (siehe ``api_extra``-Registry).

Zugriff:
- ``GET /api/openapi.json`` — vollstaendige Spec als JSON
- ``GET /api/openapi.yaml`` — gleiche Spec als YAML (falls PyYAML verfuegbar)
- ``GET /docs`` — minimale HTML-Seite mit Swagger-UI (CDN, fuer Dev)
"""

from __future__ import annotations

import inspect
import re
from typing import Any

from flask import Flask

from camwosa import __version__


# Pro Endpoint koennen Module hier ein extra-Dict eintragen, das in den
# OpenAPI-Path-Eintrag eingemischt wird (request-body schemas, responses,
# tags, etc.). Key = view-function-name (z.B. "heightmap.aus_bild").
openapi_extra: dict[str, dict] = {}

# Tag-Beschreibungen je Blueprint
TAG_BESCHREIBUNGEN: dict[str, str] = {
    "machines": "Maschinen-Verwaltung (Profile, Default-Set, CRUD)",
    "tools": "Werkzeug-Bibliothek (Schaft/Kugel/V-Bit/Bohrer/etc.)",
    "materials": "Material-Datenbank (Holz/Kunststoff/NE-Metall)",
    "spindles": "Spindel-Konfiguration je Maschine",
    "projects": "Projekt-Persistenz (.cwp-Container)",
    "operations": "CAM-Operationen (Kontur/Tasche/Bohren/Gravur/Relief/Wrap)",
    "safety": "Sicherheits-Pruefung vor G-Code-Export",
    "nesting": "Verschnittoptimierung (rectpack + nest2D)",
    "dxf": "DXF-Import (ezdxf)",
    "cad": "CAD-Plugin-Loader (DXF/SVG/STL/STEP/...)",
    "feeds": "Feeds & Speeds Rechner",
    "postprocessors": "G-Code-Postprozessoren (GRBL Standard + Rotary)",
    "workflow": "Multi-Setup-Workflow (Arbeitsplan, Werkzeugwechsel)",
    "standzeit": "Werkzeug-Standzeit-Tracking",
    "rotary": "Rotary-Profile + Rohmaterial-Setup",
    "cutting_presets": "Schnitt-Presets pro Material+Werkzeug",
    "annotationen": "Geometrie-Annotationen (Anschlag/Refpunkt/Auto-Op)",
    "quickcam": "Quick-CAM-Templates",
    "simulation": "Voxel-basierte Material-Abtrag-Simulation",
    "heightmap": "Bild→Heightmap, Wrap-Relief, Bearbeitungs-Filter, AI",
    "text": "Text-zu-Pfad-Konverter (Master-Plan A37)",
    "wrap": "Wrap-Mode Pattern-Skalierung + Batch-Toolpath (A38)",
    "health": "Health-Check",
}


def _flask_pfad_zu_openapi(pfad: str) -> tuple[str, list[dict]]:
    """``/api/projects/<project_id>`` → (``/api/projects/{project_id}``, [params])."""
    parameters = []
    def _ersetzen(match: re.Match) -> str:
        converter = match.group(1)  # z.B. "int:" oder ""
        name = match.group(2)
        typ = "string"
        if converter == "int:":
            typ = "integer"
        elif converter == "float:":
            typ = "number"
        parameters.append({
            "name": name,
            "in": "path",
            "required": True,
            "schema": {"type": typ},
        })
        return f"{{{name}}}"
    neuer_pfad = re.sub(r"<(\w+:)?(\w+)>", _ersetzen, pfad)
    return neuer_pfad, parameters


def _extrahiere_summary_und_beschreibung(docstring: str | None) -> tuple[str, str]:
    """Erste Zeile = Summary, Rest = Description."""
    if not docstring:
        return "", ""
    lines = inspect.cleandoc(docstring).split("\n")
    summary = lines[0].strip()
    beschreibung = "\n".join(lines[1:]).strip()
    return summary, beschreibung


def _erkenne_methoden(rule_methods: set[str]) -> list[str]:
    """Filter HEAD/OPTIONS — wir wollen die echten HTTP-Verben."""
    return [
        m.lower() for m in sorted(rule_methods)
        if m.lower() in ("get", "post", "put", "patch", "delete")
    ]


def generiere_spec(app: Flask) -> dict[str, Any]:
    """Generiert die OpenAPI-3.1-Spec aus den registrierten Routen."""
    paths: dict[str, dict] = {}
    benutzte_tags: set[str] = set()

    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        view_func = app.view_functions.get(rule.endpoint)
        if view_func is None:
            continue

        pfad, path_params = _flask_pfad_zu_openapi(str(rule))
        methoden = _erkenne_methoden(rule.methods or set())
        if not methoden:
            continue

        # Blueprint-Name als Tag
        blueprint = rule.endpoint.split(".")[0] if "." in rule.endpoint else "default"
        benutzte_tags.add(blueprint)

        summary, beschreibung = _extrahiere_summary_und_beschreibung(view_func.__doc__)

        operation_base = {
            "tags": [blueprint],
            "summary": summary or rule.endpoint,
            "description": beschreibung,
            "operationId": rule.endpoint.replace(".", "_"),
        }
        if path_params:
            operation_base["parameters"] = path_params

        # Standard responses
        operation_base["responses"] = {
            "200": {"description": "Erfolgreich"},
            "400": {"description": "Ungueltige Anfrage"},
            "422": {"description": "Unverarbeitbare Daten"},
        }

        # Falls Endpoint extra-Schema definiert hat
        extra = openapi_extra.get(rule.endpoint)
        if extra:
            operation_base = {**operation_base, **extra}

        if pfad not in paths:
            paths[pfad] = {}
        for methode in methoden:
            paths[pfad][methode] = operation_base

    spec: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": "CAMWOSA Backend API",
            "version": __version__,
            "description": (
                "REST-API fuer CAMWOSA. Bindet nur auf 127.0.0.1 und wird "
                "vom Electron-Renderer und MCP-Server konsumiert. "
                "Endpoints sind nach Funktion in Tags gruppiert.\n\n"
                "Generiert automatisch aus den Flask-Routen + Docstrings. "
                "Master-Plan-Position [B3]."
            ),
            "license": {"name": "MIT"},
        },
        "servers": [{"url": "http://127.0.0.1:8765", "description": "Lokaler Backend"}],
        "tags": [
            {
                "name": tag,
                "description": TAG_BESCHREIBUNGEN.get(tag, ""),
            }
            for tag in sorted(benutzte_tags)
        ],
        "paths": dict(sorted(paths.items())),
    }
    return spec


# ---------------------------------------------------------------------------
# Flask-Blueprint mit den OpenAPI-Endpoints
# ---------------------------------------------------------------------------


from flask import Blueprint, Response, current_app, jsonify  # noqa: E402

bp = Blueprint("openapi", __name__, url_prefix="/api")


@bp.get("/openapi.json")
def openapi_json():
    """Liefert die OpenAPI-3.1-Spec als JSON."""
    spec = generiere_spec(current_app)
    return jsonify(spec)


@bp.get("/openapi.yaml")
def openapi_yaml():
    """Liefert die OpenAPI-3.1-Spec als YAML (falls PyYAML verfuegbar)."""
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return jsonify({"fehler": "PyYAML nicht installiert"}), 501
    spec = generiere_spec(current_app)
    return Response(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True),
                    mimetype="application/x-yaml")


# Einfache Swagger-UI-Seite (loads from CDN — nur fuer Dev sinnvoll, im
# Production-Build ggf. weglassen). Wenn ohne Internet, kann man das Spec
# auch unter editor.swagger.io einfuegen.
_SWAGGER_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <title>CAMWOSA API Docs</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({ url: '/api/openapi.json', dom_id: '#swagger-ui' });
  </script>
</body>
</html>
"""


@bp.get("/docs")
def docs():
    """Swagger-UI-Seite (laedt UI-Assets von CDN)."""
    return Response(_SWAGGER_HTML, mimetype="text/html")


__all__ = ["bp", "generiere_spec", "openapi_extra"]
