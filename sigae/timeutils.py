"""Utilitários de tempo real usados pelo domínio e pela API."""

from __future__ import annotations

import time
from datetime import UTC, datetime


def now_epoch() -> int:
    return int(time.time())


def iso_from_epoch(value: int | None) -> str | None:
    if value is None or value <= 0:
        return None
    return datetime.fromtimestamp(value, UTC).isoformat().replace("+00:00", "Z")


def minutes_since(value: int | None, end: int | None = None) -> int | None:
    if value is None or value <= 0:
        return None
    return max(0, ((end or now_epoch()) - value) // 60)
