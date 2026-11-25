"""Persistência SQLite do estado operacional e da auditoria."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS doctors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    crm TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('Disponivel', 'Em atendimento', 'Indisponivel')),
    completed INTEGER NOT NULL DEFAULT 0 CHECK (completed >= 0),
    last_service_seconds INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 5),
    arrival_seconds INTEGER NOT NULL CHECK (arrival_seconds >= 0),
    status TEXT NOT NULL
        CHECK (status IN ('Aguardando', 'Em atendimento', 'Concluido', 'Cancelado')),
    doctor_id TEXT,
    started_seconds INTEGER,
    ended_seconds INTEGER,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

CREATE TABLE IF NOT EXISTS attendances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    doctor_id TEXT NOT NULL,
    priority INTEGER NOT NULL,
    started_seconds INTEGER NOT NULL,
    ended_seconds INTEGER,
    status TEXT NOT NULL CHECK (status IN ('Em atendimento', 'Concluido', 'Cancelado')),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    detail_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('recepcao', 'enfermagem', 'medico', 'administrador')),
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_patients_status_priority
    ON patients(status, priority, arrival_seconds);
CREATE INDEX IF NOT EXISTS idx_attendances_status
    ON attendances(status, started_seconds);
CREATE INDEX IF NOT EXISTS idx_audit_created_at
    ON audit_log(created_at DESC);
"""


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._memory_connection: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        if self.path == ":memory:":
            if self._memory_connection is None:
                self._memory_connection = sqlite3.connect(":memory:", check_same_thread=False)
                self._memory_connection.row_factory = sqlite3.Row
                self._memory_connection.execute("PRAGMA foreign_keys = ON")
            return self._memory_connection
        connection = sqlite3.connect(self.path, timeout=10, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            if self.path != ":memory:":
                connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(SCHEMA)

    def close(self) -> None:
        """Encerra a conexão compartilhada usada por bancos em memória."""
        if self._memory_connection is not None:
            self._memory_connection.close()
            self._memory_connection = None

    def audit(
        self,
        connection: sqlite3.Connection,
        event: str,
        entity_type: str,
        entity_id: str | None,
        detail: dict[str, Any],
    ) -> None:
        connection.execute(
            "INSERT INTO audit_log(event, entity_type, entity_id, detail_json) VALUES (?, ?, ?, ?)",
            (event, entity_type, entity_id, json.dumps(detail, ensure_ascii=False)),
        )

    def get_metadata(self, key: str, default: str) -> str:
        with self.connection() as connection:
            row = connection.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
        return str(row["value"]) if row else default

    def set_metadata(self, connection: sqlite3.Connection, key: str, value: object) -> None:
        connection.execute(
            "INSERT INTO metadata(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
