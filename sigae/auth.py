"""Autenticação opcional por sessão e papéis de acesso."""

from __future__ import annotations

import secrets
from functools import wraps
from typing import Any

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .database import Database

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


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


def require_roles(*roles: str):
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
    session.clear()
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
