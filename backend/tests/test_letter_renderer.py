# backend/tests/test_letter_renderer.py
from utils.letter_template import (
    LetterTemplate, PLACEHOLDERS, substitute, DEFAULT_TEMPLATE,
)


def test_substitute_replaces_known_tokens():
    out = substitute("FIR {fir_number} for {isp_name}",
                     {"fir_number": "201/25", "isp_name": "Airtel"})
    assert out == "FIR 201/25 for Airtel"


def test_substitute_missing_value_becomes_empty():
    assert substitute("Hello {officer_name}!", {}) == "Hello !"


def test_placeholders_list_has_expected_tokens():
    assert "fir_number" in PLACEHOLDERS
    assert "isp_name" in PLACEHOLDERS
    assert len(PLACEHOLDERS) == 13


def test_default_template_validates_and_has_single_ip_table():
    tpl = LetterTemplate.model_validate(DEFAULT_TEMPLATE)
    ip_tables = [b for b in tpl.blocks if b.type == "ip_table"]
    assert len(ip_tables) == 1
    assert tpl.name == "IFSO Dwarka Default"


def test_template_rejects_two_ip_tables():
    import pytest
    from pydantic import ValidationError
    bad = {
        "name": "x", "scope": "user",
        "page": DEFAULT_TEMPLATE["page"],
        "blocks": [
            {"id": "a", "type": "ip_table"},
            {"id": "b", "type": "ip_table"},
        ],
    }
    with pytest.raises(ValidationError):
        LetterTemplate.model_validate(bad)
