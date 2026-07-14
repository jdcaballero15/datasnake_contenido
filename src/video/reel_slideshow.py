"""Reel opcional: las placas del carrusel como slideshow 9:16 con música.

Apagado por defecto (cfg.reel_activado): la cuenta publica solo carruseles.

Enfoque liviano (estilo Efecto Gambeta): NO anima; encadena los PNG con
ffmpeg. Si falta ffmpeg o no hay placas, devuelve None y la pieza sale sin
reel (nunca voltea la corrida). Render atómico: escribe a reel.tmp.mp4 y
renombra solo si ffmpeg terminó bien.
"""

import logging
import shutil
import subprocess
from pathlib import Path

from src.audio.musica import elegir
from src.config import Config, DIR_MUSICA

log = logging.getLogger("datasnake.reel")


def generar_reel(carpeta: Path, cfg: Config, seed: int) -> Path | None:
    if not cfg.reel_activado:
        return None
    if shutil.which("ffmpeg") is None:
        log.warning("ffmpeg no disponible: la pieza sale sin reel")
        return None
    placas = sorted(carpeta.glob("[0-9][0-9].png"))
    if not placas:
        return None

    tmp = carpeta / "reel.tmp.mp4"
    destino = carpeta / "reel.mp4"
    seg = cfg.segundos_por_slide
    vf = ("scale=1080:1350:force_original_aspect_ratio=decrease,"
          "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x111827,format=yuv420p")
    cmd = ["ffmpeg", "-y", "-framerate", f"1/{seg}",
           "-pattern_type", "glob", "-i", str(carpeta / "[0-9][0-9].png")]

    pista = elegir(seed, DIR_MUSICA)
    if pista:
        cmd += ["-i", str(pista), "-c:a", "aac", "-shortest"]
    cmd += ["-vf", vf, "-r", "30", "-c:v", "libx264", "-movflags", "+faststart", str(tmp)]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except (subprocess.CalledProcessError, OSError) as e:
        log.error("ffmpeg falló: %s", e)
        tmp.unlink(missing_ok=True)
        return None
    tmp.rename(destino)
    return destino
