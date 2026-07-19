from src import config
from src.config import get_config


def test_palette_is_data_snake_dark():
    assert config.COLOR_FONDO == "#111827"
    assert config.COLOR_TEXTO == "#CBD5E1"
    assert config.COLOR_ACENTO == "#2A7FA8"
    assert config.COLOR_BORDE == "#253347"


def test_brand_strings():
    assert config.ESLOGAN == "Herramientas, resultados y carrera en data"
    assert get_config().ig_handle == "data.snake"


def test_piezas_por_dia_default_uno():
    cfg = get_config()
    assert config.PIEZAS_POR_DIA == 1
    assert cfg.piezas_por_dia == 1
    assert set(config.TIPOS_EVERGREEN) == {"comparativa", "rol", "tip"}


def test_hashtags_capped_at_five():
    assert len(config.HASHTAGS_DEFAULT) <= 5
