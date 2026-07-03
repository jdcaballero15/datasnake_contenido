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
