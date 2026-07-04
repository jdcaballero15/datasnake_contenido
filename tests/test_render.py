from src.config import get_config
from src.render.renderer import Renderer

PLACAS = [
    {"plantilla": "portada", "tag": "Novedad", "titulo": "LO NUEVO\nDE POWER BI"},
    {"plantilla": "idea", "numero": 1, "titulo": "Copilot", "texto": "Genera DAX en lenguaje natural."},
    {"plantilla": "codigo", "lenguaje": "sql", "codigo": "SELECT 1;"},
    {"plantilla": "comparativa", "numero": 2, "titulo": "Excel vs Python", "texto": "Depende del volumen."},
    {"plantilla": "cierre"},
]


def test_render_cada_plantilla_produce_png(tmp_path):
    cfg = get_config()
    with Renderer(cfg) as r:
        for i, ctx in enumerate(PLACAS, start=1):
            destino = tmp_path / f"{i:02d}.png"
            r.render_placa(ctx, destino)
            assert destino.exists() and destino.stat().st_size > 1000


def test_codigo_snippet_is_html_escaped():
    r = Renderer(get_config())
    html = r.env.get_template("codigo.html").render(
        codigo="SELECT * FROM t WHERE a <> b & c;", lenguaje="sql",
        c={"fondo": "#111827", "texto": "#CBD5E1", "acento": "#2A7FA8",
           "borde": "#253347", "surface": "#1C2B3A", "texto_sec": "#7B91A8",
           "grad_a": "#7C5CBF", "grad_b": "#2EE6A6"},
        logo_uri="data:,", ig_handle="data.snake", eslogan="x")
    assert "&lt;&gt;" in html and "&amp;" in html
    assert "<> b & c" not in html  # raw special chars must not leak through


def _render_template(name, **extra):
    r = Renderer(get_config())
    ctx = {
        "tag": "Comparativa",
        "titulo": "EXCEL VS\nPYTHON",
        "numero": 1,
        "texto": "Rápido para algo puntual.",
        "lenguaje": "sql",
        "codigo": "SELECT 1;",
        "slide_index": 2,
        "slide_total": 4,
        "variant": "dark",
        "module_label": "qué resuelve",
        "c": {"fondo": "#111827", "texto": "#CBD5E1", "acento": "#2A7FA8",
              "borde": "#253347", "surface": "#1C2B3A", "texto_sec": "#7B91A8",
              "grad_a": "#7C5CBF", "grad_b": "#2EE6A6"},
        "logo_uri": "data:,",
        "ig_handle": "data.snake",
        "eslogan": "Herramientas, resultados y carrera en data",
    }
    ctx.update(extra)
    return r.env.get_template(f"{name}.html").render(**ctx)


def test_templates_include_carousel_shell_and_progress():
    html = _render_template("idea")
    assert 'class="plate variant-dark"' in html
    assert 'class="plate-header"' in html
    assert '02 / 04' in html
    assert 'class="progress-dot active"' in html
    assert "DESLIZA" in html
    assert "GUARDAR" in html


def test_content_templates_use_modules():
    html = _render_template("comparativa", variant="light", module_label="cuándo conviene")
    assert 'class="plate variant-light"' in html
    assert 'class="content-module"' in html
    assert "CUÁNDO CONVIENE" in html


def test_code_template_uses_terminal_block():
    html = _render_template("codigo", variant="code", codigo="SELECT * FROM t WHERE a <> b & c;")
    assert 'class="terminal-block"' in html
    assert 'class="terminal-code"' in html
    assert "&lt;&gt;" in html and "&amp;" in html
