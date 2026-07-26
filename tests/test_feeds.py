from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import feedparser

from src.config import get_config
from src.fuentes import feeds

FIXTURE = Path(__file__).parent / "fixtures" / "feed_ejemplo.xml"


def _parse_fixture_reciente(_url):
    reciente = format_datetime(datetime.now(timezone.utc))
    xml = FIXTURE.read_text(encoding="utf-8").replace("__RECIENTE__", reciente)
    return feedparser.parse(xml)


def test_elige_la_entrada_fresca_no_la_vieja(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.dir_datos = tmp_path
    (tmp_path / "feeds.json").write_text('[{"nombre":"PBI","url":"x"}]', encoding="utf-8")
    nov = feeds.elegir_novedad(cfg, parse=_parse_fixture_reciente)
    assert nov is not None
    assert nov["titulo"] == "Nueva función de copilot en Power BI"
    assert nov["fuente"] == "PBI"


def test_no_repite_novedad_ya_vista(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.dir_datos = tmp_path
    (tmp_path / "feeds.json").write_text('[{"nombre":"PBI","url":"x"}]', encoding="utf-8")
    feeds.registrar_vista(cfg, "https://example.com/nuevo-copilot")
    nov = feeds.elegir_novedad(cfg, parse=_parse_fixture_reciente)
    assert nov is None  # la fresca ya fue vista, la otra está fuera de la ventana


def test_sin_feeds_devuelve_none(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.dir_datos = tmp_path
    (tmp_path / "feeds.json").write_text("[]", encoding="utf-8")
    assert feeds.elegir_novedad(cfg, parse=_parse_fixture_reciente) is None


def test_es_muy_tecnica_detecta_terminos_vetados():
    tecnica = {"titulo": "Governance de Redshift cross-account", "resumen": "con SageMaker"}
    amigable = {"titulo": "Nueva función de copilot", "resumen": "medidas en lenguaje natural"}
    assert feeds.es_muy_tecnica(tecnica) is True
    assert feeds.es_muy_tecnica(amigable) is False


def test_es_muy_tecnica_ignora_acentos_y_mayusculas():
    # "clúster" con tilde y en mayúsculas igual pega con el vetado "cluster".
    assert feeds.es_muy_tecnica({"titulo": "Escalá tu CLÚSTER", "resumen": ""}) is True


def _parse_dos_frescas(_url):
    reciente = format_datetime(datetime.now(timezone.utc))
    algo_antes = format_datetime(datetime.now(timezone.utc))
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Feed</title>
  <item>
    <title>Migración a Redshift con Kubernetes</title>
    <link>https://example.com/tecnica</link><guid>https://example.com/tecnica</guid>
    <description>Infra enterprise.</description><pubDate>{reciente}</pubDate>
  </item>
  <item>
    <title>Tres funciones nuevas de Power BI</title>
    <link>https://example.com/amigable</link><guid>https://example.com/amigable</guid>
    <description>Para armar reportes más rápido.</description><pubDate>{algo_antes}</pubDate>
  </item>
</channel></rss>"""
    return feedparser.parse(xml)


def test_saltea_la_novedad_muy_tecnica_y_elige_la_amigable(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.dir_datos = tmp_path
    (tmp_path / "feeds.json").write_text('[{"nombre":"PBI","url":"x"}]', encoding="utf-8")
    nov = feeds.elegir_novedad(cfg, parse=_parse_dos_frescas)
    assert nov is not None
    assert nov["titulo"] == "Tres funciones nuevas de Power BI"


def test_si_todas_las_frescas_son_tecnicas_devuelve_none(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.dir_datos = tmp_path
    (tmp_path / "feeds.json").write_text('[{"nombre":"PBI","url":"x"}]', encoding="utf-8")

    def _solo_tecnicas(_url):
        reciente = format_datetime(datetime.now(timezone.utc))
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Feed</title>
  <item><title>Airflow y Kafka en producción</title>
    <link>https://example.com/t1</link><guid>https://example.com/t1</guid>
    <description>data lake</description><pubDate>{reciente}</pubDate></item>
</channel></rss>"""
        return feedparser.parse(xml)

    assert feeds.elegir_novedad(cfg, parse=_solo_tecnicas) is None
