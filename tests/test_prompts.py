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
    las 1-2 oraciones genéricas de REGLAS_IDEAS. Los números salen de
    prompts.TIP_PORQUE_FUNCIONA_MIN/MAX (derivados de MAX_CHARS_SECCION_SOLA)
    en vez de hardcodearse, para que no puedan desincronizarse del tope real."""
    item = {"titulo": "X", "lenguaje": "sql", "gancho": "g",
            "codigo": "SELECT 1;", "explicacion": "e"}

    p = prompts.prompt_tip(item)

    assert "3-4 oraciones" in p
    assert f"{prompts.TIP_PORQUE_FUNCIONA_MIN}-{prompts.TIP_PORQUE_FUNCIONA_MAX}" in p


def test_prompt_tip_presupuesto_de_por_que_funciona_supera_el_tope_general():
    """REGLAS_IDEAS (código de revisión 2026-08-11) ahora deja explícito que
    el esqueleto JSON puede pisar el tope general de 260 caracteres para una
    sección puntual; este test fija que el presupuesto real que le comunicamos
    al modelo para "por qué funciona" siga siendo mayor a ese tope general, no
    que Gemini pueda leer la regla universal como el número que manda."""
    from src.contenido import MAX_CHARS_SECCION_TEXTO

    assert prompts.TIP_PORQUE_FUNCIONA_MIN > MAX_CHARS_SECCION_TEXTO
    assert prompts.TIP_PORQUE_FUNCIONA_MAX > MAX_CHARS_SECCION_TEXTO


def test_reglas_ideas_deja_que_el_esqueleto_pise_el_tope_general():
    """Antes de este fix, REGLAS_IDEAS se interpolaba también en prompt_tip
    (:159) con un tope universal y "consecuencia física" que contradecía el
    pedido de 350-500 caracteres para "por qué funciona" 20 líneas más abajo.
    La regla general ahora debe dejar explícito que un tope puntual en el
    esqueleto JSON gana."""
    assert "salvo que el esqueleto" in prompts.REGLAS_IDEAS


def test_prompt_novedad_pide_traducir_del_ingles():
    """Antes de este fix, prompt_novedad nunca le decía a Gemini que el
    material (Título/Resumen del RSS) viene en inglés: un modelo que reflejara
    el idioma de la fuente pasaba todos los checks de contratos.validar (que
    no chequea idioma) y publicaba en inglés, incluido "titulo_portada"
    (corrida 2026-08-11)."""
    item = {"fuente": "Power BI", "titulo": "Announcing new Copilot features",
            "resumen": "Today we are announcing a set of improvements."}

    p = prompts.prompt_novedad(item)

    assert "viene en inglés" in p
    assert "traducilo" in p
    assert 'ni siquiera en "titulo_portada"' in p


def test_prompt_tip_sigue_pidiendo_el_problema_corto():
    item = {"titulo": "X", "lenguaje": "sql", "gancho": "g",
            "codigo": "SELECT 1;", "explicacion": "e"}

    p = prompts.prompt_tip(item)

    assert "1-2 oraciones" in p


def test_los_prompts_declaran_el_tope_de_caracteres_de_seccion():
    """El validador rechaza secciones de más de MAX_CHARS_SECCION_TEXTO, pero
    el prompt solo pedía "1-2 oraciones": Gemini escribía 295-331 chars de
    buena fe y la pieza caía a plan B (corrida 2026-08-11). El número sale de
    contenido.py para que no pueda desincronizarse del validador."""
    from src.contenido import MAX_CHARS_SECCION_TEXTO

    tope = str(MAX_CHARS_SECCION_TEXTO)
    generados = [
        prompts.prompt_novedad({"fuente": "f", "titulo": "t", "resumen": "r"}),
        prompts.prompt_comparativa({"tarea": "t", "veredicto": "v", "opciones": [
            {"nombre": "A", "cuando_conviene": "x.", "donde_duele": "y."}]}),
        prompts.prompt_rol({"rol": "r", "gancho": "g", "herramientas": ["SQL"],
                            "skills": [{"nombre": "s", "por_que": "p", "como_practicar": "c"}]}),
        prompts.prompt_tip({"titulo": "x", "lenguaje": "sql", "gancho": "g",
                            "codigo": "SELECT 1;", "explicacion": "e"}),
    ]

    for p in generados:
        assert tope in p
