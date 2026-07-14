import pytest

from src.redaccion import contratos
from src.redaccion.contratos import validar

_IDEA_NOVEDAD = {"titulo": "t", "deck": "d",
                  "secciones": [{"label": "qué cambió", "texto": "x"},
                                {"label": "por qué importa", "texto": "y"}]}

BASE = {"titulo_portada": "HOLA", "ideas": [_IDEA_NOVEDAD],
        "caption": "c" * 500, "hashtags": ["data"]}

_IDEA_TIP = {"titulo": "t", "deck": "d",
             "secciones": [{"label": "el problema", "texto": "x"},
                            {"label": "el código", "texto": "y"},
                            {"label": "por qué funciona", "texto": "z"}]}


def test_valida_novedad_ok():
    contratos.validar("novedad", dict(BASE))


def test_rechaza_caption_corto():
    with pytest.raises(ValueError):
        contratos.validar("novedad", {**BASE, "caption": "corto"})


def test_tip_requiere_codigo():
    with pytest.raises(ValueError):
        contratos.validar("tip", {**BASE, "ideas": [_IDEA_TIP]})  # sin 'codigo'
    contratos.validar("tip", {**BASE, "ideas": [_IDEA_TIP], "codigo": "SELECT 1;"})


_IDEA_OK = {"titulo": "Excel", "deck": "Limpiar filas",
            "secciones": [{"label": "cuándo conviene", "texto": "Una sola vez."},
                          {"label": "dónde duele", "texto": "No queda documentado."}]}


def _red(**extra):
    base = {"titulo_portada": "EXCEL VS PYTHON", "ideas": [_IDEA_OK],
            "caption": "c" * 500, "hashtags": ["data", "sql"]}
    base.update(extra)
    return base


def test_validar_acepta_ideas_densas():
    validar("comparativa", _red())  # no levanta


def test_validar_rechaza_idea_sin_secciones():
    with pytest.raises(ValueError, match="secciones"):
        validar("comparativa", _red(ideas=[{"titulo": "Excel", "deck": "x"}]))


def test_validar_rechaza_label_inventado():
    idea = {"titulo": "Excel", "deck": "x",
            "secciones": [{"label": "lo que se me cantó", "texto": "Una sola vez."}]}
    with pytest.raises(ValueError, match="label"):
        validar("comparativa", _red(ideas=[idea]))
