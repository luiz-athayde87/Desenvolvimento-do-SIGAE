from __future__ import annotations

import uuid
from pathlib import Path

from sigae import create_app


def test_sqlite_state_survives_application_restart() -> None:
    database_path = Path("instance") / f"test-{uuid.uuid4().hex}.db"
    config = {
        "TESTING": True,
        "DATABASE": str(database_path),
        "SECRET_KEY": "test-secret",
        "AUTH_REQUIRED": False,
        "DEMO_USER": "operador",
        "DEMO_PASSWORD": "senha-segura",
    }

    try:
        first_app = create_app(config)
        first_client = first_app.test_client()
        created = first_client.post(
            "/api/v1/patients",
            json={"id": "P90", "nome": "Paciente Persistente", "prioridade": 2},
        )
        assert created.status_code == 201

        second_app = create_app(config)
        second_client = second_app.test_client()
        patient = second_client.get("/api/v1/patients/P90")
        state = second_client.get("/api/v1/state").get_json()["data"]

        assert patient.status_code == 200
        assert patient.get_json()["data"]["nome"] == "Paciente Persistente"
        assert any(item["event"] == "patient.created" for item in state["audit"])
    finally:
        database_path.unlink(missing_ok=True)
