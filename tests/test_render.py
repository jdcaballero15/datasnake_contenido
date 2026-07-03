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
