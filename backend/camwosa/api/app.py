"""Flask-API fuer CAMWOSA.

Bindet auf 127.0.0.1 (NIEMALS 0.0.0.0). Wird von Electron-Renderer und
MCP-Server konsumiert.

Endpoints werden in api/endpoints/ modular registriert.
"""

from __future__ import annotations

import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS


def create_app(*, debug: bool = False) -> Flask:
    """Erzeugt die Flask-App."""
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False  # Umlaute korrekt
    app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB max upload (STL)

    CORS(app, origins=["http://localhost:*", "app://*"])

    # Endpoints registrieren
    from camwosa.api.endpoints import (
        machines,
        materials,
        operations,
        projects,
        rotary as rotary_ep,
        spindles,
        standzeit as standzeit_ep,
        tools,
        safety as safety_ep,
        nesting as nesting_ep,
        dxf as dxf_ep,
        cad as cad_ep,
        feeds as feeds_ep,
        postprocessors,
        workflow as workflow_ep,
        cutting_presets as cutting_presets_ep,
        annotationen as annotationen_ep,
        quickcam as quickcam_ep,
        simulation as simulation_ep,
        heightmap as heightmap_ep,
        text as text_ep,
        wrap as wrap_ep,
    )

    app.register_blueprint(machines.bp)
    app.register_blueprint(spindles.bp)
    app.register_blueprint(tools.bp)
    app.register_blueprint(materials.bp)
    app.register_blueprint(projects.bp)
    app.register_blueprint(operations.bp)
    app.register_blueprint(safety_ep.bp)
    app.register_blueprint(nesting_ep.bp)
    app.register_blueprint(dxf_ep.bp)
    app.register_blueprint(cad_ep.bp)
    app.register_blueprint(feeds_ep.bp)
    app.register_blueprint(postprocessors.bp)
    app.register_blueprint(workflow_ep.bp)
    app.register_blueprint(standzeit_ep.bp)
    app.register_blueprint(rotary_ep.bp)
    app.register_blueprint(cutting_presets_ep.bp)
    app.register_blueprint(annotationen_ep.bp)
    app.register_blueprint(quickcam_ep.bp)
    app.register_blueprint(simulation_ep.bp)
    app.register_blueprint(heightmap_ep.bp)
    app.register_blueprint(text_ep.bp)
    app.register_blueprint(wrap_ep.bp)

    # OpenAPI-Spec-Generator (Master-Plan B3) — wird zuletzt registriert,
    # damit alle vorigen Routen in der Spec landen.
    from camwosa.api import openapi as openapi_mod
    app.register_blueprint(openapi_mod.bp)

    @app.route("/health")
    def health():
        from camwosa import __version__
        return jsonify({"status": "ok", "version": __version__})

    @app.errorhandler(404)
    def nicht_gefunden(_e):
        return jsonify({"fehler": "Nicht gefunden"}), 404

    @app.errorhandler(500)
    def server_fehler(_e):
        return jsonify({"fehler": "Interner Serverfehler"}), 500

    if debug:
        app.config["DEBUG"] = True
        logging.basicConfig(level=logging.DEBUG)

    return app


def main() -> None:
    """Startet den Backend-Server (Standalone, nicht Electron)."""
    port = int(os.environ.get("CAMWOSA_BACKEND_PORT", "8765"))
    debug = os.environ.get("CAMWOSA_DEBUG", "0") == "1"
    app = create_app(debug=debug)
    # WICHTIG: nur localhost binden!
    app.run(host="127.0.0.1", port=port, debug=debug)


if __name__ == "__main__":
    main()
