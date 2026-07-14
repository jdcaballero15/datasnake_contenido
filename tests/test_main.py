from src import main
from src.config import get_config
from src.main import construir_placas


def test_plan_semana_sin_novedad_da_tres_evergreen(monkeypatch, tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    piezas = main.plan_semana(cfg, seed=202627, novedad=None)
    assert len(piezas) == 3
    assert all(p["tipo"] in cfg.tipos_evergreen for p in piezas)


def test_plan_semana_con_novedad(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    nov = {"id": "http://x/1", "titulo": "T", "resumen": "R", "link": "http://x/1", "fuente": "PBI"}
    piezas = main.plan_semana(cfg, seed=202627, novedad=nov)
    assert piezas[0]["tipo"] == "novedad"
    assert len(piezas) == 3  # 1 novedad + 2 evergreen


IDEA = {"titulo": "Excel", "deck": "Limpiar filas",
        "secciones": [{"label": "cuándo conviene", "texto": "Una sola vez."}]}


def test_construir_placas_usa_una_placa_contenido_por_idea():
    red = {"titulo_portada": "EXCEL VS\nPYTHON", "ideas": [IDEA, IDEA]}

    placas = main.construir_placas("comparativa", red)

    assert [p["plantilla"] for p in placas] == ["portada", "contenido", "contenido", "cierre"]
    assert [p["slide_index"] for p in placas] == [1, 2, 3, 4]
    assert {p["slide_total"] for p in placas} == {4}
    assert placas[0]["variant"] == "cover" and placas[-1]["variant"] == "close"


def test_construir_placas_pasa_secciones_y_kicker():
    red = {"titulo_portada": "X", "ideas": [IDEA]}

    placa = main.construir_placas("comparativa", red)[1]

    assert placa["kicker"] == "opción 01"
    assert placa["deck"] == "Limpiar filas"
    assert placa["secciones"] == IDEA["secciones"]


def test_tercera_idea_sale_en_placa_clara():
    red = {"titulo_portada": "X", "ideas": [IDEA, IDEA, IDEA, IDEA]}

    variants = [p["variant"] for p in main.construir_placas("rol", red)]

    assert variants == ["cover", "dark", "dark", "light", "dark", "close"]


def test_construir_placas_tip_mete_el_codigo_como_seccion():
    red = {"titulo_portada": "TOP N", "codigo": "SELECT 1;", "lenguaje": "sql",
           "ideas": [{"titulo": "Top N", "texto": "ROW_NUMBER con PARTITION BY."}]}

    placas = main.construir_placas("tip", red)

    assert [p["plantilla"] for p in placas] == ["portada", "contenido", "cierre"]
    labels = [s["label"] for s in placas[1]["secciones"]]
    assert "el código" in labels


def test_plan_b_tip_arma_ideas_densas():
    item = {"titulo": "Top N en SQL", "gancho": "Top N por grupo.", "codigo": "SELECT 1;",
            "lenguaje": "sql", "explicacion": "ROW_NUMBER numera por grupo."}

    red = main.plan_b("tip", item)

    assert red["plan_b"] is True
    assert [s["label"] for s in red["ideas"][0]["secciones"]] == [
        "el problema", "el código", "por qué funciona"]


def test_armar_caption_agrega_ctas_y_hashtags():
    cap = main.armar_caption("cuerpo", ["data", "sql"])
    assert "cuerpo" in cap and "#data" in cap
    from src import config
    assert config.CTA_GUARDAR in cap


def test_armar_caption_capa_hashtags_en_5():
    cap = main.armar_caption("cuerpo", ["a", "b", "c", "d", "e", "f", "g"])
    assert cap.count("#") == 5


def test_plan_semana_usa_seeds_deterministas(monkeypatch, tmp_path):
    from src.fuentes import bancos
    cfg = get_config()
    cfg.dir_estado = tmp_path
    seeds = []
    real = bancos.seleccionar

    def spy(c, banco, cantidad, seed):
        seeds.append(seed)
        return real(c, banco, cantidad, seed)

    monkeypatch.setattr(main, "seleccionar", spy)
    main.plan_semana(cfg, seed=202627, novedad=None)  # no novedad → 3 evergreen slots
    assert seeds == [202628, 202629, 202630]  # seed+1, +2, +3 — deterministic, not hash-based


def test_construir_placas_adds_carousel_metadata_to_every_plate():
    red = {
        "titulo_portada": "EXCEL VS\nPYTHON",
        "ideas": [
            {"titulo": "Excel", "texto": "Rápido para algo puntual."},
            {"titulo": "Python", "texto": "Reproducible para procesos repetidos."},
        ],
    }
    placas = construir_placas("comparativa", red)

    assert [p["slide_index"] for p in placas] == [1, 2, 3, 4]
    assert {p["slide_total"] for p in placas} == {4}
    assert placas[0]["variant"] == "cover"
    assert placas[-1]["variant"] == "close"


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
