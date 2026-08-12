from datetime import date, timedelta

from src import main
from src.config import get_config


def test_plan_dia_sin_novedad_un_evergreen(monkeypatch, tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    piezas = main.plan_dia(cfg, seed=202627, novedad=None)
    assert len(piezas) == 1
    assert piezas[0]["tipo"] in cfg.tipos_evergreen


def test_plan_dia_con_novedad_una_pieza_novedad(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    nov = {"id": "http://x/1", "titulo": "T", "resumen": "R", "link": "http://x/1", "fuente": "PBI"}
    piezas = main.plan_dia(cfg, seed=202627, novedad=nov)
    assert len(piezas) == 1
    assert piezas[0]["tipo"] == "novedad"


def test_plan_dia_volumen_mayor_novedad_mas_evergreen(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.piezas_por_dia = 3
    nov = {"id": "http://x/1", "titulo": "T", "resumen": "R", "link": "http://x/1", "fuente": "PBI"}
    piezas = main.plan_dia(cfg, seed=202627, novedad=nov)
    assert len(piezas) == 3
    assert piezas[0]["tipo"] == "novedad"
    assert all(p["tipo"] in cfg.tipos_evergreen for p in piezas[1:])


IDEA = {"titulo": "Excel", "deck": "Limpiar filas",
        "secciones": [{"label": "cuándo conviene", "texto": "Una sola vez."},
                      {"label": "dónde duele", "texto": "No queda documentado."}]}

IDEA_TIP = {"titulo": "DETECTÁ DUPLICADOS", "deck": "Encontrá qué filas se repiten.",
            "secciones": [
                {"label": "el problema", "texto": "Se cuelan registros idénticos."},
                {"label": "el código", "codigo": "SELECT 1;", "lenguaje": "sql"},
                {"label": "por qué funciona", "texto": "GROUP BY junta las filas iguales."},
            ]}


def test_variante_portada_es_estable_y_avanza_en_ciclo():
    inicio = date(2026, 7, 20)

    variantes = [main.variante_portada(inicio + timedelta(days=i)) for i in range(5)]

    assert variantes == [
        "cover-green", "cover-violet", "cover-blue", "cover-coral", "cover-green",
    ]


def test_construir_placas_usa_la_variante_de_portada_indicada():
    placas = main.construir_placas(
        "comparativa", {"titulo_portada": "X", "ideas": [IDEA]}, "cover-coral")

    assert placas[0]["variant"] == "cover-coral"
    assert placas[1]["variant"] == "dark"
    assert placas[-1]["variant"] == "close"
def test_construir_placas_usa_una_placa_contenido_por_idea():
    red = {"titulo_portada": "EXCEL VS\nPYTHON", "ideas": [IDEA, IDEA]}

    placas = main.construir_placas("comparativa", red)

    assert [p["plantilla"] for p in placas] == ["portada", "contenido", "contenido", "cierre"]
    assert [p["slide_index"] for p in placas] == [1, 2, 3, 4]
    assert {p["slide_total"] for p in placas} == {4}
    assert placas[0]["variant"] == "cover-green" and placas[-1]["variant"] == "close"


def test_construir_placas_pasa_secciones_y_kicker():
    red = {"titulo_portada": "X", "ideas": [IDEA]}

    placa = main.construir_placas("comparativa", red)[1]

    assert placa["kicker"] == "opción 01"
    assert placa["deck"] == "Limpiar filas"
    assert placa["secciones"] == IDEA["secciones"]


def test_tercera_idea_sale_en_placa_clara():
    red = {"titulo_portada": "X", "ideas": [IDEA, IDEA, IDEA, IDEA]}

    variants = [p["variant"] for p in main.construir_placas("rol", red)]

    assert variants == ["cover-green", "dark", "dark", "light", "dark", "close"]


def test_plan_b_tip_arma_ideas_densas():
    item = {"titulo": "Top N en SQL", "gancho": "Top N por grupo.", "codigo": "SELECT 1;",
            "lenguaje": "sql", "explicacion": "ROW_NUMBER numera por grupo."}

    red = main.plan_b("tip", item)

    assert red["plan_b"] is True
    assert [s["label"] for s in red["ideas"][0]["secciones"]] == [
        "el problema", "el código", "por qué funciona"]


def test_plan_b_tip_usa_sql_por_defecto_si_falta_lenguaje():
    """contenido.ideas_desde_item ya usa item.get('lenguaje', 'sql'); plan_b
    tiene que seguir el mismo criterio en vez de item['lenguaje'] (KeyError
    si el banco no trae el campo)."""
    item = {"titulo": "Top N en SQL", "gancho": "Top N por grupo.", "codigo": "SELECT 1;",
            "explicacion": "ROW_NUMBER numera por grupo."}  # sin "lenguaje"

    red = main.plan_b("tip", item)

    assert red["lenguaje"] == "sql"


def test_armar_caption_agrega_ctas_y_hashtags():
    cap = main.armar_caption("cuerpo", ["data", "sql"])
    assert "cuerpo" in cap and "#data" in cap
    from src import config
    assert config.CTA_GUARDAR in cap


def test_armar_caption_capa_hashtags_en_5():
    cap = main.armar_caption("cuerpo", ["a", "b", "c", "d", "e", "f", "g"])
    assert cap.count("#") == 5


def test_plan_dia_usa_seeds_deterministas(monkeypatch, tmp_path):
    from src.fuentes import bancos
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.piezas_por_dia = 3
    seeds = []
    real = bancos.seleccionar

    def spy(c, banco, cantidad, seed):
        seeds.append(seed)
        return real(c, banco, cantidad, seed)

    monkeypatch.setattr(main, "seleccionar", spy)
    main.plan_dia(cfg, seed=202627, novedad=None)  # sin novedad → 3 evergreen slots
    assert seeds == [202628, 202629, 202630]  # seed+1, +2, +3 — determinista


def test_plan_b_rol_usa_ideas_densas_por_skill():
    item = {"id": "r01", "rol": "Data Analyst", "gancho": "g",
            "herramientas": ["SQL", "Power BI"],
            "skills": [
                {"nombre": "SQL", "por_que": "x" * 30, "como_practicar": "y" * 30},
                {"nombre": "Power BI", "por_que": "x" * 30, "como_practicar": "y" * 30},
            ]}
    red = main.plan_b("rol", item)
    assert "SQL" in red["caption"] and "Power BI" in red["caption"]
    assert "{'nombre'" not in red["caption"]
    assert [i["titulo"] for i in red["ideas"]] == ["SQL", "Power BI"]
    assert [s["label"] for s in red["ideas"][0]["secciones"]] == [
        "por qué te la piden", "cómo la practicás"]


def test_redactar_pieza_tip_inyecta_el_codigo_entre_las_otras_dos_secciones(monkeypatch, tmp_path):
    """El prompt de tip le pide a Gemini solo 'el problema' y 'por qué funciona'
    (el código viaja en los campos "codigo"/"lenguaje", no como texto de sección).
    redactar_pieza tiene que armar la sección 'el código' con ese material antes
    de devolver la pieza, igual que hace ideas_desde_item para el plan B."""
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.gemini_api_key = "fake"
    respuesta_gemini = {
        "titulo_portada": "TOP N",
        "ideas": [{"titulo": "Top N", "deck": "d", "secciones": [
            {"label": "el problema", "texto": "Sacar el top 3 por categoría."},
            {"label": "por qué funciona", "texto": "ROW_NUMBER numera por grupo."},
        ]}],
        "codigo": "SELECT 1;", "lenguaje": "sql",
        "caption": "c" * 500, "hashtags": ["sql"],
    }
    monkeypatch.setattr(main, "generar_json", lambda prompt, key: respuesta_gemini)

    item = {"titulo": "Top N en SQL", "gancho": "g", "codigo": "SELECT 1;",
            "lenguaje": "sql", "explicacion": "e"}
    red = main.redactar_pieza("tip", item, cfg)

    labels = [s["label"] for s in red["ideas"][0]["secciones"]]
    assert labels == ["el problema", "el código", "por qué funciona"]
    assert red["ideas"][0]["secciones"][1] == {
        "label": "el código", "codigo": "SELECT 1;", "lenguaje": "sql"}


def test_redactar_pieza_cae_a_plan_b_si_secciones_es_lista_de_strings(monkeypatch, tmp_path):
    """Reproduce el CRÍTICO 1 de la revisión: Gemini devuelve 'secciones' como
    lista de strings en vez de objetos {label, texto}. Antes esto tiraba un
    AttributeError que no entraba en el except de redactar_pieza y volteaba
    todo el lote; ahora tiene que caer a plan B como cualquier respuesta
    inválida."""
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.gemini_api_key = "fake"
    respuesta_malformada = {
        "titulo_portada": "X",
        "ideas": [{"titulo": "t", "deck": "d", "secciones": ["qué cambió: algo"]}],
        "caption": "c" * 500, "hashtags": ["data"],
    }
    monkeypatch.setattr(main, "generar_json", lambda prompt, key: respuesta_malformada)

    item = {"titulo": "Power BI suma Copilot", "resumen": "Genera DAX en lenguaje natural.",
            "fuente": "Power BI Blog", "id": "http://x/1"}
    red = main.redactar_pieza("novedad", item, cfg)

    assert red["plan_b"] is True


def test_redactar_pieza_cae_a_plan_b_si_texto_de_seccion_no_es_string(monkeypatch, tmp_path):
    """Mismo CRÍTICO 1, otra variante: 'texto' de una sección viene como lista."""
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.gemini_api_key = "fake"
    respuesta_malformada = {
        "titulo_portada": "X",
        "ideas": [{"titulo": "t", "deck": "d", "secciones": [
            {"label": "qué cambió", "texto": ["a"]},
            {"label": "por qué importa", "texto": "y"},
        ]}],
        "caption": "c" * 500, "hashtags": ["data"],
    }
    monkeypatch.setattr(main, "generar_json", lambda prompt, key: respuesta_malformada)

    item = {"titulo": "Power BI suma Copilot", "resumen": "Genera DAX en lenguaje natural.",
            "fuente": "Power BI Blog", "id": "http://x/1"}
    red = main.redactar_pieza("novedad", item, cfg)

    assert red["plan_b"] is True


def test_plan_b_comparativa_con_opciones_objeto():
    """Test que reproduzca el error: opciones son dicts, no strings."""
    item = {
        "id": "c01",
        "tarea": "Limpiar 10.000 filas con nulos y duplicados",
        "opciones": [
            {"nombre": "Excel",
             "cuando_conviene": "Es una limpieza de una sola vez y querés verla con los ojos: filtros, quitar duplicados y listo.",
             "donde_duele": "Son ~8 pasos manuales que nadie deja documentados: la semana que viene los repetís de memoria y no sabés si te dio distinto."},
            {"nombre": "Python / pandas",
             "cuando_conviene": "La limpieza se repite: dropna y drop_duplicates son 3 líneas que corrés igual todos los meses.",
             "donde_duele": "Necesitás el entorno armado y que alguien más pueda correrlo; para un archivo suelto es matar una mosca a cañonazos."},
        ],
        "veredicto": "Para algo puntual, Excel; para algo repetible, pandas o SQL.",
    }
    red = main.plan_b("comparativa", item)
    # Verifica que el caption menciona el nombre de una de las opciones
    assert "Excel" in red["caption"]
    assert "Python / pandas" in red["caption"]
    # Verifica que no hay representación dict en el caption
    assert "{'nombre'" not in red["caption"]


def test_construir_placas_tip_usa_dos_placas_de_contenido():
    """El tip tiene una sola idea con tres secciones: repartidas en dos placas,
    el carrusel pasa de tres slides a cuatro."""
    red = {"titulo_portada": "DETECTÁ\nDUPLICADOS", "ideas": [IDEA_TIP]}

    placas = main.construir_placas("tip", red)

    assert [p["plantilla"] for p in placas] == ["portada", "contenido", "contenido", "cierre"]
    assert [p["slide_index"] for p in placas] == [1, 2, 3, 4]
    assert {p["slide_total"] for p in placas} == {4}


def test_construir_placas_tip_reparte_las_secciones_en_orden():
    red = {"titulo_portada": "X", "ideas": [IDEA_TIP]}

    placas = main.construir_placas("tip", red)

    assert [s["label"] for s in placas[1]["secciones"]] == ["el problema", "el código"]
    assert [s["label"] for s in placas[2]["secciones"]] == ["por qué funciona"]
    # la sección de código viaja entera, con su snippet y su lenguaje
    assert placas[1]["secciones"][1] == {
        "label": "el código", "codigo": "SELECT 1;", "lenguaje": "sql"}


def test_construir_placas_continuacion_va_sin_titulo_ni_deck():
    """La segunda placa de una idea es continuación de la primera: repetir ahí
    el título gigante y el deck le roba el lugar al texto y se lee redundante.
    El kicker sí se repite: identifica la unidad de contenido, no la placa."""
    red = {"titulo_portada": "X", "ideas": [IDEA_TIP]}

    placas = main.construir_placas("tip", red)

    assert placas[1]["titulo"] == "DETECTÁ DUPLICADOS"
    assert placas[1]["deck"] == "Encontrá qué filas se repiten."
    assert placas[2]["titulo"] == ""
    assert placas[2]["deck"] == ""
    assert placas[2]["kicker"] == placas[1]["kicker"] == "tip 01"


def test_construir_placas_no_cambia_para_los_tipos_de_una_placa():
    """Regresión: comparativa y rol tienen un solo grupo, así que siguen
    emitiendo una placa por idea, con título y deck en todas."""
    red = {"titulo_portada": "X", "ideas": [IDEA, IDEA]}

    placas = main.construir_placas("comparativa", red)

    assert [p["plantilla"] for p in placas] == ["portada", "contenido", "contenido", "cierre"]
    assert all(p["titulo"] == "Excel" for p in placas[1:3])
    assert all(p["deck"] == "Limpiar filas" for p in placas[1:3])
    assert all(p["secciones"] == IDEA["secciones"] for p in placas[1:3])


def test_novedad_en_plan_b_se_reemplaza_por_un_evergreen(monkeypatch, tmp_path):
    """El plan B de novedad copia título y resumen del RSS tal cual, y los
    feeds son en inglés: es la única ruta capaz de publicar en un idioma que
    no es el de la marca (corrida 2026-08-11). Ante la duda va un evergreen,
    que siempre está escrito en español en los bancos."""
    cfg = get_config()
    cfg.dir_estado = tmp_path

    def gemini_siempre_falla(prompt, key):
        raise main.GeminiError("sin cuota")

    monkeypatch.setattr(main, "generar_json", gemini_siempre_falla)
    monkeypatch.setattr(main.time, "sleep", lambda _s: None)

    piezas = [{"tipo": "novedad", "item": {
        "id": "http://x/1", "fuente": "Power BI",
        "titulo": "Announcing new Copilot features",
        "resumen": "Today we are announcing a set of improvements.",
    }}]

    redacciones, novedad_descartada = main.redactar_lote(cfg, piezas, seed=202627)

    assert novedad_descartada is True
    assert piezas[0]["tipo"] in cfg.tipos_evergreen
    assert len(redacciones) == 1
    assert "Announcing new Copilot features" not in redacciones[0]["caption"]
    assert "Today we are announcing" not in redacciones[0]["caption"]
    assert "ANNOUNCING" not in redacciones[0]["titulo_portada"]
    assert "COPILOT" not in redacciones[0]["titulo_portada"]


def test_evergreen_en_plan_b_no_se_reemplaza(monkeypatch, tmp_path):
    """El plan B de los evergreen sale de los bancos, que están en español:
    ese camino no tiene nada de malo y se conserva tal cual."""
    cfg = get_config()
    cfg.dir_estado = tmp_path

    def gemini_siempre_falla(prompt, key):
        raise main.GeminiError("sin cuota")

    monkeypatch.setattr(main, "generar_json", gemini_siempre_falla)
    monkeypatch.setattr(main.time, "sleep", lambda _s: None)

    item = {"id": "t01", "titulo": "Rankear sin subconsultas", "lenguaje": "sql",
            "gancho": "Top N por grupo", "codigo": "SELECT 1;",
            "explicacion": "ROW_NUMBER numera dentro de cada grupo."}
    piezas = [{"tipo": "tip", "item": item}]

    redacciones, novedad_descartada = main.redactar_lote(cfg, piezas, seed=202627)

    assert novedad_descartada is False
    assert piezas[0]["tipo"] == "tip"
    assert redacciones[0]["plan_b"] is True
