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
