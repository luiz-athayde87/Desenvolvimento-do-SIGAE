"""Autenticação opcional por sessão e papéis de acesso."""

from __future__ import annotations

import secrets
import sqlite3
import threading
import time
from collections import defaultdict, deque
from functools import wraps
from typing import Any, Callable

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .database import Database

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
_login_attempts: dict[str, deque[float]] = defaultdict(deque)
_login_lock = threading.Lock()


def login_rate_limited(identifier: str, limit: int = 10, window_seconds: int = 60) -> bool:
    current = time.monotonic()
    with _login_lock:
        attempts = _login_attempts[identifier]
        while attempts and current - attempts[0] > window_seconds:
            attempts.popleft()
        if len(attempts) >= limit:
            return True
        attempts.append(current)
        return False


def seed_demo_user(database: Database, username: str, password: str) -> None:
    with database.connection() as connection:
        exists = connection.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not exists:
            connection.execute(
                "INSERT INTO users(username, password_hash, role) VALUES (?, ?, 'administrador')",
                (username, generate_password_hash(password)),
            )


def require_roles(*roles: str) -> Callable:
    def decorator(function):
        @wraps(function)
        def wrapped(*args: Any, **kwargs: Any):
            if not current_app.config["AUTH_REQUIRED"]:
                return function(*args, **kwargs)
            if not session.get("user_id"):
                return jsonify(
                    {"error": {"code": "unauthorized", "message": "Autenticação necessária."}}
                ), 401
            if roles and session.get("role") not in roles:
                return jsonify(
                    {"error": {"code": "forbidden", "message": "Acesso não autorizado."}}
                ), 403
            if request.method not in ("GET", "HEAD", "OPTIONS"):
                token = request.headers.get("X-CSRF-Token")
                if not token or not secrets.compare_digest(token, session.get("csrf_token", "")):
                    return jsonify(
                        {"error": {"code": "csrf", "message": "Token CSRF inválido."}}
                    ), 403
            return function(*args, **kwargs)

        return wrapped

    return decorator


@auth_bp.post("/login")
def login():
    remote = request.remote_addr or "unknown"
    if login_rate_limited(remote):
        return jsonify(
            {
                "error": {
                    "code": "rate_limit",
                    "message": "Muitas tentativas. Aguarde um minuto e tente novamente.",
                }
            }
        ), 429
    data = request.get_json(silent=True) or {}
    database: Database = current_app.extensions["sigae_database"]
    with database.connection() as connection:
        user = connection.execute(
            "SELECT * FROM users WHERE username = ? AND active = 1",
            (str(data.get("username", "")),),
        ).fetchone()
    if user is None or not check_password_hash(
        user["password_hash"], str(data.get("password", ""))
    ):
        return jsonify(
            {"error": {"code": "invalid_credentials", "message": "Credenciais inválidas."}}
        ), 401
    with _login_lock:
        _login_attempts.pop(remote, None)
    session.clear()
    session.permanent = True
    session.update(
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
        csrf_token=secrets.token_urlsafe(24),
    )
    return jsonify(
        {
            "user": {"username": user["username"], "role": user["role"]},
            "csrf_token": session["csrf_token"],
        }
    )


@auth_bp.post("/logout")
@require_roles()
def logout():
    session.clear()
    return "", 204


@auth_bp.get("/me")
def me():
    if not session.get("user_id"):
        return jsonify(
            {
                "authenticated": False,
                "auth_required": current_app.config["AUTH_REQUIRED"],
            }
        )
    return jsonify(
        {
            "authenticated": True,
            "auth_required": current_app.config["AUTH_REQUIRED"],
            "user": {"username": session["username"], "role": session["role"]},
            "csrf_token": session["csrf_token"],
        }
    )


@auth_bp.get("/users")
@require_roles("administrador")
def list_users():
    database: Database = current_app.extensions["sigae_database"]
    with database.connection() as connection:
        rows = connection.execute(
            "SELECT id, username, role, active FROM users ORDER BY username"
        ).fetchall()
    return jsonify(
        {
            "data": [
                {
                    "id": row["id"],
                    "username": row["username"],
                    "role": row["role"],
                    "active": bool(row["active"]),
                }
                for row in rows
            ]
        }
    )


@auth_bp.post("/users")
@require_roles("administrador")
def create_user():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", ""))
    role = str(data.get("role", "")).strip().lower()
    allowed_roles = {"recepcao", "enfermagem", "medico", "administrador"}
    if len(username) < 3 or len(password) < 8 or role not in allowed_roles:
        return jsonify(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Informe usuário, senha de 8 caracteres e um papel válido.",
                }
            }
        ), 400
    database: Database = current_app.extensions["sigae_database"]
    try:
        with database.connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users(username, password_hash, role) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), role),
            )
            database.audit(
                connection,
                "user.created",
                "user",
                str(cursor.lastrowid),
                {"username": username, "role": role},
            )
    except sqlite3.IntegrityError as exc:
        if "UNIQUE" in str(exc).upper():
            return jsonify(
                {"error": {"code": "conflict", "message": "Esse usuário já existe."}}
            ), 409
        raise
    return jsonify(
        {
            "data": {
                "id": cursor.lastrowid,
                "username": username,
                "role": role,
                "active": True,
            }
        }
    ), 201


@auth_bp.patch("/users/<int:user_id>/active")
@require_roles("administrador")
def update_user_active(user_id: int):
    data = request.get_json(silent=True) or {}
    active = bool(data.get("active"))
    if session.get("user_id") == user_id and not active:
        return jsonify(
            {
                "error": {
                    "code": "conflict",
                    "message": "Você não pode desativar a própria sessão.",
                }
            }
        ), 409
    database: Database = current_app.extensions["sigae_database"]
    with database.connection() as connection:
        cursor = connection.execute(
            "UPDATE users SET active = ? WHERE id = ?", (1 if active else 0, user_id)
        )
        if cursor.rowcount == 0:
            return jsonify(
                {"error": {"code": "not_found", "message": "Usuário não encontrado."}}
            ), 404
        database.audit(
            connection,
            "user.status_changed",
            "user",
            str(user_id),
            {"active": active},
        )
    return jsonify({"data": {"id": user_id, "active": active}})
