from src import main
from src.config import get_config


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


def test_construir_placas_tip_incluye_codigo():
    red = {"titulo_portada": "X", "ideas": [{"titulo": "a", "texto": "b"}],
           "codigo": "SELECT 1;", "lenguaje": "sql"}
    placas = main.construir_placas("tip", red)
    plantillas = [p["plantilla"] for p in placas]
    assert "codigo" in plantillas
    assert plantillas[0] == "portada" and plantillas[-1] == "cierre"


def test_armar_caption_agrega_ctas_y_hashtags():
    cap = main.armar_caption("cuerpo", ["data", "sql"])
    assert "cuerpo" in cap and "#data" in cap
    from src import config
    assert config.CTA_GUARDAR in cap
