import shutil

import pytest

from src.config import get_config
from src.video import reel_slideshow


# dos placas mínimas (PNG 1x1) para el slideshow
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d4944415478da6360000002000154a2b4bd0000000049454e44ae426082")


def _con_placas(carpeta):
    (carpeta / "01.png").write_bytes(PNG)
    (carpeta / "02.png").write_bytes(PNG)
    return carpeta


def test_sin_placas_devuelve_none(tmp_path):
    cfg = get_config()
    cfg.reel_activado = True
    assert reel_slideshow.generar_reel(tmp_path, cfg, seed=1) is None


def test_apagado_no_arma_reel(tmp_path):
    cfg = get_config()
    assert cfg.reel_activado is False, "el default de la marca es sin reel"
    assert reel_slideshow.generar_reel(_con_placas(tmp_path), cfg, seed=1) is None
    assert not (tmp_path / "reel.mp4").exists()


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg no instalado")
def test_con_placas_arma_mp4(tmp_path):
    cfg = get_config()
    cfg.reel_activado = True
    salida = reel_slideshow.generar_reel(_con_placas(tmp_path), cfg, seed=1)
    assert salida is not None and salida.exists()
