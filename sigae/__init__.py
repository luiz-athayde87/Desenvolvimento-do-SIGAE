"""Application factory do SIGAE."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from flask import Flask, g, jsonify, render_template, request

from .api import api_bp, register_error_handlers
from .auth import auth_bp, seed_demo_user
from .config import Config
from .database import Database
from .service import SigaeService


def create_app(config: dict[str, Any] | type[Config] | None = None) -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(__name__, template_folder=str(project_root / "templates"))
    app.config.from_object(Config)
    if isinstance(config, dict):
        app.config.update(config)
    elif config is not None:
        app.config.from_object(config)

    database = Database(app.config["DATABASE"])
    service = SigaeService(database)
    seed_demo_user(database, app.config["DEMO_USER"], app.config["DEMO_PASSWORD"])
    app.extensions["sigae_database"] = database
    app.extensions["sigae_service"] = service

    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    register_error_handlers(app)

    @app.before_request
    def request_context() -> None:
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))[:64]

    @app.after_request
    def security_headers(response):
        response.headers["X-Request-ID"] = g.get("request_id", "")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; connect-src 'self'"
        )
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        return render_template("index.html")

    register_legacy_routes(app)
    configure_logging(app)
    return app


def register_legacy_routes(app: Flask) -> None:
    """Mantém compatibilidade enquanto consumidores migram para ``/api/v1``."""

    @app.get("/api/estado")
    def legacy_state():
        state = app.extensions["sigae_service"].state()
        return jsonify(
            {
                "heap_pacientes": state["structures"]["patient_heap"],
                "heap_medicos": state["structures"]["doctor_heap"],
                "tabela_hash": state["structures"]["hash"],
                "historico_rn": state["structures"]["red_black"],
                "arvore_avl": state["structures"]["avl"],
            }
        )

    @app.post("/api/paciente")
    def legacy_patient():
        patient = app.extensions["sigae_service"].create_patient(request.get_json(silent=True))
        return jsonify({"sucesso": True, "paciente": patient}), 201

    @app.post("/api/medico")
    def legacy_doctor():
        doctor = app.extensions["sigae_service"].create_doctor(request.get_json(silent=True))
        return jsonify({"sucesso": True, "medico": doctor}), 201

    @app.post("/api/chamar")
    def legacy_call():
        result = app.extensions["sigae_service"].call_next()
        return jsonify({"sucesso": True, **result}), 201

    @app.get("/api/buscar/<identifier>")
    def legacy_search(identifier: str):
        value = app.extensions["sigae_service"].hash.buscar(identifier.upper())
        return jsonify({"encontrado": value is not None, "dados": value})

    @app.post("/api/reset")
    def legacy_reset():
        app.extensions["sigae_service"].reset()
        return jsonify({"sucesso": True})


def configure_logging(app: Flask) -> None:
    if not app.debug:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s level=%(levelname)s logger=%(name)s message=%(message)s")
        )
        app.logger.handlers.clear()
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
