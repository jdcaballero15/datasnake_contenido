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


def test_mix_is_one_novedad_two_evergreen():
    cfg = get_config()
    assert config.MIX_NOVEDAD == 1
    assert set(config.TIPOS_EVERGREEN) == {"comparativa", "rol", "tip"}
    assert cfg.mix["evergreen"] == 2


def test_hashtags_capped_at_five():
    assert len(config.HASHTAGS_DEFAULT) <= 5
