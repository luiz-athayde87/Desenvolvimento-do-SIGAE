from __future__ import annotations

import time

from sigae import create_app


def data(response):
    return response.get_json()["data"]


def test_each_dashboard_category_has_an_independent_route(client) -> None:
    routes = {
        "/": "Visão geral",
        "/patients": "Pacientes",
        "/triage": "Triagem de risco",
        "/queue": "Fila de atendimento",
        "/doctors": "Corpo médico",
        "/history": "Histórico",
        "/reports": "Relatórios",
        "/structures": "Estruturas de dados",
        "/settings": "Configurações",
    }

    for route, title in routes.items():
        response = client.get(route)
        assert response.status_code == 200
        assert f"<h1>{title}</h1>".encode() in response.data
        assert b"static/css/app.css" in response.data


def test_state_and_new_patient_use_real_timestamps(client) -> None:
    before = int(time.time())
    state = data(client.get("/api/v1/state"))
    created = data(
        client.post(
            "/api/v1/patients",
            json={
                "id": "P90",
                "nome": "Paciente Tempo Real",
                "queixa": "Dor abdominal",
                "prioridade": 3,
            },
        )
    )
    after = int(time.time())

    assert before <= state["clock_seconds"] <= after
    assert state["server_time"].endswith("Z")
    assert before <= created["horario_chegada"] <= after
    assert created["horario_chegada_iso"].endswith("Z")
    assert created["tempo_espera_minutos"] == 0
    assert created["queixa"] == "Dor abdominal"


def test_patient_filters_pagination_and_operational_metrics(client) -> None:
    priority_one = data(client.get("/api/v1/patients?priority=1&per_page=2"))
    waiting = data(client.get("/api/v1/patients?status=Aguardando&page=1&per_page=2"))
    summary = data(client.get("/api/v1/reports/summary"))

    assert all(patient["prioridade"] == 1 for patient in priority_one["items"])
    assert len(waiting["items"]) == 2
    assert waiting["pagination"]["total"] == 5
    assert waiting["pagination"]["pages"] == 3
    assert summary["metrics"]["waiting"] == 5
    assert summary["generated_at"].endswith("Z")


def test_doctor_availability_and_history_endpoints(client) -> None:
    unavailable = client.patch("/api/v1/doctors/M103/status", json={"situacao": "Indisponivel"})
    filtered = data(client.get("/api/v1/doctors?status=Indisponivel"))
    client.post("/api/v1/attendances/call-next")
    history = data(client.get("/api/v1/history"))

    assert unavailable.status_code == 200
    assert [doctor["id"] for doctor in filtered] == ["M103"]
    assert history["pagination"]["total"] == 1
    assert history["items"][0]["started_at"].endswith("Z")


def test_database_migrations_are_versioned(app) -> None:
    database = app.extensions["sigae_database"]
    with database.connection() as connection:
        versions = [
            row["version"]
            for row in connection.execute("SELECT version FROM schema_migrations ORDER BY version")
        ]
        patient_columns = {row["name"] for row in connection.execute("PRAGMA table_info(patients)")}
        doctor_columns = {row["name"] for row in connection.execute("PRAGMA table_info(doctors)")}

    assert versions == [1, 2]
    assert "complaint" in patient_columns
    assert "specialty" in doctor_columns


def test_administrator_can_manage_users_with_csrf() -> None:
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
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "operador", "password": "senha-segura"},
        ).get_json()
        headers = {"X-CSRF-Token": login["csrf_token"]}
        created = client.post(
            "/api/v1/auth/users",
            json={"username": "enfermeira", "password": "senha-123", "role": "enfermagem"},
            headers=headers,
        )
        users = data(client.get("/api/v1/auth/users"))
        user = next(item for item in users if item["username"] == "enfermeira")
        disabled = client.patch(
            f"/api/v1/auth/users/{user['id']}/active",
            json={"active": False},
            headers=headers,
        )

        assert created.status_code == 201
        assert disabled.status_code == 200
        assert data(disabled)["active"] is False
    finally:
        app.extensions["sigae_database"].close()


def test_auth_security_rejects_invalid_access_and_rate_limits(monkeypatch) -> None:
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
        invalid_login = client.post(
            "/api/v1/auth/login",
            json={"username": "operador", "password": "incorreta"},
        )
        unauthenticated_users = client.get("/api/v1/auth/users")

        monkeypatch.setattr("sigae.auth.login_rate_limited", lambda _identifier: True)
        rate_limited = client.post(
            "/api/v1/auth/login",
            json={"username": "operador", "password": "senha-segura"},
        )

        assert invalid_login.status_code == 401
        assert unauthenticated_users.status_code == 401
        assert rate_limited.status_code == 429
        assert rate_limited.get_json()["error"]["code"] == "rate_limit"
    finally:
        app.extensions["sigae_database"].close()


def test_user_management_validation_conflicts_and_logout() -> None:
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
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "operador", "password": "senha-segura"},
        ).get_json()
        headers = {"X-CSRF-Token": login["csrf_token"]}

        invalid = client.post(
            "/api/v1/auth/users",
            json={"username": "x", "password": "curta", "role": "desconhecido"},
            headers=headers,
        )
        duplicate = client.post(
            "/api/v1/auth/users",
            json={"username": "operador", "password": "senha-segura", "role": "administrador"},
            headers=headers,
        )
        current_user = data(client.get("/api/v1/auth/users"))[0]
        self_disable = client.patch(
            f"/api/v1/auth/users/{current_user['id']}/active",
            json={"active": False},
            headers=headers,
        )
        missing = client.patch(
            "/api/v1/auth/users/9999/active",
            json={"active": False},
            headers=headers,
        )
        invalid_csrf = client.post("/api/v1/auth/logout")
        logout = client.post("/api/v1/auth/logout", headers=headers)

        assert invalid.status_code == 400
        assert duplicate.status_code == 409
        assert self_disable.status_code == 409
        assert missing.status_code == 404
        assert invalid_csrf.status_code == 403
        assert logout.status_code == 204
    finally:
        app.extensions["sigae_database"].close()
