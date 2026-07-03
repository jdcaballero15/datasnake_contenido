# src/audio/musica.py
"""Selección del track de música de fondo del reel. Los .mp3 viven en musica/
(CC0). La elección es determinística por seed para que la misma pieza dé el
mismo track al reintentar. El recorte y los fades los hace ffmpeg en reel.py."""

from pathlib import Path


def tracks(dir_musica: Path) -> list[Path]:
    """.mp3 de la carpeta, en orden alfabético (estable)."""
    if not Path(dir_musica).is_dir():
        return []
    return sorted(Path(dir_musica).glob("*.mp3"))


def elegir(seed: int, dir_musica: Path) -> Path | None:
    """Un track según el seed (seed % cantidad). None si no hay tracks."""
    ts = tracks(dir_musica)
    if not ts:
        return None
    return ts[seed % len(ts)]
