"""Validação explícita dos contratos da API."""

from __future__ import annotations

import re
from typing import Any


class ValidationError(ValueError):
    def __init__(self, message: str, fields: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.fields = fields or {}


def require_json_object(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValidationError("O corpo da requisição deve ser um objeto JSON.")
    return data


def text_field(data: dict[str, Any], field: str, label: str, max_length: int = 120) -> str:
    raw = data.get(field, "")
    value = "" if raw is None else str(raw).strip()
    if not value:
        raise ValidationError("Revise os campos informados.", {field: f"{label} é obrigatório."})
    if len(value) > max_length:
        raise ValidationError(
            "Revise os campos informados.",
            {field: f"{label} deve ter até {max_length} caracteres."},
        )
    return value


def priority_field(data: dict[str, Any]) -> int:
    try:
        priority = int(data.get("prioridade", data.get("priority")))
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "Revise os campos informados.",
            {"prioridade": "Prioridade deve ser um número de 1 a 5."},
        ) from exc
    if priority not in range(1, 6):
        raise ValidationError(
            "Revise os campos informados.", {"prioridade": "Prioridade deve estar entre 1 e 5."}
        )
    return priority


def optional_id(data: dict[str, Any], prefixes: tuple[str, ...]) -> str | None:
    raw = data.get("id")
    if raw is None or str(raw).strip() == "":
        return None
    value = str(raw).strip().upper()
    if len(value) > 24 or not re.fullmatch(r"[A-Z0-9-]+", value):
        raise ValidationError(
            "Revise os campos informados.", {"id": "ID deve conter apenas letras, números e hífen."}
        )
    if not value.startswith(prefixes):
        raise ValidationError(
            "Revise os campos informados.", {"id": f"ID deve iniciar com {' ou '.join(prefixes)}."}
        )
    return value
