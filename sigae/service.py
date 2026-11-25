"""Serviço de domínio: fonte única de verdade do SIGAE."""

from __future__ import annotations

import json
import threading
from typing import Any

from arvore_avl import ArvoreAVL
from arvore_rubro_negra import ArvoreRubroNegra
from heap_medicos import MinHeapMedicos
from heap_pacientes import MinHeapPacientes
from tabela_hash import TabelaHash

from .database import Database
from .validation import optional_id, priority_field, text_field


class ConflictError(RuntimeError):
    pass


class NotFoundError(RuntimeError):
    pass


class DomainError(RuntimeError):
    pass


class SigaeService:
    def __init__(self, database: Database) -> None:
        self.db = database
        self.lock = threading.RLock()
        self.hash = TabelaHash()
        self.patient_heap = MinHeapPacientes()
        self.doctor_heap = MinHeapMedicos()
        self.history_rb = ArvoreRubroNegra()
        self.history_avl = ArvoreAVL()
        self.clock_seconds = 8 * 3600
        self.db.initialize()
        self._seed_if_empty()
        self._rebuild_indexes()

    @staticmethod
    def _patient_public(row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "nome": row["name"],
            "prioridade": row["priority"],
            "horario_chegada": row["arrival_seconds"],
            "situacao": row["status"],
            "medico_id": row["doctor_id"],
            "inicio_atendimento": row["started_seconds"],
            "fim_atendimento": row["ended_seconds"],
        }

    @staticmethod
    def _doctor_public(row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "nome": row["name"],
            "crm": row["crm"],
            "situacao": row["status"],
            "atendimentos_concluidos": row["completed"],
            "ultimo_atendimento": row["last_service_seconds"],
        }

    def _seed_if_empty(self) -> None:
        with self.db.connection() as connection:
            total = connection.execute("SELECT COUNT(*) AS total FROM doctors").fetchone()["total"]
            if total:
                return
            doctors = [
                ("M101", "Dr. Carlos Mendes", "CRM-RJ 520101"),
                ("M102", "Dra. Beatriz Lima", "CRM-RJ 520102"),
                ("M103", "Dr. André Carvalho", "CRM-RJ 520103"),
            ]
            connection.executemany(
                "INSERT INTO doctors(id, name, crm, status) VALUES (?, ?, ?, 'Disponivel')",
                doctors,
            )
            patients = [
                ("P01", "João Silva", 4, 8 * 3600),
                ("P02", "Maria Oliveira", 1, 8 * 3600 + 120),
                ("P03", "Pedro Souza", 2, 8 * 3600 + 60),
                ("P04", "Ana Costa", 3, 8 * 3600 + 180),
                ("P05", "Fernanda Alves", 5, 8 * 3600 + 240),
            ]
            connection.executemany(
                "INSERT INTO patients(id, name, priority, arrival_seconds, status) "
                "VALUES (?, ?, ?, ?, 'Aguardando')",
                patients,
            )
            self.db.set_metadata(connection, "clock_seconds", 8 * 3600 + 300)
            self.db.set_metadata(connection, "patient_counter", 6)
            self.db.set_metadata(connection, "doctor_counter", 104)
            self.db.audit(connection, "shift.seeded", "system", None, {"demo": True})

    def _rebuild_indexes(self) -> None:
        self.hash = TabelaHash()
        self.patient_heap = MinHeapPacientes()
        self.doctor_heap = MinHeapMedicos()
        self.history_rb = ArvoreRubroNegra()
        self.history_avl = ArvoreAVL()
        self.clock_seconds = int(self.db.get_metadata("clock_seconds", str(8 * 3600)))
        with self.db.connection() as connection:
            for row in connection.execute("SELECT * FROM patients ORDER BY arrival_seconds, id"):
                patient = self._patient_public(row)
                self.hash.inserir(patient["id"], patient)
                if patient["situacao"] == "Aguardando":
                    self.patient_heap.inserir(patient)
            for row in connection.execute("SELECT * FROM doctors ORDER BY id"):
                doctor = self._doctor_public(row)
                self.hash.inserir(doctor["id"], doctor)
                if doctor["situacao"] == "Disponivel":
                    self.doctor_heap.inserir(doctor)
            for row in connection.execute("SELECT * FROM attendances ORDER BY id"):
                record = dict(row)
                self.history_rb.inserir((row["started_seconds"], row["id"]), record)
                self.history_avl.inserir_no(row["id"], record)

    def _next_id(self, connection: Any, key: str, prefix: str, width: int) -> str:
        number = int(
            connection.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()[
                "value"
            ]
        )
        self.db.set_metadata(connection, key, number + 1)
        return f"{prefix}{number:0{width}d}"

    def create_patient(self, data: dict[str, Any]) -> dict[str, Any]:
        name = text_field(data, "nome", "Nome")
        priority = priority_field(data)
        requested_id = optional_id(data, ("P", "PAC-"))
        with self.lock, self.db.connection() as connection:
            identifier = requested_id or self._next_id(connection, "patient_counter", "P", 2)
            if connection.execute("SELECT 1 FROM patients WHERE id = ?", (identifier,)).fetchone():
                raise ConflictError(f"Já existe um paciente com o ID {identifier}.")
            self.clock_seconds += 60
            connection.execute(
                "INSERT INTO patients(id, name, priority, arrival_seconds, status) "
                "VALUES (?, ?, ?, ?, 'Aguardando')",
                (identifier, name, priority, self.clock_seconds),
            )
            self.db.set_metadata(connection, "clock_seconds", self.clock_seconds)
            self.db.audit(
                connection,
                "patient.created",
                "patient",
                identifier,
                {"name": name, "priority": priority},
            )
        self._rebuild_indexes()
        return self.get_patient(identifier)

    def create_doctor(self, data: dict[str, Any]) -> dict[str, Any]:
        name = text_field(data, "nome", "Nome")
        crm = text_field(data, "crm", "CRM", 40) if data.get("crm") else f"DEMO-{name[:12]}"
        requested_id = optional_id(data, ("M", "MED-"))
        with self.lock, self.db.connection() as connection:
            identifier = requested_id or self._next_id(connection, "doctor_counter", "M", 3)
            existing = connection.execute(
                "SELECT id FROM doctors WHERE id = ? OR crm = ?", (identifier, crm)
            ).fetchone()
            if existing:
                raise ConflictError("Já existe um médico com esse ID ou CRM.")
            connection.execute(
                "INSERT INTO doctors(id, name, crm, status) VALUES (?, ?, ?, 'Disponivel')",
                (identifier, name, crm),
            )
            self.db.audit(
                connection, "doctor.created", "doctor", identifier, {"name": name, "crm": crm}
            )
        self._rebuild_indexes()
        return self.get_doctor(identifier)

    def call_next(self) -> dict[str, Any]:
        with self.lock:
            patient = self.patient_heap.topo()
            doctor = self.doctor_heap.topo()
            if patient is None:
                raise DomainError("Nenhum paciente está aguardando na fila.")
            if doctor is None:
                raise DomainError("Nenhum médico está disponível no momento.")
            self.clock_seconds += 60
            with self.db.connection() as connection:
                connection.execute(
                    "UPDATE patients SET status = 'Em atendimento', doctor_id = ?, "
                    "started_seconds = ? "
                    "WHERE id = ? AND status = 'Aguardando'",
                    (doctor["id"], self.clock_seconds, patient["id"]),
                )
                connection.execute(
                    "UPDATE doctors SET status = 'Em atendimento' "
                    "WHERE id = ? AND status = 'Disponivel'",
                    (doctor["id"],),
                )
                cursor = connection.execute(
                    "INSERT INTO attendances("
                    "patient_id, doctor_id, priority, started_seconds, status"
                    ") "
                    "VALUES (?, ?, ?, ?, 'Em atendimento')",
                    (patient["id"], doctor["id"], patient["prioridade"], self.clock_seconds),
                )
                self.db.set_metadata(connection, "clock_seconds", self.clock_seconds)
                self.db.audit(
                    connection,
                    "attendance.started",
                    "attendance",
                    str(cursor.lastrowid),
                    {"patient_id": patient["id"], "doctor_id": doctor["id"]},
                )
            self._rebuild_indexes()
            return {
                "attendance_id": cursor.lastrowid,
                "patient": self.get_patient(patient["id"]),
                "doctor": self.get_doctor(doctor["id"]),
                "started_seconds": self.clock_seconds,
            }

    def complete_patient(self, identifier: str) -> dict[str, Any]:
        with self.lock, self.db.connection() as connection:
            row = connection.execute(
                "SELECT * FROM patients WHERE id = ? AND status = 'Em atendimento'", (identifier,)
            ).fetchone()
            if row is None:
                raise NotFoundError("Atendimento ativo não encontrado.")
            self.clock_seconds += 60
            connection.execute(
                "UPDATE patients SET status = 'Concluido', ended_seconds = ? WHERE id = ?",
                (self.clock_seconds, identifier),
            )
            connection.execute(
                "UPDATE attendances SET status = 'Concluido', ended_seconds = ? "
                "WHERE patient_id = ? AND status = 'Em atendimento'",
                (self.clock_seconds, identifier),
            )
            connection.execute(
                "UPDATE doctors SET status = 'Disponivel', completed = completed + 1, "
                "last_service_seconds = ? WHERE id = ?",
                (self.clock_seconds, row["doctor_id"]),
            )
            self.db.set_metadata(connection, "clock_seconds", self.clock_seconds)
            self.db.audit(connection, "attendance.completed", "patient", identifier, {})
        self._rebuild_indexes()
        return self.get_patient(identifier)

    def cancel_patient(self, identifier: str) -> dict[str, Any]:
        with self.lock, self.db.connection() as connection:
            row = connection.execute(
                "SELECT * FROM patients WHERE id = ?", (identifier,)
            ).fetchone()
            if row is None:
                raise NotFoundError("Paciente não encontrado.")
            if row["status"] not in ("Aguardando", "Em atendimento"):
                raise ConflictError(
                    "Somente pacientes aguardando ou em atendimento podem ser cancelados."
                )
            connection.execute(
                "UPDATE patients SET status = 'Cancelado', ended_seconds = ? WHERE id = ?",
                (self.clock_seconds, identifier),
            )
            if row["status"] == "Em atendimento":
                connection.execute(
                    "UPDATE attendances SET status = 'Cancelado', ended_seconds = ? "
                    "WHERE patient_id = ? AND status = 'Em atendimento'",
                    (self.clock_seconds, identifier),
                )
                connection.execute(
                    "UPDATE doctors SET status = 'Disponivel', last_service_seconds = ? "
                    "WHERE id = ?",
                    (self.clock_seconds, row["doctor_id"]),
                )
            self.db.audit(connection, "patient.cancelled", "patient", identifier, {})
        self._rebuild_indexes()
        return self.get_patient(identifier)

    def reclassify_patient(self, identifier: str, data: dict[str, Any]) -> dict[str, Any]:
        priority = priority_field(data)
        with self.lock, self.db.connection() as connection:
            row = connection.execute(
                "SELECT priority FROM patients WHERE id = ? AND status = 'Aguardando'",
                (identifier,),
            ).fetchone()
            if row is None:
                raise NotFoundError("Paciente aguardando não encontrado.")
            connection.execute(
                "UPDATE patients SET priority = ? WHERE id = ?", (priority, identifier)
            )
            self.db.audit(
                connection,
                "patient.reclassified",
                "patient",
                identifier,
                {"from": row["priority"], "to": priority},
            )
        self._rebuild_indexes()
        return self.get_patient(identifier)

    def get_patient(self, identifier: str) -> dict[str, Any]:
        with self.db.connection() as connection:
            row = connection.execute(
                "SELECT * FROM patients WHERE id = ?", (identifier,)
            ).fetchone()
        if row is None:
            raise NotFoundError("Paciente não encontrado.")
        return self._patient_public(row)

    def get_doctor(self, identifier: str) -> dict[str, Any]:
        with self.db.connection() as connection:
            row = connection.execute("SELECT * FROM doctors WHERE id = ?", (identifier,)).fetchone()
        if row is None:
            raise NotFoundError("Médico não encontrado.")
        return self._doctor_public(row)

    def search(self, query: str) -> list[dict[str, Any]]:
        term = f"%{query.strip()}%"
        with self.db.connection() as connection:
            patients = connection.execute(
                "SELECT id, name, priority, status FROM patients "
                "WHERE id LIKE ? OR name LIKE ? LIMIT 10",
                (term, term),
            ).fetchall()
            doctors = connection.execute(
                "SELECT id, name, crm, status FROM doctors "
                "WHERE id LIKE ? OR name LIKE ? OR crm LIKE ? LIMIT 10",
                (term, term, term),
            ).fetchall()
        return [{"type": "patient", **dict(row)} for row in patients] + [
            {"type": "doctor", **dict(row)} for row in doctors
        ]

    def state(self) -> dict[str, Any]:
        with self.db.connection() as connection:
            patients = [
                self._patient_public(row) for row in connection.execute("SELECT * FROM patients")
            ]
            doctors = [
                self._doctor_public(row) for row in connection.execute("SELECT * FROM doctors")
            ]
            active = [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM attendances WHERE status = 'Em atendimento' "
                    "ORDER BY started_seconds"
                )
            ]
            audit = []
            for row in connection.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 50"):
                item = dict(row)
                item["detail"] = json.loads(item.pop("detail_json"))
                audit.append(item)
        waiting = sorted(
            (patient for patient in patients if patient["situacao"] == "Aguardando"),
            key=lambda patient: (patient["prioridade"], patient["horario_chegada"], patient["id"]),
        )
        return {
            "clock_seconds": self.clock_seconds,
            "patients": patients,
            "doctors": doctors,
            "waiting_queue": waiting,
            "active_attendances": active,
            "audit": audit,
            "structures": {
                "patient_heap": self.patient_heap.exportar_array(),
                "doctor_heap": self.doctor_heap.exportar_array(),
                "hash": self.hash.exportar_buckets(),
                "red_black": self.history_rb.em_ordem(),
                "avl": self.history_avl.exportar_estrutura(),
            },
        }

    def reset(self) -> None:
        with self.lock, self.db.connection() as connection:
            connection.execute("DELETE FROM attendances")
            connection.execute("DELETE FROM patients")
            connection.execute("DELETE FROM doctors")
            connection.execute("DELETE FROM audit_log")
            connection.execute("DELETE FROM metadata")
        self._seed_if_empty()
        self._rebuild_indexes()
