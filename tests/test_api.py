from __future__ import annotations

from sigae import create_app


def payload(response):
    return response.get_json()["data"]


def test_health_state_and_security_headers(client) -> None:
    health = client.get("/api/v1/health")
    state = client.get("/api/v1/state")

    assert health.status_code == 200
    assert payload(health)["status"] == "healthy"
    assert payload(health)["database"] == "ready"
    assert state.status_code == 200
    assert len(payload(state)["waiting_queue"]) == 5
    assert len(payload(state)["doctors"]) == 3
    assert state.headers["X-Content-Type-Options"] == "nosniff"
    assert state.headers["Cache-Control"] == "no-store"
    assert state.headers["X-Request-ID"]
    assert state.headers["Server-Timing"].startswith("app;dur=")


def test_patient_validation_and_duplicate_conflict(client) -> None:
    invalid = client.post("/api/v1/patients", json={"nome": "", "prioridade": 9})
    created = client.post(
        "/api/v1/patients", json={"id": "P90", "nome": "Paciente Teste", "prioridade": 3}
    )
    duplicate = client.post(
        "/api/v1/patients", json={"id": "P90", "nome": "Outro", "prioridade": 2}
    )

    assert invalid.status_code == 400
    assert invalid.get_json()["error"]["code"] == "validation_error"
    assert created.status_code == 201
    assert payload(created)["id"] == "P90"
    assert duplicate.status_code == 409


def test_full_attendance_lifecycle_updates_doctor_load(client) -> None:
    call = client.post("/api/v1/attendances/call-next")
    assert call.status_code == 201
    attendance = payload(call)
    assert attendance["patient"]["id"] == "P02"
    assert attendance["doctor"]["situacao"] == "Em atendimento"

    complete = client.post(f"/api/v1/patients/{attendance['patient']['id']}/complete")
    assert complete.status_code == 200
    assert payload(complete)["situacao"] == "Concluido"

    state = payload(client.get("/api/v1/state"))
    doctor = next(item for item in state["doctors"] if item["id"] == attendance["doctor"]["id"])
    assert doctor["situacao"] == "Disponivel"
    assert doctor["atendimentos_concluidos"] == 1
    assert state["structures"]["avl"] is not None
    assert len(state["active_attendances"]) == 0


def test_reclassification_search_csv_and_reset(client) -> None:
    reclassified = client.patch("/api/v1/patients/P05/priority", json={"prioridade": 1})
    assert reclassified.status_code == 200

    state = payload(client.get("/api/v1/state"))
    assert state["waiting_queue"][0]["id"] == "P02"
    assert state["waiting_queue"][1]["id"] == "P05"

    search = client.get("/api/v1/search?q=Maria")
    report = client.get("/api/v1/reports/shift.csv")
    reset = client.post("/api/v1/reset")

    assert search.status_code == 200
    assert payload(search)[0]["id"] == "P02"
    assert report.status_code == 200
    assert "text/csv" in report.content_type
    assert report.data.startswith("\ufeff".encode())
    assert reset.status_code == 200
    assert len(payload(reset)["waiting_queue"]) == 5


def test_authentication_roles_and_csrf() -> None:
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": ":memory:",
            "SECRET_KEY": "test-secret",
            "AUTH_REQUIRED": True,
            "DEMO_USER": "operador",
            "DEMO_PASSWORD": "senha-segura",
        }
    )
    try:
        client = app.test_client()

        session_before = client.get("/api/v1/auth/me")
        denied = client.post("/api/v1/patients", json={"nome": "Teste", "prioridade": 3})
        login = client.post(
            "/api/v1/auth/login", json={"username": "operador", "password": "senha-segura"}
        )
        token = login.get_json()["csrf_token"]
        allowed = client.post(
            "/api/v1/patients",
            json={"nome": "Teste Autenticado", "prioridade": 3},
            headers={"X-CSRF-Token": token},
        )

        assert denied.status_code == 401
        assert session_before.get_json() == {
            "authenticated": False,
            "auth_required": True,
        }
        assert login.status_code == 200
        assert allowed.status_code == 201

        session_after = client.get("/api/v1/auth/me").get_json()
        assert session_after["authenticated"] is True
        assert session_after["user"]["role"] == "administrador"
    finally:
        app.extensions["sigae_database"].close()


def test_legacy_routes_remain_available(client) -> None:
    state = client.get("/api/estado")
    search = client.get("/api/buscar/P02")

    assert state.status_code == 200
    assert "heap_pacientes" in state.get_json()
    assert search.status_code == 200
    assert search.get_json()["encontrado"] is True


def test_api_errors_and_empty_operational_states(client) -> None:
    invalid_body = client.post(
        "/api/v1/patients", data="[]", content_type="application/json"
    )
    assert invalid_body.status_code == 400
    assert client.get("/api/v1/search?q=x").status_code == 400
    assert client.get("/api/v1/patients/P999").status_code == 404
    assert client.get("/api/v1/route-that-does-not-exist").status_code == 404

    for identifier in ("P02", "P03", "P04", "P01", "P05"):
        assert client.post(f"/api/v1/patients/{identifier}/cancel").status_code == 200
    empty_queue = client.post("/api/v1/attendances/call-next")

    assert empty_queue.status_code == 422
    assert empty_queue.get_json()["error"]["code"] == "domain_error"
