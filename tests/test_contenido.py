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


def test_inyectar_codigo_tip_inserta_en_la_posicion_del_contrato():
    """La sección "el código" la arma el sistema (Gemini no la escribe), y su
    posición tiene que salir de SECCIONES_POR_TIPO, no de un índice hardcodeado."""
    datos = {"ideas": [{"titulo": "t", "deck": "d", "secciones": [
        {"label": "el problema", "texto": "Sacar el top 3 por categoría."},
        {"label": "por qué funciona", "texto": "ROW_NUMBER numera por grupo."},
    ]}], "codigo": "SELECT 1;", "lenguaje": "sql"}

    contenido.inyectar_codigo_tip(datos)

    secciones = datos["ideas"][0]["secciones"]
    assert [s["label"] for s in secciones] == contenido.SECCIONES_POR_TIPO["tip"]
    pos = contenido.SECCIONES_POR_TIPO["tip"].index("el código")
    assert secciones[pos] == {"label": "el código", "codigo": "SELECT 1;", "lenguaje": "sql"}


def test_ideas_desde_item_labels_coinciden_con_secciones_por_tipo():
    """El plan B (ideas_desde_item) no pasa por contratos.validar, así que si
    hardcodea los labels como strings literales en vez de derivarlos de
    SECCIONES_POR_TIPO, renombrar un label en la constante desincroniza las
    placas del plan B en silencio. Esto cruza las dos fuentes para cada tipo."""
    items = {
        "novedad": {"titulo": "T", "resumen": "R", "fuente": "F", "id": "x"},
        "comparativa": {"tarea": "T", "veredicto": "V", "opciones": [
            {"nombre": "Excel", "cuando_conviene": "c", "donde_duele": "d"}]},
        "rol": {"rol": "R", "gancho": "g", "herramientas": ["SQL"],
                "skills": [{"nombre": "SQL", "por_que": "x", "como_practicar": "y"}]},
        "tip": {"titulo": "T", "gancho": "g", "codigo": "SELECT 1;", "lenguaje": "sql",
                "explicacion": "e"},
    }
    for tipo, item in items.items():
        ideas = contenido.ideas_desde_item(tipo, item)
        for idea in ideas:
            labels = [s["label"] for s in idea["secciones"]]
            assert labels == contenido.SECCIONES_POR_TIPO[tipo], tipo


def test_ideas_desde_item_novedad_usa_el_resumen():
    item = {"titulo": "Power BI suma Copilot", "resumen": "Genera DAX en lenguaje natural.",
            "fuente": "Power BI Blog", "link": "http://x/1", "id": "http://x/1"}

    idea = contenido.ideas_desde_item("novedad", item)[0]

    assert idea["secciones"][0] == {"label": "qué cambió", "texto": "Genera DAX en lenguaje natural."}
    assert idea["secciones"][1] == {"label": "por qué importa", "texto": "Una novedad para tener en el radar si trabajás con esta herramienta."}


def test_ideas_desde_item_novedad_limpia_el_html_del_resumen():
    """feedparser deja el HTML crudo del feed en entry.summary (ver
    fuentes/feeds.py). Con autoescape, esos tags se ven literalmente en la
    placa ("<p>Today we are announcing...</p>"): hay que limpiarlos."""
    item = {"titulo": "T", "resumen": "<p>Today we are <b>announcing</b> Copilot in DAX.</p>",
            "fuente": "F", "link": "http://x/1", "id": "http://x/1"}

    idea = contenido.ideas_desde_item("novedad", item)[0]

    texto = idea["secciones"][0]["texto"]
    assert "<" not in texto and ">" not in texto
    assert "Today we are announcing Copilot in DAX." in texto


def test_ideas_desde_item_novedad_trunca_resumen_largo_en_limite_de_palabra():
    """Los feeds mandan resúmenes largos (~1.100 caracteres es común): sin
    truncar, el panel se pasa del alto de la placa (.plate tiene
    overflow:hidden) y se come el footer. Truncar en medio de una palabra
    también se ve mal, así que el corte tiene que respetar el límite de
    palabra y cerrar con elipsis."""
    resumen_largo = "palabra " * 200  # ~1600 caracteres, bien por encima del máximo
    item = {"titulo": "T", "resumen": resumen_largo, "fuente": "F",
            "link": "http://x/1", "id": "http://x/1"}

    idea = contenido.ideas_desde_item("novedad", item)[0]

    texto = idea["secciones"][0]["texto"]
    assert len(texto) <= contenido.MAX_CHARS_SECCION_TEXTO
    assert texto.endswith("…")
    # el corte no puede caer a mitad de palabra: sin el "…" final, lo que
    # queda tiene que ser una secuencia de palabras completas de "palabra "
    cuerpo = texto[:-1].strip()
    assert cuerpo != "" and all(p == "palabra" for p in cuerpo.split())


def test_grupos_de_placa_tip_se_parte_en_dos():
    """El tip es el único tipo con una sola idea: sin partirlo, sus tres
    secciones caen todas en la misma placa y la placa queda saturada."""
    assert contenido.grupos_de_placa("tip") == [
        ["el problema", "el código"],
        ["por qué funciona"],
    ]


def test_grupos_de_placa_los_demas_tipos_van_en_una_sola_placa():
    """El default es lo que mantiene intactos a los otros tres tipos: un grupo
    con todos sus labels, es decir una placa por idea, como siempre."""
    for tipo in ("novedad", "comparativa", "rol"):
        assert contenido.grupos_de_placa(tipo) == [contenido.SECCIONES_POR_TIPO[tipo]]


def test_grupos_de_placa_no_pierde_ni_duplica_ni_reordena_secciones():
    """Invariante del reparto: aplanar los grupos tiene que devolver
    exactamente los labels del tipo, en el mismo orden. Sin esto, un typo en
    PLACAS_POR_TIPO hace desaparecer una sección de la placa en silencio,
    porque construir_placas descarta los labels que no reconoce."""
    for tipo in contenido.SECCIONES_POR_TIPO:
        aplanado = [label for grupo in contenido.grupos_de_placa(tipo) for label in grupo]
        assert aplanado == contenido.SECCIONES_POR_TIPO[tipo], tipo


def test_max_chars_seccion_da_mas_lugar_a_la_que_va_sola():
    """"por qué funciona" ocupa su placa sola, así que tiene el alto entero
    para ella; "el problema" comparte placa con el snippet de código."""
    assert contenido.max_chars_seccion("tip", "por qué funciona") == contenido.MAX_CHARS_SECCION_SOLA
    assert contenido.max_chars_seccion("tip", "el problema") == contenido.MAX_CHARS_SECCION_TEXTO
    assert contenido.max_chars_seccion("tip", "el código") == contenido.MAX_CHARS_SECCION_TEXTO


def test_max_chars_seccion_de_los_tipos_de_dos_secciones():
    for tipo in ("novedad", "comparativa", "rol"):
        for label in contenido.SECCIONES_POR_TIPO[tipo]:
            assert contenido.max_chars_seccion(tipo, label) == contenido.MAX_CHARS_SECCION_TEXTO


def test_max_chars_seccion_label_desconocido_usa_el_tope_chico():
    """Un label que no está en ningún grupo cae al tope conservador en vez de
    romper: validar() ya rechaza los labels inventados por su cuenta."""
    assert contenido.max_chars_seccion("tip", "inventado") == contenido.MAX_CHARS_SECCION_TEXTO
