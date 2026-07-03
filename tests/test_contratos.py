import pytest

from src.redaccion import contratos

BASE = {"titulo_portada": "HOLA", "ideas": [{"titulo": "t", "texto": "x"}],
        "caption": "c" * 500, "hashtags": ["data"]}


def test_valida_novedad_ok():
    contratos.validar("novedad", dict(BASE))


def test_rechaza_caption_corto():
    with pytest.raises(ValueError):
        contratos.validar("novedad", {**BASE, "caption": "corto"})


def test_tip_requiere_codigo():
    with pytest.raises(ValueError):
        contratos.validar("tip", dict(BASE))  # sin 'codigo'
    contratos.validar("tip", {**BASE, "codigo": "SELECT 1;"})
