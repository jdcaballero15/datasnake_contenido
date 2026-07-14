import pytest

from src.redaccion import contratos
from src.redaccion.contratos import validar

_IDEA_NOVEDAD = {"titulo": "t", "deck": "d",
                  "secciones": [{"label": "qué cambió", "texto": "x"},
                                {"label": "por qué importa", "texto": "y"}]}

BASE = {"titulo_portada": "HOLA", "ideas": [_IDEA_NOVEDAD],
        "caption": "c" * 500, "hashtags": ["data"]}

# Gemini solo escribe "el problema" y "por qué funciona"; "el código" lo arma
# el sistema aparte (ver contenido.inyectar_codigo_tip), a partir de los
# campos "codigo"/"lenguaje" de la respuesta.
_IDEA_TIP = {"titulo": "t", "deck": "d",
             "secciones": [{"label": "el problema", "texto": "x"},
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


def test_tip_rechaza_mas_de_una_idea():
    with pytest.raises(ValueError, match="1 idea"):
        contratos.validar("tip", {**BASE, "ideas": [_IDEA_TIP, _IDEA_TIP],
                                   "codigo": "SELECT 1;"})


def test_tip_rechaza_si_gemini_manda_la_seccion_el_codigo():
    """Gemini no debe escribir "el código" como sección: eso lo arma el sistema
    después (inyectar_codigo_tip). Si igual la manda, quedaría duplicada."""
    idea_con_codigo_de_mas = {"titulo": "t", "deck": "d", "secciones": [
        {"label": "el problema", "texto": "x"},
        {"label": "el código", "texto": "y"},
        {"label": "por qué funciona", "texto": "z"},
    ]}
    with pytest.raises(ValueError, match="secciones"):
        contratos.validar("tip", {**BASE, "ideas": [idea_con_codigo_de_mas],
                                   "codigo": "SELECT 1;"})


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


def test_validar_rechaza_secciones_incompletas():
    idea = {"titulo": "Excel", "deck": "x",
            "secciones": [{"label": "cuándo conviene", "texto": "Una sola vez."}]}
    with pytest.raises(ValueError, match="secciones"):
        validar("comparativa", _red(ideas=[idea]))


def test_validar_rechaza_secciones_fuera_de_orden():
    idea = {"titulo": "Excel", "deck": "x",
            "secciones": [{"label": "dónde duele", "texto": "No queda documentado."},
                          {"label": "cuándo conviene", "texto": "Una sola vez."}]}
    with pytest.raises(ValueError, match="secciones"):
        validar("comparativa", _red(ideas=[idea]))


_IDEA_ROL = {"titulo": "SQL", "deck": "d",
             "secciones": [{"label": "por qué te la piden", "texto": "Es el idioma."},
                           {"label": "cómo la practicás", "texto": "Base pública."}]}


def test_validar_acepta_rol():
    validar("rol", _red(ideas=[_IDEA_ROL]))  # no levanta
