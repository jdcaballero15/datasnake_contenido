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


def generar_pagina(lote_dir: Path, destino_dir: Path) -> Path:
    """Escribe destino_dir/index.html con el lote y devuelve su ruta."""
    destino_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(DIR_PLANTILLAS), autoescape=True)
    fecha = lote_dir.name.replace("semana-", "")
    html = env.get_template("pagina.html").render(
        piezas=_leer_piezas(lote_dir),
        fecha=fecha,
        c={"fondo": COLOR_FONDO, "texto": COLOR_TEXTO, "acento": COLOR_ACENTO,
           "surface": COLOR_SURFACE, "borde": COLOR_BORDE, "texto_sec": COLOR_TEXTO_SEC,
           "grad_a": GRAD_A, "grad_b": GRAD_B},
    )
    destino = destino_dir / "index.html"
    destino.write_text(html, encoding="utf-8")
    log.info("Página generada: %s (%d piezas)", destino, len(_leer_piezas(lote_dir)))
    return destino


def _lote_mas_reciente(dir_salida: Path) -> Path | None:
    lotes = sorted(p for p in dir_salida.glob("semana-*") if p.is_dir())
    return lotes[-1] if lotes else None


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    salida = RAIZ / "salida"
    lote = _lote_mas_reciente(salida)
    if lote is None:
        log.warning("No hay lote en %s: no se genera página", salida)
        return
    generar_pagina(lote, salida / "web")


if __name__ == "__main__":
    main()
