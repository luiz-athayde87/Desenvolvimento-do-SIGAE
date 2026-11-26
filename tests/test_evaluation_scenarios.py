from __future__ import annotations


def data(response):
    return response.get_json()["data"]


def test_three_doctors_receive_balanced_calls_with_deterministic_tiebreak(
    client, monkeypatch
) -> None:
    instants = iter(range(1_000, 2_000, 10))
    monkeypatch.setattr("sigae.service.now_epoch", lambda: next(instants))

    selected: list[str] = []
    for _ in range(4):
        attendance = data(client.post("/api/v1/attendances/call-next"))
        selected.append(attendance["doctor"]["id"])
        completed = client.post(
            f"/api/v1/patients/{attendance['patient']['id']}/complete"
        )
        assert completed.status_code == 200

    assert selected == ["M101", "M102", "M103", "M101"]
    doctors = data(client.get("/api/v1/doctors"))
    loads = {doctor["id"]: doctor["atendimentos_concluidos"] for doctor in doctors}
    assert loads == {"M101": 2, "M102": 1, "M103": 1}


def test_busy_doctor_is_not_reused_and_patient_survives_without_available_doctor(
    client,
) -> None:
    first = data(client.post("/api/v1/attendances/call-next"))
    second = data(client.post("/api/v1/attendances/call-next"))
    third = data(client.post("/api/v1/attendances/call-next"))
    assert [first["doctor"]["id"], second["doctor"]["id"], third["doctor"]["id"]] == [
        "M101",
        "M102",
        "M103",
    ]

    before = [patient["id"] for patient in data(client.get("/api/v1/state"))["waiting_queue"]]
    blocked = client.post("/api/v1/attendances/call-next")
    after = [patient["id"] for patient in data(client.get("/api/v1/state"))["waiting_queue"]]

    assert blocked.status_code == 422
    assert blocked.get_json()["error"]["message"] == "Nenhum médico está disponível no momento."
    assert after == before


def test_cancellation_releases_doctor_without_incrementing_completed_count(client) -> None:
    attendance = data(client.post("/api/v1/attendances/call-next"))
    doctor_id = attendance["doctor"]["id"]
    patient_id = attendance["patient"]["id"]

    cancelled = client.post(f"/api/v1/patients/{patient_id}/cancel")
    doctor = next(
        item for item in data(client.get("/api/v1/doctors")) if item["id"] == doctor_id
    )

    assert cancelled.status_code == 200
    assert data(cancelled)["situacao"] == "Cancelado"
    assert doctor["situacao"] == "Disponivel"
    assert doctor["atendimentos_concluidos"] == 0


def test_red_black_index_contains_only_waiting_patients_in_arrival_order(app, client) -> None:
    service = app.extensions["sigae_service"]
    expected = [
        (patient["horario_chegada"], patient["id"])
        for patient in data(client.get("/api/v1/state"))["patients"]
        if patient["situacao"] == "Aguardando"
    ]

    assert [item["chave"] for item in service.arrival_rb.em_ordem()] == sorted(expected)
    assert service.arrival_rb.validar_propriedades()["ok"] is True

    client.post("/api/v1/patients/P01/cancel")
    client.post("/api/v1/attendances/call-next")
    remaining_ids = {
        patient["id"]
        for patient in data(client.get("/api/v1/state"))["waiting_queue"]
    }
    indexed_ids = {item["valor"]["id"] for item in service.arrival_rb.em_ordem()}

    assert indexed_ids == remaining_ids
    assert "P01" not in indexed_ids
    assert service.arrival_rb.validar_propriedades()["ok"] is True


def test_reclassification_call_completion_and_cancellation_leave_no_orphans(
    app, client
) -> None:
    assert client.patch("/api/v1/patients/P05/priority", json={"prioridade": 1}).status_code == 200
    started = data(client.post("/api/v1/attendances/call-next"))
    patient_id = started["patient"]["id"]
    doctor_id = started["doctor"]["id"]
    assert client.post(f"/api/v1/patients/{patient_id}/cancel").status_code == 200

    state = data(client.get("/api/v1/state"))
    assert all(item["patient_id"] != patient_id for item in state["active_attendances"])
    assert patient_id not in {item["id"] for item in state["waiting_queue"]}
    doctor = next(item for item in state["doctors"] if item["id"] == doctor_id)
    assert doctor["situacao"] == "Disponivel"
    assert doctor["atendimentos_concluidos"] == 0

    with app.extensions["sigae_database"].connection() as connection:
        attendance = connection.execute(
            "SELECT status, ended_seconds FROM attendances WHERE patient_id = ?", (patient_id,)
        ).fetchone()
    assert attendance["status"] == "Cancelado"
    assert attendance["ended_seconds"] is not None
