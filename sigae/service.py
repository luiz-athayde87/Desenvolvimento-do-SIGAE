"""Serviço de domínio e fonte única de verdade do SIGAE."""

from __future__ import annotations

import json
import math
import sqlite3
import threading
from typing import Any

from arvore_avl import ArvoreAVL
from arvore_rubro_negra import ArvoreRubroNegra
from heap_medicos import MinHeapMedicos
from heap_pacientes import MinHeapPacientes
from tabela_hash import TabelaHash

from .database import Database
from .timeutils import iso_from_epoch, minutes_since, now_epoch
from .validation import ValidationError, optional_id, priority_field, text_field


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
        self.arrival_rb = ArvoreRubroNegra()
        self.history_avl = ArvoreAVL()
        self.db.initialize()
        self._seed_if_empty()
        self._upgrade_legacy_timestamps()
        self._rebuild_indexes()

    @staticmethod
    def _patient_public(row: sqlite3.Row, current_time: int | None = None) -> dict[str, Any]:
        now = current_time or now_epoch()
        arrival = int(row["arrival_seconds"])
        started = row["started_seconds"]
        ended = row["ended_seconds"]
        wait_end = int(started) if started else now
        ended_or_now = int(ended) if ended else now
        return {
            "id": row["id"],
            "nome": row["name"],
            "queixa": row["complaint"],
            "prioridade": row["priority"],
            "horario_chegada": arrival,
            "horario_chegada_iso": iso_from_epoch(arrival),
            "situacao": row["status"],
            "medico_id": row["doctor_id"],
            "inicio_atendimento": started,
            "inicio_atendimento_iso": iso_from_epoch(started),
            "fim_atendimento": ended,
            "fim_atendimento_iso": iso_from_epoch(ended),
            "tempo_espera_minutos": minutes_since(arrival, wait_end),
            "tempo_total_minutos": minutes_since(arrival, ended_or_now),
        }

    @staticmethod
    def _doctor_public(row: sqlite3.Row) -> dict[str, Any]:
        last_service = int(row["last_service_seconds"] or 0)
        return {
            "id": row["id"],
            "nome": row["name"],
            "crm": row["crm"],
            "especialidade": row["specialty"],
            "situacao": row["status"],
            "atendimentos_concluidos": row["completed"],
            "ultimo_atendimento": last_service,
            "ultimo_atendimento_iso": iso_from_epoch(last_service),
        }

    def _seed_if_empty(self) -> None:
        current_time = now_epoch()
        with self.db.connection() as connection:
            total = connection.execute("SELECT COUNT(*) AS total FROM doctors").fetchone()["total"]
            if total:
                return
            connection.executemany(
                "INSERT INTO doctors(id, name, crm, status) VALUES (?, ?, ?, 'Disponivel')",
                [
                    ("M101", "Dr. Carlos Mendes", "CRM-RJ 520101"),
                    ("M102", "Dra. Beatriz Lima", "CRM-RJ 520102"),
                    ("M103", "Dr. André Carvalho", "CRM-RJ 520103"),
                ],
            )
            connection.executemany(
                "INSERT INTO patients(id, name, priority, arrival_seconds, status) "
                "VALUES (?, ?, ?, ?, 'Aguardando')",
                [
                    ("P01", "João Silva", 4, current_time - 50 * 60),
                    ("P02", "Maria Oliveira", 1, current_time - 42 * 60),
                    ("P03", "Pedro Souza", 2, current_time - 35 * 60),
                    ("P04", "Ana Costa", 3, current_time - 27 * 60),
                    ("P05", "Fernanda Alves", 5, current_time - 15 * 60),
                ],
            )
            self.db.set_metadata(connection, "patient_counter", 6)
            self.db.set_metadata(connection, "doctor_counter", 104)
            self.db.audit(connection, "shift.seeded", "system", None, {"demo": True})

    def _upgrade_legacy_timestamps(self) -> None:
        """Converte os antigos segundos simulados em instantes Unix reais."""
        with self.db.connection() as connection:
            row = connection.execute(
                "SELECT MAX(arrival_seconds) AS maximum FROM patients"
            ).fetchone()
            maximum = int(row["maximum"] or 0)
            if maximum == 0 or maximum >= 1_000_000_000:
                return
            offset = now_epoch() - maximum
            connection.execute(
                "UPDATE patients SET arrival_seconds = arrival_seconds + ?, "
                "started_seconds = CASE WHEN started_seconds IS NULL THEN NULL "
                "ELSE started_seconds + ? END, "
                "ended_seconds = CASE WHEN ended_seconds IS NULL THEN NULL "
                "ELSE ended_seconds + ? END",
                (offset, offset, offset),
            )
            connection.execute(
                "UPDATE attendances SET started_seconds = started_seconds + ?, "
                "ended_seconds = CASE WHEN ended_seconds IS NULL THEN NULL "
                "ELSE ended_seconds + ? END",
                (offset, offset),
            )
            connection.execute(
                "UPDATE doctors SET last_service_seconds = last_service_seconds + ? "
                "WHERE last_service_seconds > 0",
                (offset,),
            )
            self.db.audit(
                connection,
                "system.timestamps_migrated",
                "system",
                None,
                {"offset_seconds": offset},
            )

    def _rebuild_indexes(self) -> None:
        self.hash = TabelaHash()
        self.patient_heap = MinHeapPacientes()
        self.doctor_heap = MinHeapMedicos()
        self.arrival_rb = ArvoreRubroNegra()
        self.history_avl = ArvoreAVL()
        current_time = now_epoch()
        with self.db.connection() as connection:
            for row in connection.execute("SELECT * FROM patients ORDER BY arrival_seconds, id"):
                patient = self._patient_public(row, current_time)
                self.hash.inserir(patient["id"], patient)
                if patient["situacao"] == "Aguardando":
                    self.patient_heap.inserir(patient)
                    self.arrival_rb.inserir(
                        (patient["horario_chegada"], patient["id"]), patient
                    )
            for row in connection.execute("SELECT * FROM doctors ORDER BY id"):
                doctor = self._doctor_public(row)
                self.hash.inserir(doctor["id"], doctor)
                if doctor["situacao"] == "Disponivel":
                    self.doctor_heap.inserir(doctor)
            for row in connection.execute("SELECT * FROM attendances ORDER BY id"):
                record = dict(row)
                self.history_avl.inserir_no(row["id"], record)

    def _next_id(self, connection: sqlite3.Connection, key: str, prefix: str, width: int) -> str:
        row = connection.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
        number = int(row["value"]) if row else 1
        self.db.set_metadata(connection, key, number + 1)
        return f"{prefix}{number:0{width}d}"

    @staticmethod
    def _paginate(page: int, per_page: int) -> tuple[int, int]:
        return max(1, page), min(100, max(1, per_page))

    @staticmethod
    def _where(clauses: list[str]) -> str:
        return f"WHERE {' AND '.join(clauses)}" if clauses else ""

    def _set_doctor_available(
        self,
        connection: sqlite3.Connection,
        doctor_id: str,
        current_time: int,
        *,
        increment_completed: bool = False,
    ) -> None:
        if increment_completed:
            connection.execute(
                "UPDATE doctors SET status = 'Disponivel', completed = completed + 1, "
                "last_service_seconds = ? WHERE id = ?",
                (current_time, doctor_id),
            )
        else:
            connection.execute(
                "UPDATE doctors SET status = 'Disponivel', last_service_seconds = ? WHERE id = ?",
                (current_time, doctor_id),
            )

    def create_patient(self, data: dict[str, Any]) -> dict[str, Any]:
        name = text_field(data, "nome", "Nome")
        priority = priority_field(data)
        complaint = str(data.get("queixa", "")).strip()
        if len(complaint) > 500:
            raise ValidationError(
                "Revise os campos informados.",
                {"queixa": "Queixa principal deve ter até 500 caracteres."},
            )
        requested_id = optional_id(data, ("P", "PAC-"))
        current_time = now_epoch()
        with self.lock, self.db.connection() as connection:
            identifier = requested_id or self._next_id(connection, "patient_counter", "P", 2)
            if connection.execute("SELECT 1 FROM patients WHERE id = ?", (identifier,)).fetchone():
                raise ConflictError(f"Já existe um paciente com o ID {identifier}.")
            connection.execute(
                "INSERT INTO patients(id, name, complaint, priority, arrival_seconds, status) "
                "VALUES (?, ?, ?, ?, ?, 'Aguardando')",
                (identifier, name, complaint, priority, current_time),
            )
            self.db.audit(
                connection,
                "patient.created",
                "patient",
                identifier,
                {"name": name, "priority": priority, "complaint": complaint},
            )
        self._rebuild_indexes()
        return self.get_patient(identifier)

    def create_doctor(self, data: dict[str, Any]) -> dict[str, Any]:
        name = text_field(data, "nome", "Nome")
        crm = text_field(data, "crm", "CRM", 40) if data.get("crm") else f"DEMO-{name[:12]}"
        specialty = str(data.get("especialidade", "Clínica Geral")).strip() or "Clínica Geral"
        if len(specialty) > 80:
            raise ValidationError(
                "Revise os campos informados.",
                {"especialidade": "Especialidade deve ter até 80 caracteres."},
            )
        requested_id = optional_id(data, ("M", "MED-"))
        with self.lock, self.db.connection() as connection:
            identifier = requested_id or self._next_id(connection, "doctor_counter", "M", 3)
            existing = connection.execute(
                "SELECT id FROM doctors WHERE id = ? OR crm = ?", (identifier, crm)
            ).fetchone()
            if existing:
                raise ConflictError("Já existe um médico com esse ID ou CRM.")
            connection.execute(
                "INSERT INTO doctors(id, name, crm, specialty, status) "
                "VALUES (?, ?, ?, ?, 'Disponivel')",
                (identifier, name, crm, specialty),
            )
            self.db.audit(
                connection,
                "doctor.created",
                "doctor",
                identifier,
                {"name": name, "crm": crm, "specialty": specialty},
            )
        self._rebuild_indexes()
        return self.get_doctor(identifier)

    def set_doctor_status(self, identifier: str, status: str) -> dict[str, Any]:
        normalized = status.strip().capitalize()
        if normalized not in {"Disponivel", "Indisponivel"}:
            raise DomainError("Situação deve ser Disponivel ou Indisponivel.")
        with self.lock, self.db.connection() as connection:
            doctor = connection.execute(
                "SELECT * FROM doctors WHERE id = ?", (identifier,)
            ).fetchone()
            if doctor is None:
                raise NotFoundError("Médico não encontrado.")
            if doctor["status"] == "Em atendimento":
                raise ConflictError("Finalize o atendimento antes de alterar a disponibilidade.")
            connection.execute(
                "UPDATE doctors SET status = ? WHERE id = ?", (normalized, identifier)
            )
            self.db.audit(
                connection,
                "doctor.status_changed",
                "doctor",
                identifier,
                {"from": doctor["status"], "to": normalized},
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
            current_time = now_epoch()
            with self.db.connection() as connection:
                connection.execute(
                    "UPDATE patients SET status = 'Em atendimento', doctor_id = ?, "
                    "started_seconds = ? WHERE id = ? AND status = 'Aguardando'",
                    (doctor["id"], current_time, patient["id"]),
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
                    (patient["id"], doctor["id"], patient["prioridade"], current_time),
                )
                self.db.audit(
                    connection,
                    "attendance.started",
                    "attendance",
                    str(cursor.lastrowid),
                    {"patient_id": patient["id"], "doctor_id": doctor["id"]},
                )
            self.patient_heap.extrair_proximo()
            self.doctor_heap.extrair_proximo()
            self.arrival_rb.remover((patient["horario_chegada"], patient["id"]))
            self._rebuild_indexes()
            return {
                "attendance_id": cursor.lastrowid,
                "patient": self.get_patient(patient["id"]),
                "doctor": self.get_doctor(doctor["id"]),
                "started_seconds": current_time,
                "started_at": iso_from_epoch(current_time),
            }

    def complete_patient(self, identifier: str) -> dict[str, Any]:
        current_time = now_epoch()
        with self.lock, self.db.connection() as connection:
            row = connection.execute(
                "SELECT * FROM patients WHERE id = ? AND status = 'Em atendimento'", (identifier,)
            ).fetchone()
            if row is None:
                raise NotFoundError("Atendimento ativo não encontrado.")
            connection.execute(
                "UPDATE patients SET status = 'Concluido', ended_seconds = ? WHERE id = ?",
                (current_time, identifier),
            )
            connection.execute(
                "UPDATE attendances SET status = 'Concluido', ended_seconds = ? "
                "WHERE patient_id = ? AND status = 'Em atendimento'",
                (current_time, identifier),
            )
            self._set_doctor_available(
                connection, row["doctor_id"], current_time, increment_completed=True
            )
            self.db.audit(connection, "attendance.completed", "patient", identifier, {})
        self.doctor_heap.inserir(self.get_doctor(row["doctor_id"]))
        self._rebuild_indexes()
        return self.get_patient(identifier)

    def cancel_patient(self, identifier: str) -> dict[str, Any]:
        current_time = now_epoch()
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
                (current_time, identifier),
            )
            if row["status"] == "Em atendimento":
                connection.execute(
                    "UPDATE attendances SET status = 'Cancelado', ended_seconds = ? "
                    "WHERE patient_id = ? AND status = 'Em atendimento'",
                    (current_time, identifier),
                )
                self._set_doctor_available(connection, row["doctor_id"], current_time)
            self.db.audit(connection, "patient.cancelled", "patient", identifier, {})
        if row["status"] == "Aguardando":
            self.patient_heap.remover(identifier)
            self.arrival_rb.remover((int(row["arrival_seconds"]), identifier))
        else:
            self.doctor_heap.inserir(self.get_doctor(row["doctor_id"]))
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
        self.patient_heap.atualizar_prioridade(identifier, priority)
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

    def list_patients(
        self,
        *,
        status: str = "",
        priority: int | None = None,
        query: str = "",
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if status:
            clauses.append("status = ?")
            parameters.append(status)
        if priority is not None:
            clauses.append("priority = ?")
            parameters.append(priority)
        if query:
            clauses.append("(id LIKE ? OR name LIKE ?)")
            term = f"%{query}%"
            parameters.extend((term, term))
        where = self._where(clauses)
        page, per_page = self._paginate(page, per_page)
        with self.db.connection() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS total FROM patients {where}", parameters
            ).fetchone()["total"]
            rows = connection.execute(
                f"SELECT * FROM patients {where} ORDER BY arrival_seconds DESC LIMIT ? OFFSET ?",
                [*parameters, per_page, (page - 1) * per_page],
            ).fetchall()
        return {
            "items": [self._patient_public(row) for row in rows],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": max(1, math.ceil(total / per_page)),
            },
        }

    def list_doctors(self, *, status: str = "", query: str = "") -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if status:
            clauses.append("status = ?")
            parameters.append(status)
        if query:
            clauses.append("(id LIKE ? OR name LIKE ? OR crm LIKE ? OR specialty LIKE ?)")
            term = f"%{query}%"
            parameters.extend((term, term, term, term))
        where = self._where(clauses)
        with self.db.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM doctors {where} ORDER BY name", parameters
            ).fetchall()
        return [self._doctor_public(row) for row in rows]

    def history(self, *, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        page, per_page = self._paginate(page, per_page)
        with self.db.connection() as connection:
            total = connection.execute("SELECT COUNT(*) AS total FROM attendances").fetchone()[
                "total"
            ]
            rows = connection.execute(
                "SELECT a.*, p.name AS patient_name, d.name AS doctor_name "
                "FROM attendances a JOIN patients p ON p.id = a.patient_id "
                "JOIN doctors d ON d.id = a.doctor_id "
                "ORDER BY a.started_seconds DESC LIMIT ? OFFSET ?",
                (per_page, (page - 1) * per_page),
            ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["started_at"] = iso_from_epoch(item["started_seconds"])
            item["ended_at"] = iso_from_epoch(item["ended_seconds"])
            item["duration_minutes"] = minutes_since(
                item["started_seconds"], item["ended_seconds"] or now_epoch()
            )
            items.append(item)
        return {
            "items": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": max(1, math.ceil(total / per_page)),
            },
        }

    def search(self, query: str) -> list[dict[str, Any]]:
        term = f"%{query.strip()}%"
        with self.db.connection() as connection:
            patients = connection.execute(
                "SELECT id, name, priority, status FROM patients "
                "WHERE id LIKE ? OR name LIKE ? LIMIT 10",
                (term, term),
            ).fetchall()
            doctors = connection.execute(
                "SELECT id, name, crm, specialty, status FROM doctors "
                "WHERE id LIKE ? OR name LIKE ? OR crm LIKE ? OR specialty LIKE ? LIMIT 10",
                (term, term, term, term),
            ).fetchall()
        return [{"type": "patient", **dict(row)} for row in patients] + [
            {"type": "doctor", **dict(row)} for row in doctors
        ]

    def state(self) -> dict[str, Any]:
        current_time = now_epoch()
        with self.db.connection() as connection:
            patients = [
                self._patient_public(row, current_time)
                for row in connection.execute("SELECT * FROM patients")
            ]
            doctors = [
                self._doctor_public(row) for row in connection.execute("SELECT * FROM doctors")
            ]
            active: list[dict[str, Any]] = [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM attendances WHERE status = 'Em atendimento' "
                    "ORDER BY started_seconds"
                )
            ]
            audit: list[dict[str, Any]] = []
            for row in connection.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 50"):
                item = dict(row)
                item["detail"] = json.loads(item.pop("detail_json"))
                audit.append(item)
            revision_row = connection.execute(
                "SELECT MAX(id) AS revision FROM audit_log"
            ).fetchone()
        waiting = sorted(
            (patient for patient in patients if patient["situacao"] == "Aguardando"),
            key=lambda patient: (patient["prioridade"], patient["horario_chegada"], patient["id"]),
        )
        completed = [patient for patient in patients if patient["situacao"] == "Concluido"]
        average_wait = (
            round(sum(patient["tempo_espera_minutos"] or 0 for patient in waiting) / len(waiting))
            if waiting
            else 0
        )
        distribution = {
            str(priority): sum(1 for patient in waiting if patient["prioridade"] == priority)
            for priority in range(1, 6)
        }
        return {
            "server_time": iso_from_epoch(current_time),
            "clock_seconds": current_time,
            "revision": int(revision_row["revision"] or 0),
            "patients": patients,
            "doctors": doctors,
            "waiting_queue": waiting,
            "active_attendances": active,
            "audit": audit,
            "metrics": {
                "waiting": len(waiting),
                "critical": sum(1 for patient in waiting if patient["prioridade"] <= 2),
                "active": len(active),
                "available_doctors": sum(
                    1 for doctor in doctors if doctor["situacao"] == "Disponivel"
                ),
                "completed": len(completed),
                "average_wait_minutes": average_wait,
                "priority_distribution": distribution,
            },
            "structures": {
                "patient_heap": self.patient_heap.exportar_array(),
                "doctor_heap": self.doctor_heap.exportar_array(),
                "hash": self.hash.exportar_buckets(),
                "red_black": self.arrival_rb.exportar_estrutura(),
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
