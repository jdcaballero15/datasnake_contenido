"""Render de plantillas HTML a PNG 1080×1350 con Playwright (adaptado de EG).

Requiere `playwright install chromium` (lo hace el workflow de Actions; local
está en el README). Un solo navegador por lote: usar Renderer como context
manager para no pagar el arranque de Chromium por placa.
"""

import base64
import logging
import mimetypes
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from src.config import (COLOR_ACENTO, COLOR_BORDE, COLOR_FONDO, COLOR_HUESO,
                        COLOR_SURFACE, COLOR_TEXTO, COLOR_TEXTO_SEC, ESLOGAN,
                        GRAD_A, GRAD_B, Config)

log = logging.getLogger("sosiego.render")

ANCHO, ALTO = 1080, 1350


def _como_data_uri(ruta: Path) -> str:
    """Imagen como data URI: Chromium no carga file:// desde set_content,
    así que el logo va incrustado en el HTML."""
    mime = mimetypes.guess_type(str(ruta))[0] or "image/png"
    b64 = base64.b64encode(ruta.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


class Renderer:
    """Renderiza placas reutilizando un único Chromium. Uso:

    with Renderer(cfg) as r:
        r.render_placa({"plantilla": "portada", ...}, destino)
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.env = Environment(loader=FileSystemLoader(cfg.dir_plantillas), autoescape=True)
        self._pw = None
        self._browser = None
        self._page = None

    def __enter__(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch()
        self._page = self._browser.new_page(viewport={"width": ANCHO, "height": ALTO})
        return self

    @property
    def browser(self):
        """El Chromium en curso, para que otros (el reel) reusen la instancia
        en vez de abrir un segundo Playwright (que rompe la sync API anidada)."""
        return self._browser

    def __exit__(self, *exc):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def render_placa(self, contexto: dict, destino: Path) -> Path:
        """contexto["plantilla"]: portada | idea | codigo | comparativa | cierre."""
        contexto = dict(contexto)
        contexto.setdefault("slide_index", 1)
        contexto.setdefault("slide_total", 1)
        contexto.setdefault("variant", "dark")
        contexto.setdefault("logo_uri", _como_data_uri(self.cfg.ruta_logo))
        contexto.setdefault("ig_handle", self.cfg.ig_handle)
        contexto.setdefault("eslogan", ESLOGAN)
        contexto.setdefault("c", {
            "fondo": COLOR_FONDO, "texto": COLOR_TEXTO, "acento": COLOR_ACENTO,
            "borde": COLOR_BORDE, "surface": COLOR_SURFACE, "texto_sec": COLOR_TEXTO_SEC,
            "grad_a": GRAD_A, "grad_b": GRAD_B, "hueso": COLOR_HUESO,
        })

        html = self.env.get_template(f"{contexto['plantilla']}.html").render(**contexto)
        self._page.set_content(html, wait_until="networkidle")
        # margen extra para que terminen de pintar las webfonts
        self._page.wait_for_timeout(250)
        destino.parent.mkdir(parents=True, exist_ok=True)
        self._page.screenshot(path=str(destino))
        log.info("Render %s → %s", contexto["plantilla"], destino.name)
        return destino
