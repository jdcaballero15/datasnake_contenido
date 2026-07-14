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


def test_ideas_desde_item_comparativa_una_idea_por_opcion():
    item = {"tarea": "Limpiar 10.000 filas", "veredicto": "Depende.", "opciones": [
        {"nombre": "Excel", "cuando_conviene": "Una sola vez.", "donde_duele": "No queda documentado."},
        {"nombre": "pandas", "cuando_conviene": "Se repite.", "donde_duele": "Necesitás entorno."}]}

    ideas = contenido.ideas_desde_item("comparativa", item)

    assert [i["titulo"] for i in ideas] == ["Excel", "pandas"]
    assert ideas[0]["deck"] == "Limpiar 10.000 filas"
    assert ideas[0]["secciones"] == [
        {"label": "cuándo conviene", "texto": "Una sola vez."},
        {"label": "dónde duele", "texto": "No queda documentado."},
    ]


def test_ideas_desde_item_rol_una_idea_por_skill():
    item = {"rol": "Data Analyst", "gancho": "El puente al negocio.", "herramientas": ["SQL"],
            "skills": [{"nombre": "SQL", "por_que": "Es el idioma.", "como_practicar": "Base pública."}]}

    ideas = contenido.ideas_desde_item("rol", item)

    assert ideas[0]["titulo"] == "SQL"
    assert ideas[0]["deck"] == "El puente al negocio."
    assert [s["label"] for s in ideas[0]["secciones"]] == ["por qué te la piden", "cómo la practicás"]


def test_ideas_desde_item_tip_tiene_las_tres_secciones_con_codigo():
    item = {"titulo": "Top N en SQL", "gancho": "Top N por grupo en una pasada.",
            "codigo": "SELECT 1;", "lenguaje": "sql", "explicacion": "ROW_NUMBER numera por grupo."}

    idea = contenido.ideas_desde_item("tip", item)[0]

    assert idea["titulo"] == "Top N en SQL"
    assert [s["label"] for s in idea["secciones"]] == ["el problema", "el código", "por qué funciona"]
    assert idea["secciones"][1] == {"label": "el código", "codigo": "SELECT 1;", "lenguaje": "sql"}


def test_ideas_desde_item_novedad_usa_el_resumen():
    item = {"titulo": "Power BI suma Copilot", "resumen": "Genera DAX en lenguaje natural.",
            "fuente": "Power BI Blog", "link": "http://x/1", "id": "http://x/1"}

    idea = contenido.ideas_desde_item("novedad", item)[0]

    assert idea["secciones"][0] == {"label": "qué cambió", "texto": "Genera DAX en lenguaje natural."}
