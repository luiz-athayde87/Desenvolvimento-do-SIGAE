from __future__ import annotations

import pytest

from sigae.validation import (
    ValidationError,
    optional_id,
    priority_field,
    require_json_object,
    text_field,
)


def test_json_and_text_contracts() -> None:
    assert require_json_object({"nome": "  Maria  "}) == {"nome": "  Maria  "}
    assert text_field({"nome": "  Maria  "}, "nome", "Nome") == "Maria"

    with pytest.raises(ValidationError):
        require_json_object([])
    with pytest.raises(ValidationError):
        text_field({"nome": ""}, "nome", "Nome")
    with pytest.raises(ValidationError):
        text_field({"nome": "nome extenso"}, "nome", "Nome", max_length=4)


def test_priority_and_optional_identifier_contracts() -> None:
    assert priority_field({"priority": "3"}) == 3
    assert optional_id({}, ("P",)) is None
    assert optional_id({"id": " pac-10 "}, ("P", "PAC-")) == "PAC-10"

    for value in (None, "texto", 0, 6):
        with pytest.raises(ValidationError):
            priority_field({"prioridade": value})

    with pytest.raises(ValidationError):
        optional_id({"id": "M10"}, ("P",))
    with pytest.raises(ValidationError):
        optional_id({"id": "P@10"}, ("P",))
