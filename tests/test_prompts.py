from src.redaccion import prompts


def test_voz_es_voseo():
    assert "voseo" in prompts.VOZ_DE_MARCA.lower() or "sos la voz" in prompts.VOZ_DE_MARCA.lower()


def test_prompt_tip_incluye_codigo_y_pide_json():
    item = {"titulo": "X", "lenguaje": "sql", "gancho": "g",
            "codigo": "SELECT 1;", "explicacion": "e"}
    p = prompts.prompt_tip(item)
    assert "SELECT 1;" in p
    assert '"codigo"' in p


def test_prompt_comparativa_lista_opciones():
    item = {"tarea": "t", "opciones": [
        {"nombre": "A", "cuando_conviene": "pasa X.", "donde_duele": "pasa Y."},
        {"nombre": "B", "cuando_conviene": "pasa Z.", "donde_duele": "pasa W."},
    ], "veredicto": "v"}
    p = prompts.prompt_comparativa(item)
    assert "A" in p and "pasa Y." in p
    assert "B" in p and "pasa W." in p
    assert "{'nombre'" not in p


def test_prompts_piden_secciones_con_los_labels_fijos():
    from src.contenido import SECCIONES_POR_TIPO
    from src.redaccion import prompts

    p = prompts.prompt_comparativa({
        "tarea": "Limpiar filas", "veredicto": "Depende.",
        "opciones": [{"nombre": "Excel", "cuando_conviene": "Una vez.", "donde_duele": "Manual."}]})

    assert "secciones" in p
    for label in SECCIONES_POR_TIPO["comparativa"]:
        assert label in p


def test_prompt_rol_incluye_material_rico_de_skills():
    item = {"rol": "Data Analyst", "gancho": "g",
            "herramientas": ["SQL", "Power BI"],
            "skills": [
                {"nombre": "SQL", "por_que": "sin SQL dependés de otro.",
                 "como_practicar": "resolvé preguntas con JOIN y GROUP BY."},
                {"nombre": "Power BI", "por_que": "el dashboard es el formato final.",
                 "como_practicar": "armá un tablero con filtros propios."},
            ]}
    p = prompts.prompt_rol(item)
    assert "sin SQL dependés de otro." in p
    assert "resolvé preguntas con JOIN y GROUP BY." in p
    assert "el dashboard es el formato final." in p
    assert "{'nombre'" not in p


def test_prompt_tip_pide_por_que_funciona_mas_largo():
    """"por qué funciona" ocupa su placa sola (ver contenido.grupos_de_placa),
    así que el prompt tiene que pedir un texto que llene ese lugar en vez de
    las 1-2 oraciones genéricas de REGLAS_IDEAS."""
    item = {"titulo": "X", "lenguaje": "sql", "gancho": "g",
            "codigo": "SELECT 1;", "explicacion": "e"}

    p = prompts.prompt_tip(item)

    assert "3-4 oraciones" in p
    assert "350-500" in p


def test_prompt_tip_sigue_pidiendo_el_problema_corto():
    item = {"titulo": "X", "lenguaje": "sql", "gancho": "g",
            "codigo": "SELECT 1;", "explicacion": "e"}

    p = prompts.prompt_tip(item)

    assert "1-2 oraciones" in p
