"""Arma una página web estática (un solo index.html autocontenido) con los
carruseles del lote, para bajarlos y copiar el caption desde el celu.

Autocontenida: imágenes embebidas como data URIs, CSS y JS inline. No hostea
archivos aparte. La publica el workflow en GitHub Pages (ver contenido.yml).
"""

import base64
import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.config import (COLOR_ACENTO, COLOR_BORDE, COLOR_FONDO, COLOR_SURFACE,
                        COLOR_TEXTO, COLOR_TEXTO_SEC, GRAD_A, GRAD_B, RAIZ)

log = logging.getLogger("sosiego.web")

DIR_PLANTILLAS = RAIZ / "plantillas"


def _data_uri(ruta: Path) -> str:
    b64 = base64.b64encode(ruta.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _leer_piezas(lote_dir: Path) -> list[dict]:
    piezas = []
    for carpeta in sorted(p for p in lote_dir.iterdir() if p.is_dir()):
        meta = {}
        meta_json = carpeta / "meta.json"
        if meta_json.exists():
            meta = json.loads(meta_json.read_text(encoding="utf-8"))
        cap = carpeta / "caption.txt"
        caption = cap.read_text(encoding="utf-8") if cap.exists() else ""
        imagenes = [_data_uri(png) for png in sorted(carpeta.glob("*.png"))]
        piezas.append({
            "tipo": meta.get("tipo") or carpeta.name.split("-", 1)[-1],
            "titulo": meta.get("titulo", ""),
            "caption": caption,
            "imagenes": imagenes,
        })
    return piezas


def _fecha_legible(nombre_lote: str) -> str:
    iso = nombre_lote.replace("lote-", "")
    try:
        y, m, d = iso.split("-")
        return f"{d}/{m}/{y}"
    except ValueError:
        return iso


def _lotes_recientes(dir_salida: Path, n: int = 7) -> list[Path]:
    lotes = sorted((p for p in dir_salida.glob("lote-*") if p.is_dir()),
                   key=lambda p: p.name, reverse=True)
    return lotes[:n]


def generar_pagina(dir_salida: Path, destino_dir: Path, n_dias: int = 7) -> Path:
    """Escribe destino_dir/index.html con los últimos n_dias lotes y devuelve su ruta."""
    destino_dir.mkdir(parents=True, exist_ok=True)
    dias = []
    for lote in _lotes_recientes(dir_salida, n_dias):
        piezas = _leer_piezas(lote)
        if piezas:
            dias.append({"fecha": _fecha_legible(lote.name), "piezas": piezas})
    env = Environment(loader=FileSystemLoader(DIR_PLANTILLAS), autoescape=True)
    html = env.get_template("pagina.html").render(
        dias=dias,
        c={"fondo": COLOR_FONDO, "texto": COLOR_TEXTO, "acento": COLOR_ACENTO,
           "surface": COLOR_SURFACE, "borde": COLOR_BORDE, "texto_sec": COLOR_TEXTO_SEC,
           "grad_a": GRAD_A, "grad_b": GRAD_B},
    )
    destino = destino_dir / "index.html"
    destino.write_text(html, encoding="utf-8")
    log.info("Página generada: %s (%d días)", destino, len(dias))
    return destino


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    salida = RAIZ / "salida"
    generar_pagina(salida, salida / "web")


if __name__ == "__main__":
    main()
