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
