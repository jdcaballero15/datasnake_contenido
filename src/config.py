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

PORTADA_VARIANTES = ("green", "violet", "blue", "coral")
COLORES_PORTADA = {
    "green": {"fondo": "#2EE6A6", "texto": "#0B1F1A"},
    "violet": {"fondo": "#A78BFA", "texto": "#17122C"},
    "blue": {"fondo": "#60A5FA", "texto": "#0B1B35"},
    "coral": {"fondo": "#FB7185", "texto": "#311018"},
}

# Carruseles por corrida (diaria). El "dial" para escalar volumen: subilo para generar
# más por día. OJO: muy arriba, los 45 evergreen se repiten rápido y las novedades RSS
# no dan abasto — habría que sumar feeds/bancos.
PIEZAS_POR_DIA = 1
# Tipos evergreen que rotan cuando no hay (o sobran) novedades.
TIPOS_EVERGREEN = ["comparativa", "rol", "tip"]

# Ventana de frescura de las novedades (la corrida es semanal).
FRESCURA_DIAS = 14

# Filtro de novedades: si el título o el resumen de una novedad RSS pega con
# alguno de estos términos, se descarta por "demasiado técnica/enterprise" y la
# corrida cae a un evergreen amigable. El público es curioso→junior, no infra
# senior. Match por substring, sin distinguir mayúsculas ni acentos. Editá la
# lista a gusto: agregá lo que veas colarse, sacá lo que filtre de más.
TEMAS_VETADOS = [
    "redshift", "cross-account", "cross account", "sagemaker", "iam", "vpc",
    "kubernetes", "k8s", "terraform", "cluster", "clúster", "airflow",
    "kafka", "spark", "hadoop", "emr", "glue", "athena", "lambda", "s3 bucket",
    "data lake", "lakehouse", "warehouse migration", "cdc", "orchestration",
    "pipeline de datos", "ci/cd", "devops", "governance", "gobierno de datos",
]

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
    piezas_por_dia: int = PIEZAS_POR_DIA
    tipos_evergreen: list = field(default_factory=lambda: list(TIPOS_EVERGREEN))
    reel_activado: bool = REEL_ACTIVADO
    segundos_por_slide: int = SEGUNDOS_POR_SLIDE
    pausa_entre_llamadas: float = 7.0  # anti rate-limit del free tier de Gemini


def get_config() -> Config:
    return Config(gemini_api_key=os.environ.get("GEMINI_API_KEY", ""))
