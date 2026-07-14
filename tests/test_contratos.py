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


def test_validar_rechaza_texto_de_seccion_muy_largo():
    """Si Gemini se va de largo en una sección, la placa desborda (.plate
    tiene overflow:hidden). validar() tiene que topear el largo en vez de
    validar OK una respuesta que después se corta silenciosamente."""
    idea = {"titulo": "Excel", "deck": "x", "secciones": [
        {"label": "cuándo conviene", "texto": "x" * (contratos.MAX_CHARS_SECCION_TEXTO + 1)},
        {"label": "dónde duele", "texto": "corto"},
    ]}
    with pytest.raises(ValueError, match="texto"):
        validar("comparativa", _red(ideas=[idea]))


def test_validar_rechaza_titulo_de_idea_muy_largo():
    idea = {"titulo": "x" * (contratos.MAX_CHARS_TITULO_IDEA + 1), "deck": "x",
            "secciones": _IDEA_OK["secciones"]}
    with pytest.raises(ValueError, match="titulo"):
        validar("comparativa", _red(ideas=[idea]))


def test_validar_rechaza_deck_muy_largo():
    idea = {"titulo": "Excel", "deck": "x" * (contratos.MAX_CHARS_DECK + 1),
            "secciones": _IDEA_OK["secciones"]}
    with pytest.raises(ValueError, match="deck"):
        validar("comparativa", _red(ideas=[idea]))


def test_validar_rechaza_secciones_como_lista_de_strings():
    """Si Gemini devuelve 'secciones' como lista de strings en vez de objetos
    {label, texto}, validar() tiene que levantar ValueError (no AttributeError:
    ese no lo atrapa el except de redactar_pieza y voltea todo el lote)."""
    idea = {"titulo": "t", "deck": "d", "secciones": ["qué cambió: algo"]}
    with pytest.raises(ValueError):
        validar("novedad", {**BASE, "ideas": [idea]})


def test_validar_rechaza_texto_de_seccion_que_no_es_string():
    """Si una sección trae 'texto' como lista (o cualquier no-string), tiene
    que ser ValueError, no el AttributeError de .strip() sobre una lista."""
    idea = {"titulo": "t", "deck": "d", "secciones": [
        {"label": "qué cambió", "texto": ["a"]},
        {"label": "por qué importa", "texto": "y"},
    ]}
    with pytest.raises(ValueError):
        validar("novedad", {**BASE, "ideas": [idea]})
