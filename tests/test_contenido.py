from src import contenido


def test_labels_fijos_por_tipo():
    assert contenido.SECCIONES_POR_TIPO["comparativa"] == ["cuándo conviene", "dónde duele"]
    assert contenido.SECCIONES_POR_TIPO["rol"] == ["por qué te la piden", "cómo la practicás"]
    assert contenido.SECCIONES_POR_TIPO["tip"] == ["el problema", "el código", "por qué funciona"]
    assert contenido.SECCIONES_POR_TIPO["novedad"] == ["qué cambió", "por qué importa"]


def test_normalizar_envuelve_idea_vieja_en_una_seccion():
    red = {"ideas": [{"titulo": "Copilot", "texto": "Genera DAX en lenguaje natural."}]}

    ideas = contenido.normalizar_ideas("novedad", red)

    assert ideas == [{
        "titulo": "Copilot",
        "deck": "",
        "secciones": [{"label": "qué cambió", "texto": "Genera DAX en lenguaje natural."}],
    }]


def test_normalizar_deja_pasar_idea_ya_densa():
    idea = {"titulo": "Excel", "deck": "Limpiar 10.000 filas",
            "secciones": [{"label": "cuándo conviene", "texto": "Algo puntual."}]}

    ideas = contenido.normalizar_ideas("comparativa", {"ideas": [idea]})

    assert ideas == [idea]


def test_normalizar_tip_agrega_seccion_de_codigo():
    red = {"ideas": [{"titulo": "Top N", "texto": "ROW_NUMBER con PARTITION BY."}],
           "codigo": "SELECT 1;", "lenguaje": "sql"}

    secciones = contenido.normalizar_ideas("tip", red)[0]["secciones"]

    assert secciones[1] == {"label": "el código", "codigo": "SELECT 1;", "lenguaje": "sql"}
