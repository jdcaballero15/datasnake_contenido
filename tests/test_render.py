import re

from src.config import get_config
from src.render.renderer import Renderer

C = {"fondo": "#111827", "texto": "#CBD5E1", "acento": "#2A7FA8", "borde": "#253347",
     "surface": "#1C2B3A", "texto_sec": "#7B91A8", "grad_a": "#7C5CBF",
     "grad_b": "#2EE6A6", "hueso": "#EEE9E1"}

SECCIONES = [
    {"label": "el problema", "texto": "Top N por grupo sin subconsultas."},
    {"label": "el código", "codigo": "SELECT * FROM t WHERE a <> b & c;", "lenguaje": "sql"},
    {"label": "por qué funciona", "texto": "ROW_NUMBER numera dentro de cada grupo."},
]

PLACAS = [
    {"plantilla": "portada", "tag": "Tip", "titulo": "TOP N\nEN SQL",
     "subtitulo": "Herramientas, resultados y carrera en data", "variant": "cover"},
    {"plantilla": "contenido", "kicker": "tip 01", "titulo": "TOP N EN SQL",
     "deck": "Sin subconsultas.", "secciones": SECCIONES, "variant": "dark"},
    {"plantilla": "contenido", "kicker": "opción 03", "titulo": "PANDAS",
     "deck": "Limpiar 10.000 filas.", "secciones": SECCIONES[:1], "variant": "light"},
    {"plantilla": "cierre", "variant": "close"},
]


def test_render_cada_plantilla_produce_png(tmp_path):
    cfg = get_config()
    with Renderer(cfg) as r:
        for i, ctx in enumerate(PLACAS, start=1):
            destino = tmp_path / f"{i:02d}.png"
            r.render_placa(ctx, destino)
            assert destino.exists() and destino.stat().st_size > 1000


def _render(name, **extra):
    ctx = {"kicker": "tip 01", "titulo": "TOP N EN SQL", "deck": "Sin subconsultas.",
           "secciones": SECCIONES, "tag": "Tip", "subtitulo": "Eslogan",
           "slide_index": 2, "slide_total": 4, "variant": "dark", "c": C,
           "logo_uri": "data:,", "ig_handle": "data.snake",
           "eslogan": "Herramientas, resultados y carrera en data"}
    ctx.update(extra)
    return Renderer(get_config()).env.get_template(f"{name}.html").render(**ctx)


def test_contenido_tiene_shell_de_carrusel():
    html = _render("contenido")
    assert 'class="plate variant-dark"' in html
    assert 'class="plate-header"' in html
    assert "02 / 04" in html
    assert 'class="progress-dot active"' in html
    assert "DESLIZA" in html and "GUARDAR" in html


def test_contenido_pinta_todas_las_secciones_con_su_label():
    html = _render("contenido")
    assert "EL PROBLEMA" in html
    assert "EL CÓDIGO" in html
    assert "POR QUÉ FUNCIONA" in html
    assert html.count('class="section-label"') == 3


def test_contenido_escapa_el_codigo():
    html = _render("contenido")
    assert "code-text" in html
    assert "&lt;&gt;" in html and "&amp;" in html
    assert "<> b & c" not in html  # los caracteres crudos no pueden filtrarse


def _clase_de_codigo(codigo):
    """Escalón de tamaño que la plantilla le puso al <pre> del snippet.

    Mira solo el atributo del <pre>: los nombres de clase también aparecen en el
    CSS, así que buscarlos en todo el HTML daría siempre positivo."""
    seccion = {"label": "el código", "codigo": codigo, "lenguaje": "sql"}
    html = _render("contenido", secciones=[seccion])
    clases = re.search(r'<pre class="([^"]*)"', html).group(1)
    return [c for c in ("code-md", "code-sm", "code-xs") if c in clases.split()]


def test_el_cuerpo_del_codigo_baja_segun_la_linea_mas_larga():
    # el snippet corto se muestra en el cuerpo grande (sin clase de escalón)
    assert _clase_de_codigo("SELECT 1;") == []
    # a partir de ~48 caracteres el cuerpo baja, escalón por escalón, para que la
    # línea entre sin partirse al medio
    assert _clase_de_codigo("x" * 55) == ["code-md"]
    assert _clase_de_codigo("x" * 65) == ["code-sm"]
    assert _clase_de_codigo("x" * 90) == ["code-xs"]


def test_el_escalon_lo_decide_la_linea_mas_larga_no_el_total():
    corto_pero_largo_total = "\n".join(["SELECT 1;"] * 10)
    assert _clase_de_codigo(corto_pero_largo_total) == []


def test_variante_clara_existe():
    html = _render("contenido", variant="light")
    assert 'class="plate variant-light"' in html


def test_portada_usa_variante_cover():
    html = _render("portada", variant="cover")
    assert 'class="plate variant-cover"' in html
    assert "TOP N" in html
