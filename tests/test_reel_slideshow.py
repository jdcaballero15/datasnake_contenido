import shutil

import pytest

from src.config import get_config
from src.video import reel_slideshow


def test_sin_placas_devuelve_none(tmp_path):
    cfg = get_config()
    assert reel_slideshow.generar_reel(tmp_path, cfg, seed=1) is None


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg no instalado")
def test_con_placas_arma_mp4(tmp_path):
    cfg = get_config()
    # dos placas mínimas (PNG 1x1) para el slideshow
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000d4944415478da6360000002000154a2b4bd0000000049454e44ae426082")
    (tmp_path / "01.png").write_bytes(png)
    (tmp_path / "02.png").write_bytes(png)
    salida = reel_slideshow.generar_reel(tmp_path, cfg, seed=1)
    assert salida is not None and salida.exists()
