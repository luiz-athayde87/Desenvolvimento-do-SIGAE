"""API REST versionada do SIGAE."""

from __future__ import annotations

import csv
import io
from typing import Any

from flask import Blueprint, Flask, Response, current_app, jsonify, request

from .auth import require_roles
from .service import ConflictError, DomainError, NotFoundError, SigaeService
from .validation import ValidationError, require_json_object

api_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


def service() -> SigaeService:
    return current_app.extensions["sigae_service"]


def success(data: Any, status: int = 200) -> Response:
    return jsonify({"data": data}), status


def positive_int(name: str, default: int) -> int:
    try:
        value = int(request.args.get(name, default))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"O parâmetro {name} deve ser um número inteiro.") from exc
    if value < 1:
        raise ValidationError(f"O parâmetro {name} deve ser maior que zero.")
    return value


@api_bp.get("/health")
def health():
    database = current_app.extensions["sigae_database"]
    with database.connection() as connection:
        connection.execute("SELECT 1").fetchone()
    return success(
        {
            "status": "healthy",
            "service": "sigae",
            "version": "1.1.0",
            "database": "ready",
        }
    )


@api_bp.get("/state")
def get_state():
    return success(service().state())


@api_bp.get("/patients")
def get_patients():
    raw_priority = request.args.get("priority", "").strip()
    priority = None
    if raw_priority:
        try:
            priority = int(raw_priority)
        except ValueError as exc:
            raise ValidationError("Prioridade deve ser um número de 1 a 5.") from exc
        if priority not in range(1, 6):
            raise ValidationError("Prioridade deve estar entre 1 e 5.")
    return success(
        service().list_patients(
            status=request.args.get("status", "").strip(),
            priority=priority,
            query=request.args.get("q", "").strip(),
            page=positive_int("page", 1),
            per_page=positive_int("per_page", 20),
        )
    )


@api_bp.get("/patients/<identifier>")
def get_patient(identifier: str):
    return success(service().get_patient(identifier.upper()))


@api_bp.post("/patients")
@require_roles("recepcao", "enfermagem", "administrador")
def create_patient():
    data = require_json_object(request.get_json(silent=True))
    return success(service().create_patient(data), 201)


@api_bp.patch("/patients/<identifier>/priority")
@require_roles("enfermagem", "administrador")
def reclassify_patient(identifier: str):
    data = require_json_object(request.get_json(silent=True))
    return success(service().reclassify_patient(identifier.upper(), data))


@api_bp.post("/patients/<identifier>/complete")
@require_roles("medico", "enfermagem", "administrador")
def complete_patient(identifier: str):
    return success(service().complete_patient(identifier.upper()))


@api_bp.post("/patients/<identifier>/cancel")
@require_roles("recepcao", "enfermagem", "administrador")
def cancel_patient(identifier: str):
    return success(service().cancel_patient(identifier.upper()))


@api_bp.post("/doctors")
@require_roles("administrador")
def create_doctor():
    data = require_json_object(request.get_json(silent=True))
    return success(service().create_doctor(data), 201)


@api_bp.get("/doctors")
def get_doctors():
    return success(
        service().list_doctors(
            status=request.args.get("status", "").strip(),
            query=request.args.get("q", "").strip(),
        )
    )


@api_bp.patch("/doctors/<identifier>/status")
@require_roles("administrador")
def update_doctor_status(identifier: str):
    data = require_json_object(request.get_json(silent=True))
    return success(service().set_doctor_status(identifier.upper(), str(data.get("situacao", ""))))


@api_bp.post("/attendances/call-next")
@require_roles("enfermagem", "administrador")
def call_next():
    return success(service().call_next(), 201)


@api_bp.get("/search")
def search():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        raise ValidationError("Informe pelo menos dois caracteres para buscar.")
    return success(service().search(query))


@api_bp.get("/history")
def history():
    return success(
        service().history(
            page=positive_int("page", 1),
            per_page=positive_int("per_page", 20),
        )
    )


@api_bp.get("/structures")
def structures():
    return success(service().state()["structures"])


@api_bp.get("/reports/summary")
def report_summary():
    state = service().state()
    return success(
        {
            "generated_at": state["server_time"],
            "metrics": state["metrics"],
            "audit_events": len(state["audit"]),
            "total_patients": len(state["patients"]),
            "total_doctors": len(state["doctors"]),
        }
    )


@api_bp.get("/reports/shift.csv")
def export_shift():
    state = service().state()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Paciente", "Prioridade", "Chegada", "Situação", "Médico"])
    for patient in state["patients"]:
        writer.writerow(
            [
                patient["id"],
                patient["nome"],
                patient["prioridade"],
                patient["horario_chegada_iso"],
                patient["situacao"],
                patient["medico_id"] or "",
            ]
        )
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=sigae-plantao.csv"},
    )


@api_bp.post("/reset")
@require_roles("administrador")
def reset():
    service().reset()
    return success(service().state())


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ValidationError)
    def validation_error(error: ValidationError):
        return (
            jsonify(
                {
                    "error": {
                        "code": "validation_error",
                        "message": error.message,
                        "fields": error.fields,
                    }
                }
            ),
            400,
        )

    @app.errorhandler(ConflictError)
    def conflict_error(error: ConflictError):
        return jsonify({"error": {"code": "conflict", "message": str(error)}}), 409

    @app.errorhandler(NotFoundError)
    def not_found_error(error: NotFoundError):
        return jsonify({"error": {"code": "not_found", "message": str(error)}}), 404

    @app.errorhandler(DomainError)
    def domain_error(error: DomainError):
        return jsonify({"error": {"code": "domain_error", "message": str(error)}}), 422

    @app.errorhandler(404)
    def route_not_found(error: Exception) -> Response:
        if request.path.startswith("/api/"):
            return jsonify(
                {"error": {"code": "route_not_found", "message": "Rota não encontrada."}}
            ), 404
        return error
