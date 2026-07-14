from src import contenido


def test_labels_fijos_por_tipo():
    assert contenido.SECCIONES_POR_TIPO["comparativa"] == ["cuándo conviene", "dónde duele"]
    assert contenido.SECCIONES_POR_TIPO["rol"] == ["por qué te la piden", "cómo la practicás"]
    assert contenido.SECCIONES_POR_TIPO["tip"] == ["el problema", "el código", "por qué funciona"]
    assert contenido.SECCIONES_POR_TIPO["novedad"] == ["qué cambió", "por qué importa"]


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
    assert idea["deck"] == ""
    assert [s["label"] for s in idea["secciones"]] == ["el problema", "el código", "por qué funciona"]
    assert idea["secciones"][1] == {"label": "el código", "codigo": "SELECT 1;", "lenguaje": "sql"}


def test_ideas_desde_item_novedad_usa_el_resumen():
    item = {"titulo": "Power BI suma Copilot", "resumen": "Genera DAX en lenguaje natural.",
            "fuente": "Power BI Blog", "link": "http://x/1", "id": "http://x/1"}

    idea = contenido.ideas_desde_item("novedad", item)[0]

    assert idea["secciones"][0] == {"label": "qué cambió", "texto": "Genera DAX en lenguaje natural."}
    assert idea["secciones"][1] == {"label": "por qué importa", "texto": "Una novedad para tener en el radar si trabajás con esta herramienta."}
