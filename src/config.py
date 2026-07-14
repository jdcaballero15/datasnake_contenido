"""Configuración de Data Snake. TODO lo ajustable vive acá."""

import os
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_MUSICA = RAIZ / "musica"

# Paleta de marca (dark). Base azul-forward; gradiente violeta→verde para acentos.
COLOR_FONDO = "#111827"        # Midnight
COLOR_TEXTO = "#CBD5E1"        # Cloud
COLOR_ACENTO = "#2A7FA8"       # Ocean Blue
COLOR_BORDE = "#253347"        # Border
COLOR_SURFACE = "#1C2B3A"      # Deep Slate (cards)
COLOR_TEXTO_SEC = "#7B91A8"    # Mist
GRAD_A = "#7C5CBF"             # Slate Violet
GRAD_B = "#2EE6A6"             # verde del logo
COLOR_HUESO = "#EEE9E1"        # fondo de la placa clara

# Mix semanal: 1 novedad (RSS) + 2 evergreen rotando entre estos tipos.
MIX_NOVEDAD = 1
TIPOS_EVERGREEN = ["comparativa", "rol", "tip"]

# Ventana de frescura de las novedades (la corrida es semanal).
FRESCURA_DIAS = 14

ESLOGAN = "Herramientas, resultados y carrera en data"

# Doble CTA fija del caption (señales del algoritmo: compartir + guardar), tono tech.
CTA_COMPARTIR = "📩 Mandáselo a alguien que esté metido en data."
CTA_GUARDAR = "🔖 Guardalo para tu próximo proyecto."

HASHTAGS_DEFAULT = ["data", "analytics", "powerbi", "sql", "python"]

# Reels de slideshow: apagados. La cuenta publica solo carruseles; el código
# queda para cuando haga falta. Poner True acá (y ffmpeg en el workflow) lo revive.
REEL_ACTIVADO = False
SEGUNDOS_POR_SLIDE = 3


@dataclass
class Config:
    gemini_api_key: str = ""
    dir_datos: Path = RAIZ / "datos"
    dir_estado: Path = RAIZ / "estado"
    dir_salida: Path = RAIZ / "salida"
    dir_plantillas: Path = RAIZ / "plantillas"
    ruta_logo: Path = RAIZ / "marca" / "logos" / "logo.png"
    ig_handle: str = "data.snake"
    mix: dict = field(default_factory=lambda: {"novedad": MIX_NOVEDAD, "evergreen": 2})
    tipos_evergreen: list = field(default_factory=lambda: list(TIPOS_EVERGREEN))
    reel_activado: bool = REEL_ACTIVADO
    segundos_por_slide: int = SEGUNDOS_POR_SLIDE
    pausa_entre_llamadas: float = 7.0  # anti rate-limit del free tier de Gemini


def get_config() -> Config:
    return Config(gemini_api_key=os.environ.get("GEMINI_API_KEY", ""))
